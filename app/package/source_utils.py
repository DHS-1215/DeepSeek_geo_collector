import hashlib
import html
from collections import Counter
from typing import Any
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from urllib.parse import (
    urlsplit,
    urlunsplit,
)

TRACKING_PREFIXES = ("utm_",)

TRACKING_KEYS = {
    "from",
    "source",
    "spm",
    "scene",
    "share_token",
}


def normalize_url(
        url: str | None,
) -> str | None:
    if not url:
        return None

    parts = urlsplit(url)

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            "",
            "",
        )
    )


def normalize_raw_url(url: Any) -> str:
    """对原始 URL 做最小规范化，但保留业务 query 参数。"""

    text = html.unescape(str(url or "")).strip()

    if not text:
        return ""

    parts = urlsplit(text)

    if not parts.scheme or not parts.netloc:
        return text.rstrip("/")

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            parts.query,
            "",
        )
    )


def canonicalize_url(url: str | None) -> str:
    """生成用于 source 去重判断的 canonical URL。"""

    if not url:
        return ""

    text = normalize_raw_url(url)

    if not text:
        return ""

    parts = urlsplit(text)

    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"

    query_items: list[tuple[str, str]] = []

    for key, value in parse_qsl(
            parts.query,
            keep_blank_values=True,
    ):
        low_key = key.lower()

        if (
                low_key in TRACKING_KEYS
                or any(
            low_key.startswith(prefix)
            for prefix in TRACKING_PREFIXES
        )
        ):
            continue

        query_items.append((key, value))

    query = urlencode(sorted(query_items))

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            "",
        )
    )


def finalize_source_rows(
        batch_id: str,
        rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """按照 geo_package_v1 规则完成 source 去重和 occurrence_id 生成。"""

    kept: list[dict[str, Any]] = []

    seen_exact: set[tuple[str, int, str]] = set()
    seen_normalized: set[tuple[str, int, str]] = set()

    order_to_url: dict[tuple[str, int], str] = {}

    duplicate_urls_by_answer: Counter[tuple[str, str]] = Counter()

    exact_duplicate_rows_removed = 0

    removed_duplicate_rows: list[dict[str, Any]] = []
    source_order_conflicts: list[dict[str, Any]] = []

    for line_no, source in enumerate(rows, start=1):
        answer_id = str(
            source.get("answer_id") or ""
        )

        source_order = int(
            source.get("source_order") or 0
        )

        raw_url = normalize_raw_url(
            source.get("source_url_raw")
        )

        normalized_url = canonicalize_url(raw_url)

        order_key = (
            answer_id,
            source_order,
        )

        exact_key = (
            answer_id,
            source_order,
            raw_url,
        )

        normalized_key = (
            answer_id,
            source_order,
            normalized_url,
        )

        previous_order_url = order_to_url.get(
            order_key
        )

        if (
                previous_order_url is not None
                and previous_order_url != normalized_url
        ):
            source_order_conflicts.append(
                {
                    "line_no": line_no,
                    "answer_id": answer_id,
                    "source_order": source_order,
                    "previous_normalized_url": previous_order_url,
                    "current_normalized_url": normalized_url,
                    "current_url": raw_url,
                    "title": source.get(
                        "source_title_raw"
                    ),
                }
            )
            continue

        order_to_url[order_key] = normalized_url

        if (
                exact_key in seen_exact
                or normalized_key in seen_normalized
        ):
            exact_duplicate_rows_removed += 1

            removed_duplicate_rows.append(
                {
                    "line_no": line_no,
                    "answer_id": answer_id,
                    "source_order": source_order,
                    "source_url_raw": raw_url,
                    "normalized_source_url_raw": (
                        normalized_url
                    ),
                    "source_title_raw": source.get(
                        "source_title_raw"
                    ),
                    "old_occurrence_id": source.get(
                        "occurrence_id"
                    ),
                    "task_id": source.get(
                        "task_id"
                    ),
                    "question_id": source.get(
                        "question_id"
                    ),
                    "mode_code": source.get(
                        "mode_code"
                    ),
                }
            )
            continue

        finalized = dict(source)

        finalized["source_url_raw"] = raw_url
        finalized["normalized_source_url_raw"] = (
            normalized_url
        )

        finalized.pop(
            "occurrence_id",
            None,
        )

        seen_exact.add(exact_key)
        seen_normalized.add(normalized_key)

        duplicate_urls_by_answer[
            (
                answer_id,
                normalized_url,
            )
        ] += 1

        kept.append(finalized)

    if source_order_conflicts:
        preview = source_order_conflicts[:5]

        raise RuntimeError(
            "source_order_conflict: "
            f"{preview!r}"
        )

    for sequence, source in enumerate(
            kept,
            start=1,
    ):
        identity = "\n".join(
            [
                batch_id,
                str(
                    source.get("answer_id")
                    or ""
                ),
                str(
                    source.get("source_order")
                    or ""
                ),
                str(
                    source.get("source_url_raw")
                    or ""
                ),
            ]
        )

        digest = hashlib.sha1(
            identity.encode("utf-8")
        ).hexdigest()[:12]

        source["occurrence_id"] = (
            f"{batch_id}_"
            f"{sequence:04d}_"
            f"{digest}"
        )

    diagnostics = {
        "source_authoritative_file": "sources.json",
        "source_csv_used": False,
        "source_rows_before_dedup": len(rows),
        "exact_duplicate_rows_removed": (
            exact_duplicate_rows_removed
        ),
        "source_rows_after_dedup": len(kept),
        "duplicate_url_in_answer_count": sum(
            count - 1
            for count
            in duplicate_urls_by_answer.values()
            if count > 1
        ),
        "unique_constraint_conflict_count": 0,
        "removed_duplicate_rows": removed_duplicate_rows,
        "source_order_conflicts": source_order_conflicts,
        "occurrence_id_generation": (
            "batch_id + final_sequence + "
            "sha1(batch_id, answer_id, "
            "source_order, source_url_raw)[0:12]"
        ),
    }

    return kept, diagnostics
