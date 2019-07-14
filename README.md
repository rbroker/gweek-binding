# gweek-binding
This project uses Python to generate a runtime C++ OpenGL binding from the OpenGL official XML spec files, and exposes a static library which can be used to easily include extended OpenGL support in any CMake project.

# Prerequisites
- Python 3

# Using the Bindings
This imports the OpenGL extension header files from the Khronos-maintained OpenGL-Registry, and generates a static library which can be linked with
to bind to the Core OpenGL library functions at runtime.

The build uses CMAKE to define a new build target "`gweek-binding`", as well as a variable "`${gweek-binding-include}`", allowing easy integration into an existing CMakeLists.txt using:

```cmake
add_subdirectory(extern/gweek-binding)

target_include_directories(myproject PRIVATE ${gweek-binding-include})
target_link_libraries(myproject PRIVATE gweek-binding)
```

After which, the bound OpenGL functions can be accessed by including the appropriate headers, and calling the functions.:

```c++
#include <GL/glcorearb.h>
#include <GL/glext.h>
#include <GL/glxext.h>
#include <GL/wgl.h>
#include <GL/wglext.h>

bool is_func_available()
{
    return ::glGenBuffers != nullptr;
}
```


