#pragma once

#include <cstddef>
#include <array>
#include <optional>
#include <algorithm>

template <typename T, std::size_t Capacity>
class RingBuffer {
    static_assert(Capacity > 0, "RingBuffer capacity must be greater than 0");

public:
    RingBuffer() = default;

    // Push new item. Overwrites oldest item if capacity is reached.
    void push(const T& item) {
        buffer_[head_] = item;
        head_ = (head_ + 1) % Capacity;

        if (full_) {
            tail_ = (tail_ + 1) % Capacity; // Advance tail to discard oldest sample
        } else if (head_ == tail_) {
            full_ = true;
        }
    }

    // Pop oldest item from buffer
    std::optional<T> pop() {
        if (is_empty()) {
            return std::nullopt;
        }

        T item = buffer_[tail_];
        full_ = false;
        tail_ = (tail_ + 1) % Capacity;
        return item;
    }

    // Copies current contiguous window buffer into output target array
    void extract_window(T* dest) const {
        std::size_t current_size = size();
        for (std::size_t i = 0; i < current_size; ++i) {
            dest[i] = buffer_[(tail_ + i) % Capacity];
        }
    }

    [[nodiscard]] bool is_empty() const { return (!full_ && (head_ == tail_)); }
    [[nodiscard]] bool is_full() const { return full_; }
    
    [[nodiscard]] std::size_t size() const {
        if (full_) return Capacity;
        if (head_ >= tail_) return head_ - tail_;
        return Capacity + head_ - tail_;
    }

    [[nodiscard]] constexpr std::size_t capacity() const { return Capacity; }

    void clear() {
        head_ = 0;
        tail_ = 0;
        full_ = false;
    }

private:
    std::array<T, Capacity> buffer_{};
    std::size_t head_{0};
    std::size_t tail_{0};
    bool full_{false};
};
