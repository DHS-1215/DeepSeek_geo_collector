import argparse
import asyncio
from pathlib import Path

from app.analysis.export_serialization import (
    build_analysis_document,
)
from app.analysis.exporter import (
    export_analysis_json,
)
from app.analysis.replay import (
    replay_analysis,
)
from app.analysis.sentiment_config import (
    load_sentiment_config,
)
from app.analysis.sentiment_providers import (
    create_sentiment_provider,
)
from app.analysis.verifier import (
    verify_analysis_file,
)


def parse_args(
        args: list[str] | None = None,
):
    parser = argparse.ArgumentParser(
        description="DeepSeek GEO Analysis Replay"
    )

    parser.add_argument(
        "--package",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--product-id",
        required=True,
    )

    parser.add_argument(
        "--product-name",
        required=True,
    )

    parser.add_argument(
        "--batch-id",
        default=None,
    )

    return parser.parse_args(args)


async def run_analysis_cli(
        args,
) -> Path:

    config = load_sentiment_config()

    provider = create_sentiment_provider(
        config
    )

    analysis_result = await replay_analysis(
        package_path=args.package,
        product_id=args.product_id,
        product_name=args.product_name,
        sentiment_provider=provider,
        sentiment_config=config,
    )

    from app.package.reader import (
        read_geo_package,
    )

    package = read_geo_package(
        args.package
    )

    results = (
        __import__(
            "app.analysis.replay",
            fromlist=[
                "build_replay_results"
            ],
        )
        .build_replay_results(
            package
        )
    )

    document = build_analysis_document(
        batch_id=(
            args.batch_id
            or package.manifest.batch_id
        ),
        product_id=args.product_id,
        product_name=args.product_name,
        analysis=analysis_result,
        results=results,
    )

    output_path = (
        args.output_dir
        /
        "geo_analysis.json"
    )

    export_analysis_json(
        document=document,
        output_path=output_path,
    )

    verify_result = verify_analysis_file(
        output_path
    )

    if not verify_result.passed:
        raise RuntimeError(
            "analysis verify failed: "
            f"{verify_result.errors}"
        )

    return output_path


def main(
        args: list[str] | None = None,
) -> int:

    parsed = parse_args(
        args
    )

    output = asyncio.run(
        run_analysis_cli(
            parsed
        )
    )

    print(
        "ANALYSIS PASS"
    )

    print(
        f"OUTPUT: {output}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )