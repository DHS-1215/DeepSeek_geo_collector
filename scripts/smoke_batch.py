import argparse
import asyncio
from pathlib import Path

from app.batch.export import (
    export_batch_package,
)
from app.batch.loader import (
    load_batch_tasks,
)
from app.batch.runner import (
    run_batch,
)
from app.core.enums import TaskStatus
from app.package.verifier import (
    verify_geo_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a real DeepSeek batch smoke test "
            "and export geo_package_v1."
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
        default=Path("output/package"),
        help="Package output directory.",
    )

    parser.add_argument(
        "--product-id",
        default="hongmao_yaojiu",
        help="Product identifier.",
    )

    parser.add_argument(
        "--product-name",
        default="鸿茅药酒",
        help="Product name.",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    print("=" * 80)
    print("LOAD BATCH")
    print("=" * 80)

    tasks = load_batch_tasks(
        csv_path=args.csv,
        batch_id=args.batch_id,
    )

    print(
        "CSV:",
        args.csv,
    )

    print(
        "BATCH ID:",
        args.batch_id,
    )

    print(
        "TASK COUNT:",
        len(tasks),
    )

    if not tasks:
        raise RuntimeError(
            "Batch CSV contains no tasks."
        )

    for task in tasks:
        print(
            "TASK:",
            task.task_id,
            "|",
            task.mode.value,
            "|",
            task.question,
        )

    print()
    print("=" * 80)
    print("RUN BATCH")
    print("=" * 80)

    batch_result = await run_batch(
        tasks
    )

    print(
        "BATCH STATUS:",
        batch_result.status.value,
    )

    print(
        "TOTAL:",
        batch_result.total_count,
    )

    print(
        "SUCCESS:",
        batch_result.success_count,
    )

    print(
        "FAILED:",
        batch_result.failed_count,
    )

    print()

    for result in batch_result.results:
        print("-" * 80)

        print(
            "TASK ID:",
            result.task.task_id,
        )

        print(
            "QUESTION ID:",
            result.task.question_id,
        )

        print(
            "MODE:",
            result.task.mode.value,
        )

        print(
            "STATUS:",
            result.status.value,
        )

        print(
            "ANSWER LENGTH:",
            len(
                result.answer_text_clean
            ),
        )

        print(
            "SOURCE STATUS:",
            result.sources.status.value,
        )

        print(
            "SOURCE COUNT:",
            len(
                result.sources.sources
            ),
        )

        if result.failure is not None:
            print(
                "FAILURE TYPE:",
                result.failure.type.value,
            )

            print(
                "FAILURE MESSAGE:",
                result.failure.message,
            )

            print(
                "RETRYABLE:",
                result.failure.retryable,
            )

    print()
    print("=" * 80)
    print("EXPORT PACKAGE")
    print("=" * 80)

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    package_path = export_batch_package(
        result=batch_result,
        output_dir=args.output_dir,
        product_id=args.product_id,
        product_name=args.product_name,
    )

    print(
        "PACKAGE:",
        package_path,
    )

    print()
    print("=" * 80)
    print("VERIFY PACKAGE")
    print("=" * 80)

    verify_geo_package(
        package_path
    )

    print(
        "PACKAGE VERIFY: PASS"
    )

    print()
    print("=" * 80)
    print("SMOKE SUMMARY")
    print("=" * 80)

    all_success = all(
        result.status
        == TaskStatus.SUCCESS
        for result in batch_result.results
    )

    if all_success:
        print(
            "SMOKE RESULT: PASS"
        )
    else:
        print(
            "SMOKE RESULT: PASS_WITH_TASK_FAILURES"
        )

        raise RuntimeError(
            "Package verification passed, "
            "but one or more collection tasks failed."
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
