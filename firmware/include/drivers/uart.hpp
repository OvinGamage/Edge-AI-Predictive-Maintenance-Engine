#ifndef PERIPHERALS_UART_HPP
#define PERIPHERALS_UART_HPP

#include <cstdint>
#include <cstddef>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the hardware UART peripheral interface (115200 8N1).
 */
void uart_init(void);

/**
 * @brief Transmit a single character over UART.
 * @param c Character byte to transmit.
 */
void uart_send_char(char c);

/**
 * @brief Transmit a null-terminated string over UART.
 * @param str Pointer to the null-terminated C-string.
 */
void uart_send_string(const char* str);

/**
 * @brief Transmit a raw buffer of bytes over UART.
 * @param data Pointer to byte buffer.
 * @param length Number of bytes to transmit.
 */
void uart_send_bytes(const uint8_t* data, size_t length);

/**
 * @brief Read a single character from UART (blocking or non-blocking depending on implementation).
 * @return Character received, or negative value on timeout/error.
 */
int uart_read_char(void);

#ifdef __cplusplus
}
#endif

#endif // PERIPHERALS_UART_HPP
