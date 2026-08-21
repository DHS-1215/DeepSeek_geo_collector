import argparse
import asyncio

from app.core.enums import GeoMode
from app.core.models import GeoTask
from app.deepseek.runner import (
    run_deepseek_task,
)


def parse_args():
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


async def main():
    args = parse_args()

    mode = (
        GeoMode.QUICK
        if args.mode == "quick"
        else GeoMode.EXPERT
    )

    task = GeoTask(
        task_id="smoke_001",
        question_id="Q001",
        question=args.question,
        mode=mode,
    )

    result = await run_deepseek_task(
        task,
        batch_id="smoke_batch",
    )

    print("=" * 80)
    print("RUN RESULT")
    print("=" * 80)

    print(
        "STATUS:",
        result.status.value,
    )

    print(
        "RUN ID:",
        result.run_id,
    )

    print()

    print("ANSWER:")
    print(
        result.answer_text_clean
    )

    print()

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


if __name__ == "__main__":
    asyncio.run(main())
