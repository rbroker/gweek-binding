cmake_minimum_required(VERSION 3.11)

project(gweek-binding VERSION 0.1
    DESCRIPTION "OpenGL Binding Generator"
    LANGUAGES C)

find_package(Python3 REQUIRED Interpreter)

set(gweek_binding_include ${CMAKE_CURRENT_SOURCE_DIR}/include/public)

set_source_files_properties(${gweek_binding_include}/gweekgl/opengl.h PROPERTIES GENERATED TRUE)
set_source_files_properties(${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c PROPERTIES GENERATED TRUE)

# Copy OpenGL headers from registry
add_custom_command(
    OUTPUT
        ${gweek_binding_include}/GL/glext.h        
    COMMAND 
        ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/extern/OpenGL-Registry/api/GL/ ${gweek_binding_include}/GL/
    COMMENT 
        "Copying Pre-Generated OpenGL Headers from OpenGL-Registry"
)

add_custom_command(
    OUTPUT 
        ${gweek_binding_include}/KHR/khrplatform.h
    COMMAND
        ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/extern/EGL-Registry/api/KHR/ ${gweek_binding_include}/KHR/    
    COMMENT
        "Copying Pre-Generaed OpenGL Headers from EGL-Registry"
)
            
# Generate The OpenGL bindings from the registry files.
add_custom_command(
    OUTPUT
        ${gweek_binding_include}/gweekgl/opengl.h
        ${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c     
    COMMAND
        ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/script/opengl_registry.py --xmlDir "${CMAKE_CURRENT_SOURCE_DIR}/extern/OpenGL-Registry/xml/" --xmlName "gl.xml" --srcFile "${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c" --hdrFile "${gweek_binding_include}/gweekgl/opengl.h"
    COMMENT
        "Generating code for core OpenGL bindings..."
)

add_library(gweek-binding STATIC    
    ${gweek_binding_include}/GL/glext.h
    ${gweek_binding_include}/KHR/khrplatform.h
    ${gweek_binding_include}/gweekgl/platform.h
	${gweek_binding_include}/gweekgl/opengl.h
	${CMAKE_CURRENT_SOURCE_DIR}/src/opengl.c    
)

target_include_directories(gweek-binding PUBLIC ${gweek_binding_include})
target_include_directories(gweek-binding PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if (WIN32)
    target_link_libraries(gweek-binding PRIVATE Opengl32.lib)
elseif(UNIX)
	target_link_libraries(gweek-binding PRIVATE libGL.so)
endif()
