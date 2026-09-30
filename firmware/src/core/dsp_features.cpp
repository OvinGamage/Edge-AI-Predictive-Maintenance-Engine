#include <cstdint>
#include <cmath>
#include <algorithm>

struct NormalizationParams {
    float min_val;
    float max_val;
};

class DSPFeatureExtractor {
private:
    // Update these 3 min-max bounds to match your training set parameters exactly
    NormalizationParams norm_params[3] = {
        {0.0f, 100.0f},  // Feature 0 (e.g., Sensor 1 Min/Max)
        {0.0f, 500.0f},  // Feature 1 (e.g., Sensor 2 Min/Max)
        {0.0f, 50.0f}    // Feature 2 (e.g., Sensor 3 Min/Max)
    };

public:
    DSPFeatureExtractor() = default;

    // Normalizes raw float inputs into [0.0, 1.0] range
    void normalize_features(const float raw_input[3], float normalized_output[3]) {
        for (int i = 0; i < 3; i++) {
            float min_v = norm_params[i].min_val;
            float max_v = norm_params[i].max_val;
            float clamped = std::clamp(raw_input[i], min_v, max_v);
            normalized_output[i] = (clamped - min_v) / (max_v - min_v + 1e-6f);
        }
    }

    // Quantizes normalized float to int8_t using TFLite scale and zero point
    int8_t quantize_sample(float value, float scale, int32_t zero_point) {
        int32_t qval = static_cast<int32_t>(std::round(value / scale)) + zero_point;
        return static_cast<int8_t>(
            std::clamp<std::int32_t>(qval, -128, 127));
    }

    // Dequantizes int8_t model output back to float for MSE loss calculation
    float dequantize_sample(int8_t qvalue, float scale, int32_t zero_point) {
        return (static_cast<float>(qvalue) - zero_point) * scale;
    }
};