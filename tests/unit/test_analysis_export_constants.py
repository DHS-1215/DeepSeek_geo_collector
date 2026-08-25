from app.analysis.export_constants import (
    ANALYSIS_FILE_PREFIX,
    ANALYSIS_SCHEMA_VERSION,
    DEFAULT_ANALYSIS_PLATFORM_CODE,
)


def test_analysis_schema_version() -> None:
    assert (
        ANALYSIS_SCHEMA_VERSION
        == "geo_analysis_v1"
    )


def test_analysis_export_defaults() -> None:
    assert (
        ANALYSIS_FILE_PREFIX
        == "geo_analysis"
    )

    assert (
        DEFAULT_ANALYSIS_PLATFORM_CODE
        == "deepseek"
    )
