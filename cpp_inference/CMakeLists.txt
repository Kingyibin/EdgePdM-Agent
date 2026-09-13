cmake_minimum_required(VERSION 3.16)
project(edgepdm_infer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(ONNXRUNTIME_ROOT "${CMAKE_SOURCE_DIR}/../third_party/onnxruntime-win-x64-1.20.1" CACHE PATH "ONNX Runtime root")

add_executable(edgepdm_infer
  src/main.cpp
)

target_include_directories(edgepdm_infer PRIVATE
  ${ONNXRUNTIME_ROOT}/include
  ${CMAKE_SOURCE_DIR}/src
)

target_link_directories(edgepdm_infer PRIVATE ${ONNXRUNTIME_ROOT}/lib)
# MinGW import library created via dlltool
target_link_libraries(edgepdm_infer PRIVATE onnxruntime)

# Copy DLL next to binary after build
add_custom_command(TARGET edgepdm_infer POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${ONNXRUNTIME_ROOT}/lib/onnxruntime.dll"
    "$<TARGET_FILE_DIR:edgepdm_infer>/onnxruntime.dll"
)
