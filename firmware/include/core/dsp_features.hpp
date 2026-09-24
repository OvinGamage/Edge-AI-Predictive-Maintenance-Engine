#pragma once

#include <cstddef>
#include <cmath>
#include <algorithm>
#include <numeric>

// Struct containing the extracted time-domain features
struct SensorFeatures {
    float rms{0.0f};
    float peak_to_peak{0.0f};
    float kurtosis{0.0f};
};

class DSPProcessor {
public:
    DSPProcessor() = default;

    /**
     * @brief Computes RMS, Peak-to-Peak, and Kurtosis over a contiguous sample window.
     * 
     * @param raw_window Pointer to the contiguous float array (e.g. extracted from RingBuffer).
     * @param window_size Number of elements in raw_window.
     * @return SensorFeatures Struct populated with calculated DSP features.
     */
    static SensorFeatures extract_features(const float* raw_window, std::size_t window_size) {
        SensorFeatures features{};

        // Guard against null pointers or empty processing windows
        if (raw_window == nullptr || window_size == 0) {
            return features;
        }

        float sum_squares = 0.0f;
        float sum = 0.0f;
        float min_val = raw_window[0];
        float max_val = raw_window[0];

        // First pass: compute Sum, Sum of Squares, Min, and Max
        for (std::size_t i = 0; i < window_size; ++i) {
            float val = raw_window[i];
            sum_squares += val * val;
            sum += val;
            min_val = std::min(min_val, val);
            max_val = std::max(max_val, val);
        }

        // 1. Root Mean Square (RMS)
        features.rms = std::sqrt(sum_squares / static_cast<float>(window_size));

        // 2. Peak-to-Peak
        features.peak_to_peak = max_val - min_val;

        // 3. Kurtosis (Fourth standardized moment)
        float mean = sum / static_cast<float>(window_size);
        float variance_sum = 0.0f;
        float fourth_moment_sum = 0.0f;

        for (std::size_t i = 0; i < window_size; ++i) {
            float diff = raw_window[i] - mean;
            variance_sum += diff * diff;
            fourth_moment_sum += diff * diff * diff * diff;
        }

        float variance = variance_sum / static_cast<float>(window_size);

        // Guard against division by zero for flat/DC signals
        if (variance > 1e-7f) {
            features.kurtosis = (fourth_moment_sum / static_cast<float>(window_size)) / (variance * variance);
        } else {
            features.kurtosis = 0.0f;
        }

        return features;
    }
};
