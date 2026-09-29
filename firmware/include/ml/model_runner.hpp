#ifndef MODEL_RUNNER_HPP
#define MODEL_RUNNER_HPP

#include <cstdint>

#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_data.h"

class ModelRunner {
private:
    static constexpr int kTensorArenaSize = 8 * 1024;
    alignas(16) uint8_t tensor_arena[kTensorArenaSize];

    const tflite::Model* model = nullptr;
    tflite::MicroInterpreter* interpreter = nullptr;
    TfLiteTensor* input_tensor = nullptr;
    TfLiteTensor* output_tensor = nullptr;
    
    // Autoencoder uses 6 standard operators: FullyConnected, Relu, Quantize, Dequantize, etc.
    tflite::MicroMutableOpResolver<10> resolver;

public:
    ModelRunner() = default;

    bool init();
    void set_input(const int8_t quantized_input[3]);
    bool run();
    const int8_t* get_output() const;
    float compute_reconstruction_mse() const;
};

#endif // MODEL_RUNNER_HPP