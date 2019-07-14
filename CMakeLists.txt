cmake_minimum_required(VERSION 3.1)

project(gweek-binding VERSION 0.1
    DESCRIPTION "OpenGL Binding Generator"
    LANGUAGES C)

find_package(Python3 REQUIRED Interpreter)

set(gweek_binding_include ${CMAKE_CURRENT_SOURCE_DIR}/include/public)

add_library(gweek-binding STATIC    
    ${CMAKE_CURRENT_SOURCE_DIR}/include/platform.h
	${gweek_binding_include}/gweekgl/opengl.h
	${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c
)

set_source_files_properties(${gweek_binding_include}/gweekgl/opengl.h PROPERTIES GENERATED TRUE)
set_source_files_properties(${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c PROPERTIES GENERATED TRUE)

# Copy OpenGL headers from registry
add_custom_command(TARGET gweek-binding PRE_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/extern/OpenGL-Registry/api/GL/
    ${gweek_binding_include}/GL/
)

add_custom_command(TARGET gweek-binding PRE_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/extern/EGL-Registry/api/KHR/
    ${gweek_binding_include}/KHR/
)  

# Generate OpenGL bindings.
add_custom_command(TARGET gweek-binding PRE_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/script/generate_binding.py --xmlDir "${CMAKE_CURRENT_SOURCE_DIR}/extern/OpenGL-Registry/xml/" --xmlName "gl.xml" --srcFile "${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c" --hdrFile "${gweek_binding_include}/gweekgl/opengl.h" --extensionDir "${CMAKE_CURRENT_SOURCE_DIR}/extern/OpenGL-Registry/extensions/"
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/script/generate_binding.py
    OUTPUTS ${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c
    COMMENT "Generating code for core OpenGL bindings"
)

target_include_directories(gweek-binding PUBLIC ${gweek_binding_include})
target_include_directories(gweek-binding PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if (WIN32)
    target_link_libraries(gweek-binding PRIVATE Opengl32.lib)
elseif(UNIX)
	target_link_libraries(gweek-binding PRIVATE libGL.so)
endif()