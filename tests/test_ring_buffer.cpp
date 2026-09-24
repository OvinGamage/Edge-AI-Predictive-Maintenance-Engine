#include <gtest/gtest.h>
#include "core/ring_buffer.hpp"

// Test fixture for a float buffer of capacity 4
class RingBufferTest : public ::testing::Test {
protected:
    static constexpr std::size_t CAPACITY = 4;
    RingBuffer<float, CAPACITY> buffer;
};

TEST_F(RingBufferTest, InitiallyEmpty) {
    EXPECT_TRUE(buffer.is_empty());
    EXPECT_FALSE(buffer.is_full());
    EXPECT_EQ(buffer.size(), 0);
    EXPECT_EQ(buffer.capacity(), CAPACITY);
    EXPECT_EQ(buffer.pop(), std::nullopt);
}

TEST_F(RingBufferTest, PushAndPopSingleElement) {
    buffer.push(10.5f);

    EXPECT_FALSE(buffer.is_empty());
    EXPECT_FALSE(buffer.is_full());
    EXPECT_EQ(buffer.size(), 1);

    auto item = buffer.pop();
    ASSERT_TRUE(item.has_value());
    EXPECT_FLOAT_EQ(item.value(), 10.5f);

    EXPECT_TRUE(buffer.is_empty());
    EXPECT_EQ(buffer.size(), 0);
}

TEST_F(RingBufferTest, FillToCapacity) {
    buffer.push(1.0f);
    buffer.push(2.0f);
    buffer.push(3.0f);
    buffer.push(4.0f);

    EXPECT_TRUE(buffer.is_full());
    EXPECT_FALSE(buffer.is_empty());
    EXPECT_EQ(buffer.size(), CAPACITY);
}

TEST_F(RingBufferTest, OverwriteOldestWhenFull) {
    // Fill buffer: [1.0, 2.0, 3.0, 4.0]
    for (float i = 1.0f; i <= 4.0f; ++i) {
        buffer.push(i);
    }
    EXPECT_TRUE(buffer.is_full());

    // Push 5.0f, overwriting 1.0f -> expected state: [2.0, 3.0, 4.0, 5.0]
    buffer.push(5.0f);

    EXPECT_TRUE(buffer.is_full());
    EXPECT_EQ(buffer.size(), CAPACITY);

    // Verify first pop is 2.0f (1.0f was discarded)
    auto item = buffer.pop();
    ASSERT_TRUE(item.has_value());
    EXPECT_FLOAT_EQ(item.value(), 2.0f);
}

TEST_F(RingBufferTest, ExtractLinearizedWindow) {
    // Fill and overflow slightly to shift head and tail
    // Push: 1, 2, 3, 4, 5 -> Buffer contents: [2, 3, 4, 5]
    for (float i = 1.0f; i <= 5.0f; ++i) {
        buffer.push(i);
    }

    float window[CAPACITY] = {0.0f};
    buffer.extract_window(window);

    EXPECT_FLOAT_EQ(window[0], 2.0f);
    EXPECT_FLOAT_EQ(window[1], 3.0f);
    EXPECT_FLOAT_EQ(window[2], 4.0f);
    EXPECT_FLOAT_EQ(window[3], 5.0f);
}

TEST_F(RingBufferTest, ClearResetsState) {
    buffer.push(42.0f);
    buffer.push(84.0f);
    buffer.clear();

    EXPECT_TRUE(buffer.is_empty());
    EXPECT_FALSE(buffer.is_full());
    EXPECT_EQ(buffer.size(), 0);
    EXPECT_EQ(buffer.pop(), std::nullopt);
}
