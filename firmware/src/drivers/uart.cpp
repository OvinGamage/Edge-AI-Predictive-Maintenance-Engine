#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <cstdint>
// Platform-independent UART interface wrapper
class UARTLogger {
private:
    std::uint32_t baud_rate;

public:
    UARTLogger(uint32_t baud = 115200) : baud_rate(baud) {}

    void init() {
        // Platform-specific initialization (e.g., Serial.begin(baud) or HAL_UART_Init)
    }

    void print(const char* str) {
        // Replace with platform write call: e.g., Serial.print(str) or HAL_UART_Transmit(...)
        printf("%s", str);
    }

    void printf_log(const char* format, ...) {
        char buffer[128];
        va_list args;
        va_start(args, format);
        vsnprintf(buffer, sizeof(buffer), format, args);
        va_end(args);
        print(buffer);
    }

    void log_status(const char* tag, float mse, int status_code) {
        printf_log("[%s] Reconstruction MSE: %.5f | Status Code: %d\r\n", tag, mse, status_code);
    }
};