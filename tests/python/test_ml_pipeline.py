import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml_pipeline"))

try:
    import numpy as np
    import tensorflow as tf

    import train
except ImportError:
    np = None
    tf = None
    train = None


@unittest.skipIf(tf is None, "ML pipeline tests require TensorFlow, NumPy, Pandas, and scikit-learn")
class ModelConversionTests(unittest.TestCase):
    def test_scaling_uses_healthy_training_units_only(self):
        rows = []
        for unit in range(10):
            for cycle in range(40):
                rows.append(
                    {
                        "unit_number": unit,
                        "time_cycles": cycle,
                        "rms": unit * 100 + cycle,
                        "peak_to_peak": unit * 10 + cycle * 0.2,
                        "kurtosis": unit * 2 + cycle * 0.03,
                        "label": int(cycle >= 30),
                    }
                )
        frame = train.pd.DataFrame(rows)
        units = frame["unit_number"].drop_duplicates().to_numpy()
        training_units, _ = train.train_test_split(
            units, test_size=0.2, random_state=42
        )
        training_units, _ = train.train_test_split(
            training_units, test_size=0.25, random_state=42
        )
        feature_columns = ["rms", "peak_to_peak", "kurtosis"]
        training_healthy = frame[
            frame["unit_number"].isin(training_units) & (frame["label"] == 0)
        ]
        expected_mean = training_healthy[feature_columns].values.mean(axis=0)

        with patch.object(train, "DATA_PATH", "synthetic.csv"), patch.object(
            train.os.path, "exists", return_value=True
        ), patch.object(train.pd, "read_csv", return_value=frame):
            X_train, X_calibration, X_test_healthy, X_test_anomalous, mean, _ = (
                train.load_healthy_data()
            )

        np.testing.assert_allclose(mean, expected_mean)
        np.testing.assert_allclose(X_train.mean(axis=0), 0.0, atol=1e-6)
        self.assertEqual(len(X_train), len(training_healthy))
        self.assertGreater(len(X_calibration), 0)
        self.assertGreater(len(X_test_healthy), 0)
        self.assertGreater(len(X_test_anomalous), 0)

    def test_conversion_produces_runnable_int8_model(self):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(3,)),
                tf.keras.layers.Dense(3, activation="relu"),
                tf.keras.layers.Dense(3, activation="linear"),
            ]
        )
        samples = np.asarray(
            [[-1.0, 0.0, 1.0], [0.5, -0.5, 0.25], [1.0, 1.0, -1.0]],
            dtype=np.float32,
        )

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(train, "TFLITE_MODEL_PATH", str(Path(directory) / "model.tflite")):
                model_bytes = train.convert_to_int8_tflite(model, samples)

        interpreter = tf.lite.Interpreter(model_content=model_bytes)
        interpreter.allocate_tensors()
        input_detail = interpreter.get_input_details()[0]
        output_detail = interpreter.get_output_details()[0]
        self.assertEqual(input_detail["dtype"], np.int8)
        self.assertEqual(output_detail["dtype"], np.int8)

        scale, zero_point = input_detail["quantization"]
        quantized = np.clip(
            np.rint(samples[0:1] / scale + zero_point), -128, 127
        ).astype(np.int8)
        interpreter.set_tensor(input_detail["index"], quantized)
        interpreter.invoke()
        self.assertEqual(interpreter.get_tensor(output_detail["index"]).shape, (1, 3))

    def test_evaluation_reports_holdout_false_positive_and_recall_rates(self):
        result = train.evaluate_anomaly_detection(
            np.asarray([0.1, 0.2, 0.7]),
            np.asarray([0.8, 1.2]),
            warn_threshold=0.5,
            critical_threshold=1.0,
        )
        self.assertEqual(result["healthy_false_positive_warn"], 1 / 3)
        self.assertEqual(result["healthy_false_positive_critical"], 0.0)
        self.assertEqual(result["anomaly_recall_warn"], 1.0)
        self.assertEqual(result["anomaly_recall_critical"], 0.5)


if __name__ == "__main__":
    unittest.main()
