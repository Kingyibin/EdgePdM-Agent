/**
 * EdgePdM-Agent C++ ONNX inference smoke test.
 *
 * Reads a pre-scaled window CSV (rows=window, cols=features),
 * runs rul_lstm.onnx, prints predicted RUL and latency.
 *
 * Usage:
 *   edgepdm_infer.exe <onnx_path> <window_csv> [warmup=5] [iters=50]
 */

#include <onnxruntime_cxx_api.h>

#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::vector<float> load_csv_matrix(const std::string& path, size_t& rows, size_t& cols) {
  std::ifstream in(path);
  if (!in) {
    throw std::runtime_error("cannot open csv: " + path);
  }
  std::vector<float> data;
  rows = 0;
  cols = 0;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::stringstream ss(line);
    std::string cell;
    size_t c = 0;
    while (std::getline(ss, cell, ',')) {
      data.push_back(std::stof(cell));
      ++c;
    }
    if (rows == 0) cols = c;
    else if (c != cols) throw std::runtime_error("ragged csv rows");
    ++rows;
  }
  return data;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc < 3) {
      std::cerr << "Usage: " << argv[0]
                << " <model.onnx> <window.csv> [warmup] [iters]\n";
      return 2;
    }
    const std::string model_path = argv[1];
    const std::string csv_path = argv[2];
    const int warmup = (argc >= 4) ? std::stoi(argv[3]) : 5;
    const int iters = (argc >= 5) ? std::stoi(argv[4]) : 50;

    size_t rows = 0, cols = 0;
    auto values = load_csv_matrix(csv_path, rows, cols);
    std::cout << "Loaded window: " << rows << " x " << cols << "\n";

    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "edgepdm");
    Ort::SessionOptions opts;
    opts.SetIntraOpNumThreads(1);
    opts.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

#ifdef _WIN32
    std::wstring wmodel(model_path.begin(), model_path.end());
    Ort::Session session(env, wmodel.c_str(), opts);
#else
    Ort::Session session(env, model_path.c_str(), opts);
#endif

    Ort::AllocatorWithDefaultOptions allocator;
    auto input_name = session.GetInputNameAllocated(0, allocator);
    auto output_name = session.GetOutputNameAllocated(0, allocator);

    std::array<int64_t, 3> shape{1, static_cast<int64_t>(rows), static_cast<int64_t>(cols)};
    Ort::MemoryInfo mem = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
        mem, values.data(), values.size(), shape.data(), shape.size());

    const char* input_names[] = {input_name.get()};
    const char* output_names[] = {output_name.get()};

    for (int i = 0; i < warmup; ++i) {
      auto outs = session.Run(Ort::RunOptions{nullptr}, input_names, &input_tensor, 1, output_names, 1);
    }

    double total_ms = 0.0;
    float last_pred = 0.0f;
    for (int i = 0; i < iters; ++i) {
      auto t0 = std::chrono::steady_clock::now();
      auto outs = session.Run(Ort::RunOptions{nullptr}, input_names, &input_tensor, 1, output_names, 1);
      auto t1 = std::chrono::steady_clock::now();
      total_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
      float* out = outs[0].GetTensorMutableData<float>();
      last_pred = out[0];
    }

    const double avg_ms = total_ms / iters;
    std::cout << "predicted_rul=" << last_pred << "\n";
    std::cout << "latency_ms_avg=" << avg_ms << " (warmup=" << warmup << ", iters=" << iters << ")\n";
    std::cout << "throughput_qps=" << (1000.0 / avg_ms) << "\n";
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << "ERROR: " << ex.what() << "\n";
    return 1;
  }
}
