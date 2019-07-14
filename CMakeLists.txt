cmake_minimum_required(VERSION 3.1)

project(gweek-binding VERSION 0.1
    DESCRIPTION "C++ OpenGL Binding Generator"
    LANGUAGES CXX)

find_package(Python3 REQUIRED Interpreter)

set(gweek_binding_include ${CMAKE_CURRENT_SOURCE_DIR}/include)
set(gweek_binding_srcs ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_library(gweek STATIC
)

target_include_directories(gweek PUBLIC include)
target_compile_features(gweek PRIVATE cxx_std_17)