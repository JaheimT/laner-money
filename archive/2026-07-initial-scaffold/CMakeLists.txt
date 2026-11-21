cmake_minimum_required(VERSION 3.16)
project(laner_money C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Compile with warnings-as-signal, not silenced. Security-relevant: catches
# a lot of the classic C footguns (implicit int conversions, unused results
# from functions like read()/write(), format string mismatches) at compile
# time instead of at runtime.
add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -Wshadow
    -Wconversion
    -Wformat=2
    -fstack-protector-strong
)

# Debug builds get sanitizers to catch memory bugs during development.
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-fsanitize=address,undefined -g)
    add_link_options(-fsanitize=address,undefined)
endif()

include_directories(include)

add_executable(laner_money
    src/main.c
)

# SQLite and other dependencies will be linked here once introduced.
