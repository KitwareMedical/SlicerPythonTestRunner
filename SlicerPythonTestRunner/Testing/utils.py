from pathlib import Path


def a_reporting_failing_test_content():
    return (
        "import logging\n"
        "import sys\n"
        "def test_failing():\n"
        "  print('STD OUT')\n"
        "  print('STD ERR', file=sys.stderr)\n"
        "  logging.exception('LOGGING EXCEPTION')\n"
        "  logging.debug('LOGGING DEBUG')\n"
        "  logging.warn('LOGGING WARN')\n"
        "  assert False\n"
    )


def a_success_test_content():
    return "def test_success():\n" "  assert True\n"


def a_slicer_test_content():
    return (
        "def test_slicer():\n"
        "  import slicer\n"
        "  node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')\n"
        "  assert node\n"
    )


def a_failing_test_content():
    return "def test_failing():\n" "  assert False\n"


def a_succeeding_test_file_with_two_tests_content():
    return "def test_success_1():\n" "  pass\n" "def test_success_2():\n" "  pass\n"


def a_test_file_with_passing_failing_tests_content():
    return "def test_pass():\n" "  pass\n" "def test_fail():\n" "  assert False\n"


def a_unittest_case_content():
    return (
        "import unittest\n"
        "class MyTestCase(unittest.TestCase):\n"
        "  def test_success(self):\n"
        "    self.assertTrue(True)\n"
        "  def test_failing(self):\n"
        "    self.assertTrue(False)\n"
    )


def a_file_with_one_passed_one_failed_one_skipped_content():
    return (
        "import pytest\n"
        "def test_passed():\n"
        "  pass\n"
        "def test_failed():\n"
        "  assert False\n"
        "@pytest.mark.skip(reason='No testing here')\n"
        "def test_skipped():\n"
        "  pass\n"
    )


def write_file(tmpdir, file_path, file_content):
    file_path = Path(tmpdir).joinpath(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(file_content)
    return file_path
