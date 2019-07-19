#pragma once

#if defined(_WIN32)
#define GWEEK_PLATFORM_WINDOWS
#if defined(_WIN64)
#define GWEEK_PLATFORM_X64
#elif !defined(_WIN64)
#define GWEEK_PLATFORM_X86
#endif
#elif defined(__linux__)
#define GWEEK_PLATFORM_LINUX
#else
#error Unsupported Platform
#endif

// #################################
// Definitions for Windows Platform
// #################################
#if defined(GWEEK_PLATFORM_WINDOWS)
#if !defined(WIN32_LEAN_AND_MEAN)
#define WIN32_LEAN_AND_MEAN
#define GWEEK_WIN32_LEAN_AND_MEAN
#endif

#if !defined(NOMINMAX)
#define NOMINMAX
#define GWEEK_NOMINMAX
#endif

#include <Windows.h>
#include <gl/GL.h>
#include <GL/glext.h>

#if defined(GWEEK_WIN32_LEAN_AND_MEAN)
#undef GWEEK_WIN32_LEAN_AND_MEAN
#undef WIN32_LEAN_AND_MEAN
#endif

#if defined(GWEEK_NOMINMAX)
#undef GWEEK_NOMINMAX
#undef NOMINMAX
#endif

#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_0 1
#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_1 1

#define GWEEK_PROC_ADDR_FUNC	(wglGetProcAddress)
#endif

// #################################
// Definitions for Linux Platform
// #################################
#if defined(GWEEK_PLATFORM_LINUX)
#include <GL/gl.h>
#include <GL/glx.h>
#include <GL/glext.h>

#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_0 1
#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_1 1
#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_2 1
#define GWEEK_SYSTEM_DEFINES_GL_VERSION_1_3 1
#define GWEEK_SYSTEM_DEFINES_GL_ARB_imaging 1

#define GWEEK_PROC_ADDR_FUNC    (glXGetProcAddress)
#endif