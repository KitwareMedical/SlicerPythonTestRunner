cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerPythonTestRunner)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/KitwareMedical/SlicerPythonTestRunner")
set(EXTENSION_CATEGORY "Developer Tools")
set(EXTENSION_CONTRIBUTORS "Thibault Pelletier (Kitware SAS)")
set(EXTENSION_DESCRIPTION "This extension allows to run Slicer's Python tests directly from Slicer by leveraging PyTest and PyTest-json-report librairies. The tests are executed in a new Slicer process to avoid outdated package import problems.")
set(EXTENSION_ICONURL "https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/SlicerPythonTestRunner.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/0.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SlicerPythonTestRunner)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
