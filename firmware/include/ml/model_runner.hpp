#ifndef MODEL_RUNNER_HPP
#define MODEL_RUNNER_HPP

#include <cstdint>

#if __has_include("tensorflow/lite/micro/all_ops_resolver.h") && \
    __has_include("tensorflow/lite/micro/micro_interpreter.h") && \
    __has_include("tensorflow/lite/schema/schema_generated.h") && \
    __has_include("model_data.h")
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "model_data.h"
#else
namespace tflite {
class Model;
// Provide a complete fallback type so the header remains compilable when the
// TensorFlow Lite Micro headers are unavailable.
class AllOpsResolver {};
class MicroInterpreter;
}  // namespace tflite

struct TfLiteTensor;
#endif

class ModelRunner {
private:
    static constexpr int kTensorArenaSize = 8 * 1024; // 8 KB arena
    alignas(16) uint8_t tensor_arena[kTensorArenaSize];

    const tflite::Model* model = nullptr;
    tflite::MicroInterpreter* interpreter = nullptr;
    TfLiteTensor* input_tensor = nullptr;
    TfLiteTensor* output_tensor = nullptr;
    tflite::AllOpsResolver resolver;

public:
    ModelRunner() = default;
    
    bool init();
    void set_input(const int8_t quantized_input[3]);
    bool run();
    const int8_t* get_output() const;
    float compute_reconstruction_mse() const;
};

#endif // MODEL_RUNNER_HPP