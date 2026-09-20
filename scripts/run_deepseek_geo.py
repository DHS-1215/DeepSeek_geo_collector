from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output" / "package"

PRODUCTS = {
    "1": {
        "product_id": "hongmao_yaojiu",
        "product_name": "鸿茅药酒",
        "csv_path": INPUT_DIR / "hongmao_questions.csv",
    },
    "2": {
        "product_id": "tianyishou_qixueguben",
        "product_name": "天益寿气血固本",
        "csv_path": INPUT_DIR / "tianyishou_questions.csv",
    },
}

CHECKPOINT_ROOT = PROJECT_ROOT / "output" / "checkpoints"


def find_latest_incomplete_batch(
        product_id: str,
) -> dict | None:
    """
    查找指定产品最近一个未完成的 checkpoint。

    RUNNING:
        上次可能异常退出。

    INCOMPLETE:
        上次存在失败任务，可继续补采。

    COMPLETED:
        忽略。
    """

    if not CHECKPOINT_ROOT.is_dir():
        return None

    candidates = []

    for directory in CHECKPOINT_ROOT.iterdir():
        if not directory.is_dir():
            continue

        if not directory.name.startswith(
                f"{product_id}_"
        ):
            continue

        checkpoint_path = (
                directory
                / "checkpoint.json"
        )

        if not checkpoint_path.is_file():
            continue

        try:
            import json

            payload = json.loads(
                checkpoint_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            continue

        status = str(
            payload.get(
                "status",
                "",
            )
        ).upper()

        if status == "COMPLETED":
            continue

        candidates.append(
            {
                "batch_id": str(
                    payload.get(
                        "batch_id",
                        directory.name,
                    )
                ),
                "status": status,
                "total_count": int(
                    payload.get(
                        "total_count",
                        0,
                    )
                ),
                "successful_count": int(
                    payload.get(
                        "successful_count",
                        0,
                    )
                ),
                "updated_at": str(
                    payload.get(
                        "updated_at",
                        "",
                    )
                ),
                "path": checkpoint_path,
            }
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["updated_at"],
            item["batch_id"],
        ),
        reverse=True,
    )

    return candidates[0]


def choose_batch_id(
        product_id: str,
) -> str:
    """
    优先提示用户是否恢复最近的未完成 Batch。
    """

    incomplete = find_latest_incomplete_batch(
        product_id
    )

    if incomplete is not None:
        print()
        print("=" * 60)
        print("检测到未完成采集")
        print("=" * 60)
        print()
        print(
            f"[BATCH]   "
            f"{incomplete['batch_id']}"
        )
        print(
            f"[STATUS]  "
            f"{incomplete['status']}"
        )
        print(
            f"[DONE]    "
            f"{incomplete['successful_count']}"
            f" / {incomplete['total_count']}"
        )
        print(
            f"[UPDATED] "
            f"{incomplete['updated_at']}"
        )
        print()
        print("R. 继续上次采集")
        print("N. 开始新批次")
        print("Q. 取消")
        print()

        while True:
            choice = input(
                "请输入选项 [R/N/Q]: "
            ).strip().lower()

            if choice == "r":
                print()
                print(
                    "[RESUME] 继续批次："
                    f"{incomplete['batch_id']}"
                )
                return str(
                    incomplete["batch_id"]
                )

            if choice == "n":
                break

            if choice == "q":
                raise KeyboardInterrupt

            print()
            print(
                "[ERROR] "
                "请输入 R、N 或 Q。"
            )
            print()

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        f"{product_id}_{timestamp}"
    )


def choose_product() -> dict:
    print("=" * 60)
    print("DeepSeek GEO Collection Pipeline")
    print("=" * 60)
    print()
    print("请选择采集产品：")
    print()
    print("1. 鸿茅药酒")
    print("2. 天益寿气血固本")
    print()
    print("Q. 退出")
    print()

    while True:
        choice = input("请输入选项 [1/2/Q]: ").strip().lower()

        if choice == "q":
            raise KeyboardInterrupt

        product = PRODUCTS.get(choice)

        if product is not None:
            return product

        print()
        print("[ERROR] 无效选项，请输入 1、2 或 Q。")
        print()


def run_pipeline(product: dict) -> int:
    product_id = str(product["product_id"])
    product_name = str(product["product_name"])
    csv_path = Path(product["csv_path"])

    if not csv_path.exists():
        print()
        print("[ERROR] 找不到该产品的问题 CSV：")
        print(csv_path)
        print()
        return 1

    batch_id = choose_batch_id(
        product_id
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 60)
    print("任务信息")
    print("=" * 60)
    print()
    print(f"[PRODUCT]  {product_name}")
    print(f"[ID]       {product_id}")
    print(f"[CSV]      {csv_path}")
    print(f"[BATCH]    {batch_id}")
    print(f"[OUTPUT]   {OUTPUT_DIR}")
    print()

    command = [
        sys.executable,
        "-m",
        "app.pipeline",
        "--csv",
        str(csv_path),
        "--batch-id",
        batch_id,
        "--output-dir",
        str(OUTPUT_DIR),
        "--product-id",
        product_id,
        "--product-name",
        product_name,
    ]

    print("=" * 60)
    print("Pipeline Starting")
    print("=" * 60)
    print()

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        print()
        print(
            "[ERROR] Pipeline exited with "
            f"code {result.returncode}"
        )
        return result.returncode

    package_path = (
            OUTPUT_DIR
            / (
                "geo_package_deepseek_"
                f"{batch_id}.zip"
            )
    )

    print()
    print("=" * 60)

    if not package_path.exists():
        print(
            "[ERROR] Pipeline finished "
            "but GEO ZIP was not found:"
        )
        print(package_path)
        return 1

    print("[SUCCESS] GEO package generated")
    print()
    print(f"产品：{product_name}")
    print(f"批次：{batch_id}")
    print()
    print("GEO Package:")
    print(package_path)
    print()
    print(
        "该 ZIP 可直接上传到 "
        "GEO Analysis System。"
    )
    print("=" * 60)

    return 0


def main() -> int:
    try:
        product = choose_product()
        return run_pipeline(product)

    except KeyboardInterrupt:
        print()
        print("\u5df2\u53d6\u6d88\u8fd0\u884c\u3002")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
