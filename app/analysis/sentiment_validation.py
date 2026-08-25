import re
import unicodedata

from typing import Any

from app.analysis.models import (
    SentimentLabel,
)

ALLOWED_SENTIMENTS = {
    label.value
    for label in SentimentLabel
}


def validate_model_payload(
        payload: Any,
        *,
        target_name: str,
        original_answer: str,
        evidence_max_items: int,
) -> tuple[
    dict[str, Any],
    str | None,
    list[str],
    dict[str, str],
    dict[str, Any],
]:
    if not isinstance(
            payload,
            dict,
    ):
        return (
            payload,
            (
                "model response is not "
                "a JSON object"
            ),
            [],
            {},
            _confidence_diagnostics(
                raw=None,
                parsed=None,
                missing=True,
                fallback=True,
            ),
        )

    payload = dict(
        payload
    )

    warnings: list[str] = []

    coercion_fields: dict[
        str,
        str,
    ] = {}

    (
        confidence_diagnostics,
        confidence_warnings,
    ) = _normalize_confidence_payload(
        payload
    )

    warnings.extend(
        confidence_warnings
    )

    if "sentiment" not in payload:
        for source_key in (
                "answer",
                "label",
                "result",
        ):
            if (
                    payload.get(source_key)
                    in ALLOWED_SENTIMENTS
            ):
                payload[
                    "sentiment"
                ] = payload[
                    source_key
                ]

                coercion_fields[
                    source_key
                ] = "sentiment"

                warnings.append(
                    "coerced "
                    f"{source_key} "
                    "to sentiment"
                )

                break

    if (
            payload.get("sentiment")
            not in ALLOWED_SENTIMENTS
    ):
        return (
            payload,
            "missing or invalid sentiment",
            warnings,
            coercion_fields,
            confidence_diagnostics,
        )

    incoming_target = payload.get(
        "target_name"
    )

    if (
            incoming_target
            and incoming_target
            != target_name
    ):
        return (
            payload,
            "target_name mismatch",
            warnings,
            coercion_fields,
            confidence_diagnostics,
        )

    if not incoming_target:
        payload[
            "target_name"
        ] = target_name

        warnings.append(
            "missing target_name; "
            "filled locally"
        )

    if (
            "reason" not in payload
            or payload.get("reason")
            in {None, ""}
    ):
        payload["reason"] = (
            "模型未返回原因"
        )

        warnings.append(
            "missing reason; "
            "filled locally"
        )

    evidence = payload.get(
        "evidence"
    )

    if evidence is None:
        evidence = []

        warnings.append(
            "missing evidence; "
            "filled locally"
        )

    if not isinstance(
            evidence,
            list,
    ):
        evidence = []

        warnings.append(
            "invalid evidence; "
            "cleared locally"
        )

    valid_evidence = [
        item
        for item
        in evidence[
           :evidence_max_items
           ]
        if (
                isinstance(item, str)
                and item
                and item in original_answer
        )
    ]

    if (
            evidence
            and len(valid_evidence)
            != len(
        evidence[
        :evidence_max_items
        ]
    )
    ):
        warnings.append(
            "invalid evidence items removed"
        )

    payload[
        "evidence"
    ] = valid_evidence

    payload[
        "confidence"
    ] = confidence_diagnostics[
        "confidence_parsed"
    ]

    return (
        payload,
        None,
        warnings,
        coercion_fields,
        confidence_diagnostics,
    )


def _normalize_confidence_payload(
        payload: dict[str, Any],
) -> tuple[
    dict[str, Any],
    list[str],
]:
    confidence_present = (
            "confidence" in payload
    )

    raw = (
        payload.get("confidence")
        if confidence_present
        else None
    )

    if (
            _confidence_is_missing(raw)
            or not confidence_present
    ):
        return (
            _confidence_diagnostics(
                raw=raw,
                parsed=None,
                missing=True,
                fallback=True,
            ),
            [
                "missing confidence; "
                "filled locally"
            ],
        )

    (
        parsed,
        warnings,
        fallback,
    ) = _parse_confidence_value(
        raw
    )

    return (
        _confidence_diagnostics(
            raw=raw,
            parsed=parsed,
            missing=False,
            fallback=fallback,
        ),
        warnings,
    )


def _confidence_diagnostics(
        *,
        raw: Any,
        parsed: float | None,
        missing: bool,
        fallback: bool,
) -> dict[str, Any]:
    return {
        "confidence_raw": raw,
        "confidence_parsed": parsed,
        "confidence_missing": missing,
        "confidence_fallback_applied": (
            fallback
        ),
    }


def _confidence_is_missing(
        raw: Any,
) -> bool:
    if raw is None:
        return True

    if (
            isinstance(raw, str)
            and not raw.strip()
    ):
        return True

    return False


def _parse_confidence_value(
        raw: Any,
) -> tuple[
    float | None,
    list[str],
    bool,
]:
    if isinstance(
            raw,
            bool,
    ):
        return (
            None,
            [
                "invalid confidence; "
                "cleared locally"
            ],
            True,
        )

    if isinstance(
            raw,
            str,
    ):
        text = (
            unicodedata
            .normalize(
                "NFKC",
                raw,
            )
            .strip()
        )

        percent_match = re.fullmatch(
            r"([+-]?\d+(?:\.\d+)?)"
            r"\s*%",
            text,
        )

        if percent_match:
            percent_value = float(
                percent_match.group(1)
            )

            if (
                    0
                    <= percent_value
                    <= 100
            ):
                return (
                    percent_value / 100,
                    [
                        "confidence percentage "
                        "normalized"
                    ],
                    True,
                )

            return (
                None,
                [
                    "confidence out of range; "
                    "cleared locally"
                ],
                True,
            )

        try:
            value = float(
                text
            )

        except ValueError:
            return (
                None,
                [
                    "invalid confidence; "
                    "cleared locally"
                ],
                True,
            )

    elif isinstance(
            raw,
            (int, float),
    ):
        value = float(
            raw
        )

    else:
        return (
            None,
            [
                "invalid confidence; "
                "cleared locally"
            ],
            True,
        )

    if 0 <= value <= 1:
        return (
            value,
            [],
            False,
        )

    return (
        None,
        [
            "confidence out of range; "
            "cleared locally"
        ],
        True,
    )
