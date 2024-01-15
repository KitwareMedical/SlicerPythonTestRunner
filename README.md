# Slicer Python Test Runner

<img src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/0.png"/>

## Table of contents

* [Introduction](#introduction)
* [Why this extension](#why-this-extension)
* [Using the extension](#using-the-extension)
* [Test decorators](#test-decorators)
* [Changelog](#changelog)
* [Contributing](#contributing)

## Introduction

<div style="text-align:center">
<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/SlicerPythonTestRunner.png"/>
</div>

This module allows running 3D Slicer module's unit tests directly from 3D Slicer's UI.

It uses PyTest and PyTest JSON Report to discover the unit tests in a given directory or file and runs the tests in a 
separate 3D Slicer process.

After the tests have been run, the results are displayed in the UI.
The plugin also provides decorators to help running unit tests directly in your favorite IDEs.

## Why this extension

3D Slicer is a C++ based application and provides numerous libraries which are conveniently wrapped and available in 
its Python environment. 

The Python interpreter is named `python-real` in Slicer's binary folder and can be used directly to run Python libraries
installed in the Python environment such as NumPy and ITK.

Some features, however, are only available when running inside the full 3D Slicer environment, for instance access to 
the application main window or accessing loaded modules.

When testing a 3D Slicer modules, it is hence necessary to run in the full 3D Slicer environment.

3D Slicer provides a `Reload and Test` developer tool which reloads the current module python file and runs its unit
tests. However, this mechanism has the following limitations :
* Due to Python's lack of reloading mechanism for packages, it only works well for single file modules
* The tests run only provides print in Slicer's console 
* The test run doesn't allow for filtering tests to run

3D Slicer also has CTest testing functionalities. However, these functionalities are not readily available for
a developer wishing to develop a Slicer extension using a pre-built application.

By launching a new Slicer process for its tests and using PyTest's filtering mechanism, this extension provides an
efficient way of running UnitTests inside 3D Slicer without the previous caveats.

## Using the extension

This extension can be installed directly using Slicer's extension manager.

Once installed, navigate to `Developer Tools>Slicer Python Test Runner` in the modules drop down menu or search directly
for `Slicer Python Test Runner`.

You will see the following, empty, test runner module:

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/2.png"/>

Start by selecting the directory containing the tests using the top path selector.
Then enter the file filter pattern, test class filter pattern, and test function filter pattern.

*Warning* : Note that by default, the module uses PyTest's conventions which expects test files, classes and functions
to be prefixed by `test`.

If you are testing using 3D Slicer convention, please use the following pattern:
* file : *.py
* class : *TestCase

Click on the `collect` button to check that the tests to run are correctly found by the extension.

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/3.png"/>

Afterwards, click on the `run` button to start testing.

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/4.png"/>

You can cancel test running using the `stop` button. Note however that as the test runner starts new Slicer processes
the cancel may not be graceful and 3D Slicer windows may have to be killed manually.

Once the tests have run, you will see the tests results in the UI.

Clicking on one test in the tree view will display its result in the text editor below, along the error if any.

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/5.png"/>

Additional buttons allow to filter the tests displayed in the UI (passed, ignored, collected).

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/6.png"/>

To modify the execution settings, click on the `settings` button.

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/7.png"/>

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/8.png"/>

The following settings are accessible: 
* Close Slicer after run: Closes the spawned Slicer process when the tests have finished running.
* Use main window: If unchecked, opens the Slicer process without any main window GUI
* Minimize main window: If checked and a main window is used, minimizes the launched window at startup
* Extra slicer args: Comma separated list of args to use when starting Slicer instance (refer to Slicer launcher CLI args for more info)
* Extra pytest args: Comma separated list of args to pass to PyTest (please refer to PyTest args for more info)


## Test decorators

This module also provides the following decorators : 
* runTestInSlicerContext: This decorator will run the current test by using the Module's test runner if executed 
    outside a 3D Slicer application. This allows to run the tests directly in your favorite IDE's test runner.
* skipTestOutsideSlicer: This decorator will skip the current test if executed outside a 3D Slicer application.

<img class="center" src="https://github.com/KitwareMedical/SlicerPythonTestRunner/raw/main/Screenshots/9.png"/>

## Changelog


## Contributing

This project welcomes contributions. If you want more information about how you can contribute, please refer to
the [CONTRIBUTING.md file](CONTRIBUTING.md).
