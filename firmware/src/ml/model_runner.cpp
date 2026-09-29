#include "ml/model_runner.hpp"

bool ModelRunner::init() {
    // Register Ops needed for Dense Autoencoder
    resolver.AddFullyConnected();
    resolver.AddRelu();
    resolver.AddQuantize();
    resolver.AddDequantize();
    resolver.AddReshape();

    // 1. Map model
    model = tflite::GetModel(g_model);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        return false;
    }

    // 2. Instantiate interpreter
    static tflite::MicroInterpreter static_interpreter(
        model, resolver, tensor_arena, kTensorArenaSize);
    interpreter = &static_interpreter;

    // 3. Allocate tensor memory
    if (interpreter->AllocateTensors() != kTfLiteOk) {
        return false;
    }

    input_tensor = interpreter->input(0);
    output_tensor = interpreter->output(0);
    return true;
}

void ModelRunner::set_input(const int8_t quantized_input[3]) {
    if (input_tensor != nullptr && input_tensor->data.int8 != nullptr) {
        for (int i = 0; i < 3; i++) {
            input_tensor->data.int8[i] = quantized_input[i];
        }
    }
}

bool ModelRunner::run() {
    if (interpreter == nullptr) return false;
    return interpreter->Invoke() == kTfLiteOk;
}

const int8_t* ModelRunner::get_output() const {
    if (output_tensor == nullptr) return nullptr;
    return output_tensor->data.int8;
}

float ModelRunner::compute_reconstruction_mse() const {
    if (input_tensor == nullptr || output_tensor == nullptr) {
        return 0.0f;
    }

    float input_scale = input_tensor->params.scale;
    int32_t input_zp = input_tensor->params.zero_point;
    float output_scale = output_tensor->params.scale;
    int32_t output_zp = output_tensor->params.zero_point;

    float mse = 0.0f;
    for (int i = 0; i < 3; i++) {
        float in_dequant = (static_cast<float>(input_tensor->data.int8[i]) - input_zp) * input_scale;
        float out_dequant = (static_cast<float>(output_tensor->data.int8[i]) - output_zp) * output_scale;
        float diff = in_dequant - out_dequant;
        mse += diff * diff;
    }
    return mse / 3.0f; // Mean squared error across 3 features
}