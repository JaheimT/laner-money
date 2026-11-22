# Laner Money — top-level build file.
#
# Usage (from the repo root):
#   cmake -S . -B build            # configure (Debug by default, see below)
#   cmake --build build            # compile
#   ./build/laner                  # run
#
# Release build:
#   cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
#   cmake --build build-release

# 3.20 is old enough for Ubuntu 22.04 / Debian 12 LXC templates, new enough
# for everything used below. (CMake 4.x, which Arch ships, refuses projects
# that declare a minimum below 3.5 — so don't lower this much.)
cmake_minimum_required(VERSION 3.20)

project(laner_money
    VERSION 0.1.0
    DESCRIPTION "Self-hosted personal finance platform"
    LANGUAGES C)

# C17 = C11 plus defect fixes; no new features, so nothing exotic.
# EXTENSIONS OFF passes -std=c17 rather than -std=gnu17, so GNU-only
# extensions produce warnings instead of silently working on GCC and then
# breaking on another compiler.
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Writes build/compile_commands.json so clangd / clang-tidy / VS Code know
# the exact flags each file is compiled with.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ---------------------------------------------------------------------------
# Default build type
# ---------------------------------------------------------------------------
# If you run plain `cmake -S . -B build`, CMAKE_BUILD_TYPE is empty, which
# means no optimisation AND none of the Debug-only sanitizers below — the
# worst of both worlds. Default to Debug so the safety nets are on unless
# you explicitly ask for Release.
# (The GENERATOR_IS_MULTI_CONFIG check skips this for IDE generators that
# pick the build type at build time instead.)
get_property(_multi_config GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(NOT _multi_config AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
    message(STATUS "No CMAKE_BUILD_TYPE given — defaulting to Debug")
endif()

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
# FindSQLite3 ships with CMake. It finds sqlite3.h and libsqlite3 and
# creates an "imported target" SQLite::SQLite3 that carries both the
# include path and the library. REQUIRED = stop with a clear error now
# rather than a confusing linker error later.
#   Arch:          pacman -S sqlite        (headers included)
#   Debian/Ubuntu: apt install libsqlite3-dev
find_package(SQLite3 REQUIRED)

# ---------------------------------------------------------------------------
# Shared compiler/linker settings
# ---------------------------------------------------------------------------
# An INTERFACE library compiles nothing; it's a bundle of settings. Any
# target that links laner_build_flags inherits them. When M1 adds a core
# library and a test executable, they link this too and get identical
# warnings + hardening, instead of copy-pasting flag lists.
add_library(laner_build_flags INTERFACE)

target_compile_options(laner_build_flags INTERFACE
    -Wall -Wextra -Wpedantic       # the standard broad warning sets
    -Wshadow                       # inner variable hides an outer one
    -Wconversion -Wsign-conversion # silent narrowing, e.g. int64_t pence -> int,
                                   # or a negative int becoming a huge size_t
    -Wformat=2                     # printf-family misuse, incl. non-literal
                                   # format strings (format-string attacks)
    -Wstrict-prototypes            # `int f()` means "any args" in C; require (void)
    -Wmissing-prototypes           # non-static function without a header decl
    -Wvla                          # variable-length arrays: unbounded stack use
    -fstack-protector-strong       # canary checks on functions with local arrays
)

# Debug: AddressSanitizer (out-of-bounds, use-after-free, leaks) and
# UndefinedBehaviorSanitizer (signed overflow, bad shifts, misaligned
# access...). Slower and bigger binaries, so dev builds only.
# -fno-omit-frame-pointer gives the sanitizers readable stack traces.
target_compile_options(laner_build_flags INTERFACE
    $<$<CONFIG:Debug>:-g3 -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=undefined>
)
target_link_options(laner_build_flags INTERFACE
    $<$<CONFIG:Debug>:-fsanitize=address,undefined>
)

# Release: _FORTIFY_SOURCE makes glibc swap calls like memcpy/snprintf for
# checked versions when the compiler can see the buffer size, aborting on
# overflow instead of corrupting memory. It only works with optimisation
# on, hence non-Debug only. Level 3 (GCC 12+/Clang 9+) covers more cases
# than 2. The -U first avoids a "redefined" warning on distros (Ubuntu)
# whose GCC already defines it by default.
target_compile_options(laner_build_flags INTERFACE
    $<$<NOT:$<CONFIG:Debug>>:-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3>
)

# Full RELRO: after startup the loader marks the GOT (the table of addresses
# for shared-library functions like sqlite3_open_v2) read-only, so a memory
# bug can't be used to overwrite it and hijack a call. -z now resolves
# all of those addresses at startup, which is what makes that possible.
# -z noexecstack: the stack is never executable.
target_link_options(laner_build_flags INTERFACE
    -Wl,-z,relro,-z,now -Wl,-z,noexecstack
)

# ---------------------------------------------------------------------------
# The `laner` executable
# ---------------------------------------------------------------------------
add_executable(laner
    src/main.c
)

# PRIVATE: these apply to building `laner` itself and aren't passed on
# to anything that might link it (nothing does — it's an executable —
# but PRIVATE is the right default and keeps intent explicit).
target_include_directories(laner PRIVATE ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(laner PRIVATE SQLite::SQLite3 laner_build_flags)

# One source of truth for the version: project(VERSION ...) above.
# Becomes `#define LANER_VERSION "0.1.0"` inside the C code.
target_compile_definitions(laner PRIVATE LANER_VERSION="${PROJECT_VERSION}")

# ---------------------------------------------------------------------------
# Core library
# ---------------------------------------------------------------------------
# Application logic lives in a static library rather than directly in the
# `laner` executable, so the tests link the exact same compiled code that
# ships. include/ is PUBLIC: anything linking laner_core can #include
# "money.h" without repeating the path.
add_library(laner_core STATIC
    src/core/money.c
)
target_include_directories(laner_core PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(laner_core PRIVATE laner_build_flags)

# ---------------------------------------------------------------------------
# Tests — run with: ctest --test-dir build --output-on-failure
# ---------------------------------------------------------------------------
# enable_testing() must be in the top-level CMakeLists.txt so CTest finds
# the tests from the build directory root. Each test is a plain executable;
# exit code 0 = pass, anything else = fail. Linking laner_build_flags means
# tests run under ASan/UBSan in Debug, catching memory bugs as well as
# wrong answers.
enable_testing()

add_executable(test_money tests/test_money.c)
target_link_libraries(test_money PRIVATE laner_core laner_build_flags)
add_test(NAME money COMMAND test_money)
