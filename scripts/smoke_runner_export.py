import argparse
import asyncio
from pathlib import Path

from app.core.enums import GeoMode
from app.core.models import GeoTask
from app.deepseek.runner import (
    run_deepseek_task,
)
from app.package.exporter import (
    export_geo_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--question",
        required=True,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "quick",
            "expert",
        ],
        default="quick",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    mode = (
        GeoMode.QUICK
        if args.mode == "quick"
        else GeoMode.EXPERT
    )

    task = GeoTask(
        task_id="smoke_export_001",
        question_id="Q001",
        question=args.question,
        mode=mode,
    )

    result = await run_deepseek_task(
        task,
        batch_id="smoke_export_batch",
    )

    print("=" * 80)
    print("RUN RESULT")
    print("=" * 80)

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
        "SOURCE COUNT:",
        len(
            result.sources.sources
        ),
    )

    print(
        "RUNNER SOURCE STATUS:",
        result.sources.status,
    )

    print(
        "RUNNER SOURCE COUNT:",
        len(
            result.sources.sources
        ),
    )

    output_dir = Path(
        "output/package"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )



    package_path = export_geo_package(
        batch_id="smoke_export_batch",
        results=[result],
        output_dir=output_dir,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    print()
    print("=" * 80)
    print("PACKAGE")
    print("=" * 80)

    print(
        package_path
    )


if __name__ == "__main__":
    asyncio.run(main())
