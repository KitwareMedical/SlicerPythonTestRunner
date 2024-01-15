#-----------------------------------------------------------------------------
set(MODULE_NAME SlicerPythonTestRunner)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  SlicerPythonTestRunnerLib/__init__.py
  SlicerPythonTestRunnerLib/Case.py
  SlicerPythonTestRunnerLib/Decoractor.py
  SlicerPythonTestRunnerLib/EnsureRequirements.py
  SlicerPythonTestRunnerLib/IconPath.py
  SlicerPythonTestRunnerLib/LoadingWidget.py
  SlicerPythonTestRunnerLib/QWidget.py
  SlicerPythonTestRunnerLib/Results.py
  SlicerPythonTestRunnerLib/RunnerLogic.py
  SlicerPythonTestRunnerLib/RunnerWidget.py
  SlicerPythonTestRunnerLib/Settings.py
  SlicerPythonTestRunnerLib/SettingsDialog.py
  SlicerPythonTestRunnerLib/Signal.py
  SlicerPythonTestRunnerLib/TreeProxyModel.py
  SlicerPythonTestRunnerLib/TreeView.py
  Testing/a_test_results_file.json
  Testing/conftest.py
  Testing/test_runner_logic.py
  Testing/test_runner_widget.py
  Testing/test_tree_view.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/show_ignored_icon.png
  Resources/Icons/show_passed_icon.png
  Resources/Icons/SlicerPythonTestRunner.png
  Resources/Icons/test_collect_icon.png
  Resources/Icons/test_failed_icon.png
  Resources/Icons/test_loading.gif
  Resources/Icons/test_ok_icon.png
  Resources/Icons/test_skipped_icon.png
  Resources/Icons/test_start_icon.png
  Resources/Icons/test_stop_icon.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)
endif()
