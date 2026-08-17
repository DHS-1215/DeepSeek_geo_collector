PACKAGE_SCHEMA_VERSION = "geo_package_v1"
GEO_BATCH_VERSION = "geo_batch_v1"

GENERATOR_VERSION = "0.1.0"

DEFAULT_PLATFORM_CODE = "deepseek"
DEFAULT_PLATFORM_NAME = "DeepSeek"

DEFAULT_SOURCE_SYSTEM = "deepseek_geo_collector"
DEFAULT_SOURCE_EXPORT_TYPE = "dom_collection"

REQUIRED_PACKAGE_FILES = (
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
    "checksums.json",
)

CHECKSUM_DATA_FILES = (
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
)
