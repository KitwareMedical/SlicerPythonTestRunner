import traceback
from functools import wraps, partial
from pathlib import Path
from typing import List, Set


def get_all_cov_formats():
    return ["json", "xml", "lcov", "html"]


def get_coverage_formats_from_list(reportFormats: List[str]) -> Set[str]:
    return {
        v for v in get_all_cov_formats() if v in reportFormats
    }


def get_coverage_formats_from_conf(cov: "Coverage") -> Set[str]:
    config = cov.config.config_file
    if not config or not Path(config).is_file():
        return set()

    try:
        with open(config, "r") as f:
            content = f.read()

            return {
                v for v in get_all_cov_formats() if f"{v}]" in content
            }
    except OSError:
        return set()


def get_coverage_formats(cov: "Coverage", reportFormats: List[str]) -> List[str]:
    report_formats = get_coverage_formats_from_list(reportFormats)
    config_formats = get_coverage_formats_from_conf(cov)
    return list(report_formats.union(config_formats))


def _coverage(runSettings):
    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            from coverage import Coverage
            if not runSettings.doRunCoverage:
                return f(*args, **kwargs)

            try:
                cov = Coverage(source=runSettings.coverageSources)
                cov.start()
                ret = f(*args, **kwargs)
                cov.stop()
                cov.save()

                formats = get_coverage_formats(cov, runSettings.coverageReportFormats)
                reportDict = {
                    "json": partial(cov.json_report, outfile=runSettings.coverageFilePath),
                    "xml": partial(cov.xml_report, outfile=runSettings.coverageFilePath),
                    "lcov": partial(cov.lcov_report, outfile=runSettings.coverageFilePath),
                    "html": partial(cov.html_report, directory=runSettings.coverageFilePath),
                }

                for cov_format in formats:
                    reportDict[cov_format]()

                return ret
            except Exception:  # noqa
                traceback.print_exc()
                return 1

        return decorator

    return wrapper
