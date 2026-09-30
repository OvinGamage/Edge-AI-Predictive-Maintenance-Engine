#include <cstdio>
#include <cstdint>

#include "drivers/uart.hpp"
#include "core/ring_buffer.hpp"
#include "core/dsp_features.hpp"
#include "ml/model_runner.hpp"
#include "ml/model_data.h"

static constexpr std::size_t kCyclesPerWindow = 10;
static constexpr std::size_t kSensorsPerCycle = 5;
static constexpr std::size_t kWindowSamples = kCyclesPerWindow * kSensorsPerCycle;

// First ten FD001 cycles, channels s_2, s_3, s_4, s_11, and s_12.
static constexpr float kSimulatedSensorWindow[kCyclesPerWindow][kSensorsPerCycle] = {
    {641.82f, 1589.7f, 1400.6f, 47.47f, 521.66f},
    {642.15f, 1591.82f, 1403.14f, 47.49f, 522.28f},
    {642.35f, 1587.99f, 1404.2f, 47.27f, 522.42f},
    {642.35f, 1582.79f, 1401.87f, 47.13f, 522.86f},
    {642.37f, 1582.85f, 1406.22f, 47.28f, 522.19f},
    {642.1f, 1584.47f, 1398.37f, 47.16f, 521.68f},
    {642.48f, 1592.32f, 1397.77f, 47.36f, 522.32f},
    {642.56f, 1582.96f, 1400.97f, 47.24f, 522.47f},
    {642.12f, 1590.98f, 1394.8f, 47.29f, 521.79f},
    {641.71f, 1591.24f, 1400.46f, 47.03f, 521.79f}
};

int main() {
    // 1. Initialize Peripherals
    uart_init();
    uart_send_string("[SYS] Initializing Firmware Anomaly Detector...\r\n");

    // 2. Initialize Machine Learning Model Engine
    ModelRunner model_runner;
    if (!model_runner.init()) {
        uart_send_string("[ERR] Failed to initialize TFLm interpreter!\r\n");
        return -1;
    }
    uart_send_string("[SYS] Model Runner initialized successfully.\r\n");

    // 3. Initialize DSP Data Structures
    RingBuffer<float, kWindowSamples> ring_buffer;

    // Simulated sensor stream loop
    uart_send_string("[SYS] Starting Ingestion & Inference Loop...\r\n");
    
    // Simulate one ten-cycle window using the same sensor columns as training.
    for (std::size_t cycle = 0; cycle < kCyclesPerWindow; ++cycle) {
        for (std::size_t sensor = 0; sensor < kSensorsPerCycle; ++sensor) {
            ring_buffer.push(kSimulatedSensorWindow[cycle][sensor]);
        }
    }

    float raw_window[kWindowSamples];
    ring_buffer.extract_window(raw_window);
    const SensorFeatures features =
        DSPProcessor::extract_features(raw_window, ring_buffer.size());

    const float extracted_features[3] = {
        (features.rms - kFeatureMean[0]) / kFeatureScale[0],
        (features.peak_to_peak - kFeatureMean[1]) / kFeatureScale[1],
        (features.kurtosis - kFeatureMean[2]) / kFeatureScale[2]
    };

    // Feed standardized features to the model runner for tensor quantization.
    model_runner.set_input(extracted_features);

    // Run inference
    if (!model_runner.run()) {
        uart_send_string("[ERR] Inference execution failed!\r\n");
        return -1;
    }

    // Calculate Reconstruction MSE Error
    const float mse = model_runner.compute_reconstruction_mse();

    // Anomaly decision uses thresholds calibrated during training.
    char msg_buf[128];
    if (mse >= THRESHOLD_CRIT) {
        std::snprintf(msg_buf, sizeof(msg_buf),
                      "[CRITICAL ANOMALY] MSE: %.5f | Action: Emergency Shutdown Recommended\r\n", mse);
    } else if (mse >= THRESHOLD_WARN) {
        std::snprintf(msg_buf, sizeof(msg_buf),
                      "[WARNING] MSE: %.5f | Action: Inspection Required\r\n", mse);
    } else {
        std::snprintf(msg_buf, sizeof(msg_buf),
                      "[OK] MSE: %.5f | Status: Normal\r\n", mse);
    }

    uart_send_string(msg_buf);

    uart_send_string("[SYS] Ingestion loop completed.\r\n");
    return 0;
}
