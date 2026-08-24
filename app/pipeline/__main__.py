import argparse
import asyncio
from pathlib import Path

from app.batch.reporter import (
    build_batch_summary,
)
from app.package.verifier import (
    PackageVerificationError,
)
from app.pipeline.models import (
    PipelineStatus,
)
from app.pipeline.runner import (
    run_collection_pipeline,
)


def parse_args(
        argv: list[str] | None = None,
) -> argparse.Namespace:
    """
    解析 DeepSeek GEO Pipeline 命令行参数。
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run the DeepSeek GEO collection pipeline."
        )
    )

    parser.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Batch CSV file path.",
    )

    parser.add_argument(
        "--batch-id",
        required=True,
        help="Batch identifier.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "output/package"
        ),
        help="Package output directory.",
    )

    parser.add_argument(
        "--product-id",
        required=True,
        help="Product identifier.",
    )

    parser.add_argument(
        "--product-name",
        required=True,
        help="Product name.",
    )

    return parser.parse_args(
        argv
    )


async def run_cli(
        args: argparse.Namespace,
) -> int:
    """
    执行 Pipeline CLI 主流程。
    """

    result = await run_collection_pipeline(
        csv_path=args.csv,
        batch_id=args.batch_id,
        output_dir=args.output_dir,
        product_id=args.product_id,
        product_name=args.product_name,
    )

    summary = build_batch_summary(
        result.batch_result
    )

    print("=" * 80)
    print("DEEPSEEK GEO PIPELINE")
    print("=" * 80)

    print(
        "PIPELINE STATUS:",
        result.status.value,
    )

    print(
        "BATCH ID:",
        summary.batch_id,
    )

    print(
        "TOTAL:",
        summary.total_count,
    )

    print(
        "SUCCESS:",
        summary.success_count,
    )

    print(
        "FAILED:",
        summary.failed_count,
    )

    print(
        "SUCCESS RATE:",
        f"{summary.success_rate:.2%}",
    )

    print(
        "PACKAGE:",
        result.package_path,
    )

    print(
        "PACKAGE VERIFY:",
        (
            "PASS"
            if result.package_verified
            else "FAILED"
        ),
    )

    if (
            result.status
            == PipelineStatus.PASS
    ):
        return 0

    return 1


def main(
        argv: list[str] | None = None,
) -> int:
    """
    DeepSeek GEO Pipeline CLI 入口。
    """

    args = parse_args(
        argv
    )

    try:
        return asyncio.run(
            run_cli(args)
        )

    except PackageVerificationError as exc:
        print(
            "PACKAGE VERIFICATION FAILED:",
            exc,
        )

        return 3

    except (
            FileNotFoundError,
            ValueError,
    ) as exc:
        print(
            "INPUT ERROR:",
            exc,
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
