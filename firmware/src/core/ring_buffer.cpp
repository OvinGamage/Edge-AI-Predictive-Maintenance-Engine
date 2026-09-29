#include <cstdint>
#include <cstddef>
#include <algorithm>

template <typename T, size_t Capacity>
class RingBuffer {
private:
    T buffer[Capacity];
    size_t head = 0;
    size_t tail = 0;
    size_t count = 0;

public:
    RingBuffer() = default;

    bool push(const T& item) {
        buffer[head] = item;
        head = (head + 1) % Capacity;
        if (count < Capacity) {
            count++;
        } else {
            tail = (tail + 1) % Capacity; // Overwrite oldest data
        }
        return true;
    }

    bool pop(T& item) {
        if (count == 0) return false;
        item = buffer[tail];
        tail = (tail + 1) % Capacity;
        count--;
        return true;
    }

    size_t size() const { return count; }
    size_t capacity() const { return Capacity; }
    bool is_full() const { return count == Capacity; }

    void clear() {
        head = 0;
        tail = 0;
        count = 0;
    }

    // Get contiguous snapshot or element by index from oldest to newest
    T get(size_t index) const {
        return buffer[(tail + index) % Capacity];
    }
};