# gweek-binding
This project uses pure Python 3 to generate a C OpenGL binding from OpenGL's official XML spec files, and exposes a static library which can be used to easily include extended OpenGL support in any CMake project.

It was intended to be easily included and built from a git submodule, in other CMake projects.

# Prerequisites
- Python 3
- CMake

# Platforms I've Used
- Linux (at least Debian, Buster)
- Windows

# Using the Bindings
The build uses CMake to define a new build target "`gweek-binding`", as well as a variable "`${gweek_binding_include}`", allowing easy integration into an existing CMakeLists.txt using:

```cmake
add_subdirectory(extern/gweek-binding)

target_include_directories(myproject PRIVATE ${gweek_binding_include})
target_link_libraries(myproject PRIVATE gweek-binding)
```

After which, the bound OpenGL functions can be accessed by including the appropriate headers, and calling the functions.:

```c
#include <gweekgl/opengl.h>

GLint get_major_opengl_version()
{
    // Initialize a rendering context (e.g. ::glfwMakeContextCurrent(window)), then call:

    gweekgl_initialize();
    
    GLint version;
    ::glGetIntegerv(GL_MAJOR_VERSION, &version);

    return version;
}
```

As this repository contains submodules from other repositories, don't forget to also clone these using `git submodule update --init --recursive`

