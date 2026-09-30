#include <gtest/gtest.h>
#include <vector>
#include <cmath>
#include "core/dsp_features.hpp"

TEST(DSPFeaturesTest, NullOrEmptyInputReturnsZeroes) {
    SensorFeatures f1 = DSPProcessor::extract_features(nullptr, 100);
    EXPECT_FLOAT_EQ(f1.rms, 0.0f);
    EXPECT_FLOAT_EQ(f1.peak_to_peak, 0.0f);
    EXPECT_FLOAT_EQ(f1.kurtosis, 0.0f);

    float data[4] = {1.0f, 2.0f, 3.0f, 4.0f};
    SensorFeatures f2 = DSPProcessor::extract_features(data, 0);
    EXPECT_FLOAT_EQ(f2.rms, 0.0f);
    EXPECT_FLOAT_EQ(f2.peak_to_peak, 0.0f);
    EXPECT_FLOAT_EQ(f2.kurtosis, 0.0f);
}

TEST(DSPFeaturesTest, ConstantDCConstantSignal) {
    // Constant signal [5.0, 5.0, 5.0, 5.0]
    std::vector<float> signal(100, 5.0f);
    SensorFeatures features = DSPProcessor::extract_features(signal.data(), signal.size());

    EXPECT_NEAR(features.rms, 5.0f, 1e-4f);
    EXPECT_FLOAT_EQ(features.peak_to_peak, 0.0f);
    // Kurtosis zero-variance guard should return 0.0f instead of NaN/Inf
    EXPECT_FLOAT_EQ(features.kurtosis, 0.0f);
}

TEST(DSPFeaturesTest, SineWaveKnownRMSAndP2P) {
    // Generate 1 kHz Sine wave at 100 kHz sample rate (A = 2.0)
    constexpr std::size_t N = 1000;
    std::vector<float> sine_wave(N);
    constexpr float amplitude = 2.0f;
    constexpr float pi = 3.14159265358979323846f;

    for (std::size_t i = 0; i < N; ++i) {
        sine_wave[i] = amplitude * std::sin(2.0f * pi * static_cast<float>(i) / 100.0f);
    }

    SensorFeatures features = DSPProcessor::extract_features(sine_wave.data(), sine_wave.size());

    // Theoretical RMS of A * sin(wt) is A / sqrt(2) ≈ 2.0 / 1.4142135 = 1.4142135
    EXPECT_NEAR(features.rms, amplitude / std::sqrt(2.0f), 1e-2f);

    // Peak-to-Peak should be 2 * Amplitude = 4.0
    EXPECT_NEAR(features.peak_to_peak, 2.0f * amplitude, 1e-2f);

    // Fisher excess kurtosis for a pure sine wave is -1.5.
    EXPECT_NEAR(features.kurtosis, -1.5f, 1e-1f);
}

TEST(DSPFeaturesTest, ImpulsePeakKurtosisSpike) {
    // Zero baseline with a single large impulse spike
    std::vector<float> signal(1000, 0.0f);
    signal[500] = 50.0f; // Impulse

    SensorFeatures features = DSPProcessor::extract_features(signal.data(), signal.size());

    EXPECT_FLOAT_EQ(features.peak_to_peak, 50.0f);
    // Impulse signals produce significantly higher kurtosis values (> 100)
    EXPECT_GT(features.kurtosis, 100.0f);
}
