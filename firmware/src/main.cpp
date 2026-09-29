#include <cstdio>
#include <cstdint>

#include "peripherals/uart.hpp"
#include "dsp/ring_buffer.hpp"
#include "dsp/dsp_features.hpp"
#include "ml/model_runner.hpp"

// Anomaly Detection Thresholds (Tuned during training)
static constexpr float kWarningThreshold  = 0.045f;
static constexpr float kCriticalThreshold = 0.090f;

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
    RingBuffer ring_buffer;
    ring_buffer_init(&ring_buffer);

    // Simulated sensor stream loop
    uart_send_string("[SYS] Starting Ingestion & Inference Loop...\r\n");
    
    // Example: Process 10 simulated sensor read iterations
    for (int iteration = 0; iteration < 10; ++iteration) {
        // Simulate reading 3-axis accelerometer/vibration data (X, Y, Z)
        // In production, replace with hardware I2C/SPI sensor reads
        float raw_sensor_samples[3] = {
            1.0f + (iteration * 0.05f),
            0.5f - (iteration * 0.02f),
            -0.2f + (iteration * 0.08f)
        };

        // Push new raw sample to ring buffer
        for (int i = 0; i < 3; ++i) {
            ring_buffer_push(&ring_buffer, raw_sensor_samples[i]);
        }

        // Extract 3 normalized statistical features (e.g., Mean, Variance, RMS)
        int8_t quantized_features[3];
        dsp_extract_features(&ring_buffer, quantized_features);

        // Feed features into TFLm input tensor
        model_runner.set_input(quantized_features);

        // Run inference
        if (!model_runner.run()) {
            uart_send_string("[ERR] Inference execution failed!\r\n");
            continue;
        }

        // Calculate Reconstruction MSE Error
        float mse = model_runner.compute_reconstruction_mse();

        // 4. Anomaly Decision Logic & Telemetry Output
        char msg_buf[128];
        if (mse >= kCriticalThreshold) {
            std::snprintf(msg_buf, sizeof(msg_buf), 
                          "[CRITICAL ANOMALY] MSE: %.5f | Action: Emergency Shutdown Recommended\r\n", mse);
        } else if (mse >= kWarningThreshold) {
            std::snprintf(msg_buf, sizeof(msg_buf), 
                          "[WARNING] MSE: %.5f | Action: Inspection Required\r\n", mse);
        } else {
            std::snprintf(msg_buf, sizeof(msg_buf), 
                          "[OK] MSE: %.5f | Status: Normal\r\n", mse);
        }
        
        uart_send_string(msg_buf);
    }

    uart_send_string("[SYS] Ingestion loop completed.\r\n");
    return 0;
}
