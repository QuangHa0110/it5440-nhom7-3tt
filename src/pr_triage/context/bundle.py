"""Dựng `ContextBundle` có băm ổn định (dùng cho cache và tái lập)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace

from pr_triage.core.models import ContextBundle, ContextSlice, Variant
from pr_triage.core.secrets import mask


def make_bundle(
    variant: Variant,
    finding_id: str,
    slices: Sequence[ContextSlice],
    source: str | None = None,
    sink: str | None = None,
    sanitizers: Sequence[str] = (),
    missing: Sequence[str] = (),
    extract_ms: int = 0,
) -> ContextBundle:
    slices = [replace(s, text=mask(s.text)[0]) for s in slices]
    payload = json.dumps(
        [
            variant.value,
            finding_id,
            [[s.file, s.start, s.end, s.role, s.text] for s in slices],
            source,
            sink,
            list(sanitizers),
            list(missing),
        ],
        ensure_ascii=False,
    )
    return ContextBundle(
        bundle_hash=hashlib.sha256(payload.encode()).hexdigest(),
        variant=variant,
        finding_id=finding_id,
        slices=tuple(slices),
        source=source,
        sink=sink,
        sanitizers=tuple(sanitizers),
        missing=tuple(missing),
        extract_ms=extract_ms,
    )
