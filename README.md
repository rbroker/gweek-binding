# gweek_binding
C++ OpenGL Binding Generator

# Prerequisites
- Python 3

# Using the Bindings
gweek-binding is built using CMAKE. It defines a static library target "`gweek-binding`", as well as a variable "`${gweek-binding-include}`" which defines the available OpenGL functions & macros. It can be included in an existing CMakeLists.txt using:

`add_subdirectory(extern/gweek-binding)`

After which, the generated binding header can be included using:

```c++
#include <gweekgl/gl.h>
```


