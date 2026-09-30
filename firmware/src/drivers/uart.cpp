#include <cstdint>
#include "drivers/uart.hpp"

namespace {

constexpr std::uintptr_t kUart0Base = 0x40004000u;
constexpr std::uintptr_t kDataOffset = 0x00u;
constexpr std::uintptr_t kStateOffset = 0x04u;
constexpr std::uintptr_t kControlOffset = 0x08u;
constexpr std::uintptr_t kBaudDivOffset = 0x10u;
constexpr std::uint32_t kTxFull = 1u << 0;
constexpr std::uint32_t kRxFull = 1u << 1;
constexpr std::uint32_t kTxEnable = 1u << 0;
constexpr std::uint32_t kRxEnable = 1u << 1;
constexpr std::uint32_t kPeripheralClockHz = 25000000u;
constexpr std::uint32_t kBaudRate = 115200u;

volatile std::uint32_t& uart_register(std::uintptr_t offset) {
    return *reinterpret_cast<volatile std::uint32_t*>(kUart0Base + offset);
}

}  // namespace

extern "C" void uart_init(void) {
    uart_register(kControlOffset) = 0;
    uart_register(kBaudDivOffset) = kPeripheralClockHz / kBaudRate;
    uart_register(kControlOffset) = kTxEnable | kRxEnable;
}

extern "C" void uart_send_char(char c) {
    while ((uart_register(kStateOffset) & kTxFull) != 0) {
    }
    uart_register(kDataOffset) = static_cast<std::uint8_t>(c);
}

extern "C" void uart_send_string(const char* str) {
    if (str == nullptr) {
        return;
    }
    while (*str != '\0') {
        uart_send_char(*str++);
    }
}

extern "C" void uart_send_bytes(const std::uint8_t* data, std::size_t length) {
    if (data == nullptr) {
        return;
    }
    for (std::size_t i = 0; i < length; ++i) {
        uart_send_char(static_cast<char>(data[i]));
    }
}

extern "C" int uart_read_char(void) {
    if ((uart_register(kStateOffset) & kRxFull) == 0) {
        return -1;
    }
    return static_cast<int>(uart_register(kDataOffset) & 0xFFu);
}