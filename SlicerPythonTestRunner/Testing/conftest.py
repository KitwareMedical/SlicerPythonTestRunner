import pytest
from pathlib import Path


@pytest.fixture()
def a_json_test_result_file():
    return Path(__file__).parent.joinpath("a_test_results_file.json")


@pytest.fixture(autouse=True)
def default_module_settings():
    import qt

    try:
        settings = qt.QSettings()
        savedSettings = {}

        for k in settings.allKeys():
            if "SlicerPythonTestRunner/" in k:
                savedSettings[k] = settings.value(k)
                settings.remove(k)

        yield

        for k, v in savedSettings.items():
            settings.setValue(k, v)

    except AttributeError:
        yield
