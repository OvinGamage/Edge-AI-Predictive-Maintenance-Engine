import os
import numpy as np
import pandas as pd
import tensorflow as tf
keras = tf.keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

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
    """Split by engine before fitting the scaler to avoid adjacent-window leakage."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Could not find {DATA_PATH}. Run prepare_data.py first!")

    df = pd.read_csv(DATA_PATH)

    units = df["unit_number"].drop_duplicates().to_numpy()
    if len(units) < 5:
        raise ValueError("At least five distinct engine units are required for evaluation.")
    train_units, test_units = train_test_split(units, test_size=0.2, random_state=42)
    train_units, calibration_units = train_test_split(
        train_units, test_size=0.25, random_state=42
    )

    train_rows = df[df["unit_number"].isin(train_units)]
    calibration_rows = df[df["unit_number"].isin(calibration_units)]
    test_rows = df[df["unit_number"].isin(test_units)]
    feature_columns = ["rms", "peak_to_peak", "kurtosis"]
    train_healthy = train_rows[train_rows["label"] == 0]
    calibration_healthy = calibration_rows[calibration_rows["label"] == 0]
    test_healthy = test_rows[test_rows["label"] == 0]
    test_anomalous = test_rows[test_rows["label"] == 1]
    if any(
        frame.empty
        for frame in (
            train_healthy,
            calibration_healthy,
            test_healthy,
            test_anomalous,
        )
    ):
        raise ValueError(
            "The engine-unit split must contain healthy training, calibration, "
            "and test rows plus anomalous test rows."
        )

    scaler = StandardScaler()
    scaler.fit(train_healthy[feature_columns].values)

    def transform(frame):
        return scaler.transform(frame[feature_columns].values).astype(np.float32)

    return (
        transform(train_healthy),
        transform(calibration_healthy),
        transform(test_healthy),
        transform(test_anomalous),
        scaler.mean_,
        scaler.scale_,
    )


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
    errors = calculate_int8_errors(tflite_model, X_calibration)
    return float(np.percentile(errors, 95)), float(np.percentile(errors, 99.5))


def calculate_int8_errors(tflite_model, samples):
    """Return per-sample reconstruction MSE using the exported INT8 model."""
    if len(samples) == 0:
        raise ValueError("At least one sample is required to calculate reconstruction errors.")

    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()

    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]

    input_scale, input_zero_point = input_detail["quantization"]
    output_scale, output_zero_point = output_detail["quantization"]

    if input_scale <= 0 or output_scale <= 0:
        raise ValueError("TFLite input/output quantization scales must be positive.")

    errors = []
    for sample in samples:
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

    return np.asarray(errors, dtype=np.float32)


def evaluate_anomaly_detection(
    healthy_errors, anomalous_errors, warn_threshold, critical_threshold
):
    """Report holdout false-positive and anomaly-detection rates at calibrated thresholds."""
    if len(healthy_errors) == 0 or len(anomalous_errors) == 0:
        raise ValueError("Evaluation requires healthy and anomalous holdout samples.")
    if critical_threshold < warn_threshold:
        raise ValueError("Critical threshold must not be lower than the warning threshold.")

    def rates(errors, threshold):
        return float(np.mean(errors >= threshold))

    return {
        "healthy_samples": len(healthy_errors),
        "anomalous_samples": len(anomalous_errors),
        "healthy_false_positive_warn": rates(healthy_errors, warn_threshold),
        "healthy_false_positive_critical": rates(healthy_errors, critical_threshold),
        "anomaly_recall_warn": rates(anomalous_errors, warn_threshold),
        "anomaly_recall_critical": rates(anomalous_errors, critical_threshold),
    }


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
    (
        X_train,
        X_calibration,
        X_test_healthy,
        X_test_anomalous,
        feature_mean,
        feature_scale,
    ) = load_healthy_data()

    print("Building and training Autoencoder...")
    autoencoder = build_autoencoder()
    autoencoder.fit(
        X_train,
        X_train,  # Targets are identical to input for autoencoding
        epochs=20,
        batch_size=32,
        validation_data=(X_calibration, X_calibration),
        verbose=1
    )

    print("\nQuantizing Autoencoder to INT8...")
    tflite_model = convert_to_int8_tflite(autoencoder, X_train)

    mse_95, mse_99_5 = calculate_int8_thresholds(tflite_model, X_calibration)
    evaluation = evaluate_anomaly_detection(
        calculate_int8_errors(tflite_model, X_test_healthy),
        calculate_int8_errors(tflite_model, X_test_anomalous),
        mse_95,
        mse_99_5,
    )
    print("\nHeld-out engine-unit evaluation (thresholds calibrated on healthy units):")
    for name, value in evaluation.items():
        if name.endswith("_samples"):
            print(f"  {name}: {value}")
        else:
            print(f"  {name}: {value:.1%}")

    print("\nExporting model and thresholds to static C++ header...")
    export_c_header(
        tflite_model,
        mse_95,
        mse_99_5,
        feature_mean,
        feature_scale,
    )

if __name__ == "__main__":
    main()