import os
import numpy as np
import pandas as pd
import tensorflow as tf
keras = tf.keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# File Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "processed_features.csv")
TFLITE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.tflite")
HEADER_OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "firmware", "include","ml" ,"model_data.h"
)


def load_healthy_data():
    """Loads preprocessed features and filters strictly healthy samples for Autoencoder training."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Could not find {DATA_PATH}. Run prepare_data.py first!")

    df = pd.read_csv(DATA_PATH)
    
    # Scale all features (Mean=0, Std=1)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[["rms", "peak_to_peak", "kurtosis"]].values)
    
    # Train Autoencoder ONLY on healthy operational baseline (label == 0)
    X_healthy = X_scaled[df["label"].values == 0]
    X_anomalous = X_scaled[df["label"].values == 1]

    X_train, X_test = train_test_split(X_healthy, test_size=0.2, random_state=42)

    return X_train, X_test, X_anomalous, scaler.mean_, scaler.scale_


def build_autoencoder():
    """Creates a ultra-lightweight Autoencoder bottleneck model (Input 3 -> 8 -> 2 -> 8 -> Output 3)."""
    model = keras.Sequential([
        # Encoder
        keras.layers.Input(shape=(3,)),
        keras.layers.Dense(8, activation="relu"),
        keras.layers.Dense(2, activation="relu"),  # Latent bottleneck space
        
        # Decoder
        keras.layers.Dense(8, activation="relu"),
        keras.layers.Dense(3, activation="linear")  # Reconstruct 3 original features
    ])

    model.compile(optimizer="adam", loss="mse")
    return model


def convert_to_int8_tflite(model, X_train):
    """Quantizes the Autoencoder model into fully-quantized INT8 TFLite format."""

    def representative_dataset():
        for i in range(min(100, len(X_train))):
            yield [X_train[i : i + 1].astype(np.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset

    # Enforce strict INT8 execution for microcontroller deployment
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()

    with open(TFLITE_MODEL_PATH, "wb") as f:
        f.write(tflite_model)

    print(f"✅ INT8 Quantized Autoencoder TFLite model saved: {TFLITE_MODEL_PATH}")
    return tflite_model
def calculate_int8_thresholds(tflite_model, X_calibration):
    """Calculate healthy reconstruction-error thresholds using INT8 TFLite inference."""
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()

    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]

    input_scale, input_zero_point = input_detail["quantization"]
    output_scale, output_zero_point = output_detail["quantization"]

    if input_scale <= 0 or output_scale <= 0:
        raise ValueError("TFLite input/output quantization scales must be positive.")

    errors = []
    for sample in X_calibration:
        sample = sample.reshape(1, -1).astype(np.float32)

        quantized_input = np.rint(sample / input_scale + input_zero_point)
        quantized_input = np.clip(
            quantized_input,
            np.iinfo(input_detail["dtype"]).min,
            np.iinfo(input_detail["dtype"]).max,
        ).astype(input_detail["dtype"])

        interpreter.set_tensor(input_detail["index"], quantized_input)
        interpreter.invoke()

        quantized_output = interpreter.get_tensor(output_detail["index"])
        reconstruction = (
            quantized_output.astype(np.float32) - output_zero_point
        ) * output_scale

        errors.append(float(np.mean(np.square(sample - reconstruction))))

    mse_95 = float(np.percentile(errors, 95))
    mse_99_5 = float(np.percentile(errors, 99.5))
    return mse_95, mse_99_5


def export_c_header(tflite_model, mse_95, mse_99_5, feature_mean, feature_scale):
    """Converts the TFLite model and thresholds into a static C++ header."""
    hex_array = ", ".join([f"0x{b:02x}" for b in tflite_model])
    array_len = len(tflite_model)
    mean_array = ", ".join(f"{float(value):.9g}f" for value in feature_mean)
    scale_array = ", ".join(f"{float(value):.9g}f" for value in feature_scale)

    os.makedirs(os.path.dirname(HEADER_OUTPUT_PATH), exist_ok=True)

    header_content = f"""#pragma once
// Auto-generated INT8 Quantized Autoencoder Array
// Total Size: {array_len} bytes

#include <cstddef>

#define THRESHOLD_WARN {mse_95:.9g}f
#define THRESHOLD_CRIT {mse_99_5:.9g}f

inline constexpr float kFeatureMean[3] = {{{mean_array}}};
inline constexpr float kFeatureScale[3] = {{{scale_array}}};

alignas(16) const unsigned char g_model[] = {{
    {hex_array}
}};

const size_t g_model_len = {array_len};
"""

    with open(HEADER_OUTPUT_PATH, "w") as f:
        f.write(header_content)

    print(f"C++ model and threshold header generated: {HEADER_OUTPUT_PATH}")
    print(f"Thresholds: warn={mse_95:.9g}, critical={mse_99_5:.9g}")
    print(f"Final binary footprint: {array_len} bytes")


def main():
    print("Loading healthy training baseline...")
    X_train, X_test, X_anomalous, feature_mean, feature_scale = load_healthy_data()

    print("Building and training Autoencoder...")
    autoencoder = build_autoencoder()
    autoencoder.fit(
        X_train,
        X_train,  # Targets are identical to input for autoencoding
        epochs=20,
        batch_size=32,
        validation_data=(X_test, X_test),
        verbose=1
    )

    # Calculate baseline reconstruction error threshold
    reconstructions = autoencoder.predict(X_test, verbose=0)
    healthy_mse = np.mean(np.square(X_test - reconstructions), axis=1)
    mse_95 = np.percentile(healthy_mse, 95)
    mse_99_5 = np.percentile(healthy_mse, 99.5)
    print("\nQuantizing Autoencoder to INT8...")
    tflite_model = convert_to_int8_tflite(autoencoder, X_train)

    mse_95, mse_99_5 = calculate_int8_thresholds(tflite_model, X_test)

    print("\nExporting model and thresholds to static C++ header...")
    export_c_header(
        tflite_model,
        mse_95,
        mse_99_5,
        feature_mean,
        feature_scale,
    )
def cross_validate_cmapss(df, feature_cols, target_col='RUL', n_splits=5):
    """
    Performs Group K-Fold Cross Validation keeping unit_numbers intact within folds.
    """
    groups = df['unit_number'].values
    X = df[feature_cols].values
    y = df[target_col].values

    gkf = GroupKFold(n_splits=n_splits)
    fold_scores = []

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # Build model
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu', input_shape=(X_train.shape[1],)),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # Train
        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=15,
            batch_size=64,
            verbose=0
        )

        # Evaluate
        val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
        fold_scores.append(val_mae)
        print(f"Fold {fold + 1} - Validation MAE: {val_mae:.4f}")

    print(f"\nMean CV MAE: {np.mean(fold_scores):.4f} +/- {np.std(fold_scores):.4f}")
    return fold_scores


if __name__ == "__main__":
    main()