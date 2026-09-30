from pathlib import Path
import pandas as pd  # type: ignore[import-not-found]
import numpy as np  # type: ignore[import-not-found]
from scipy.stats import kurtosis  # type: ignore[import-not-found]

# 1. Define paths relative to the project root
DATA_DIR = Path(__file__).parent / "data"
RAW_FILE = DATA_DIR / "train_FD001.txt"
OUTPUT_FILE = DATA_DIR / "processed_features.csv"

# 2. Schema definition for NASA CMAPSS FD001 (26 raw columns)
index_names = ['unit_number', 'time_cycles']
setting_names = ['setting_1', 'setting_2', 'setting_3']
sensor_names = [f's_{i}' for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names


def extract_window_features(window):
    """Computes RMS, Peak-to-Peak, and Kurtosis across core sensor channels."""
    # Flatten the selected informative sensors across the time window
    signal = window[['s_2', 's_3', 's_4', 's_11', 's_12']].values.flatten()

    rms = np.sqrt(np.mean(signal**2))
    peak_to_peak = np.ptp(signal)
    kurt = kurtosis(signal, fisher=True, bias=True)
    if not np.isfinite(kurt):
        kurt = 0.0

    return pd.Series(
        [rms, peak_to_peak, kurt],
        index=['rms', 'peak_to_peak', 'kurtosis']
    )


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Could not find raw data at {RAW_FILE}. "
            "Please unzip train_FD001.txt into ml_pipeline/data/ first."
        )

    print(f"Loading raw dataset from {RAW_FILE}...")
    df = pd.read_csv(RAW_FILE, sep=r'\s+', header=None, names=col_names)

    # Calculate Remaining Useful Life (RUL) and Binary Health Label
    # Label = 1 (Anomaly) if engine is within 30 cycles of failure, else 0 (Normal)
    df['max_cycle'] = df.groupby('unit_number')['time_cycles'].transform('max')
    df['RUL'] = df['max_cycle'] - df['time_cycles']
    df['label'] = (df['RUL'] <= 30).astype(int)

    print("Extracting DSP features across rolling engine windows...")
    window_size = 10
    features_list = []

    # Process each engine trajectory independently to avoid window bleeding across units
    for unit_id, group in df.groupby('unit_number'):
        group = group.reset_index(drop=True)
        for i in range(len(group) - window_size + 1):
            window = group.iloc[i : i + window_size]
            features = extract_window_features(window)
            
            # Use the health label of the latest cycle in the window
            features['label'] = window['label'].iloc[-1]
            features['unit_number'] = unit_id
            features['time_cycles'] = window['time_cycles'].iloc[-1]
            
            features_list.append(features)

    # Reassemble features into a single DataFrame
    processed_df = pd.DataFrame(features_list)

    # Reorder columns for clean presentation
    cols = ['unit_number', 'time_cycles', 'rms', 'peak_to_peak', 'kurtosis', 'label']
    processed_df = processed_df[cols]

    # Save automatically to CSV
    processed_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Done! Successfully saved {len(processed_df)} feature vectors to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
