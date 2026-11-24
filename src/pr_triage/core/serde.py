"""Chuyển dataclass miền qua lại dict/JSON, không dùng thư viện ngoài."""

from __future__ import annotations

import dataclasses
import json
import types
import typing
from enum import Enum
from typing import Any, Union, get_args, get_origin


def to_plain(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (tuple, list)):
        return [to_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_plain(v) for k, v in obj.items()}
    return obj


def to_json(obj: Any) -> str:
    return json.dumps(to_plain(obj), ensure_ascii=False, sort_keys=True)


def _convert(value: Any, hint: Any) -> Any:
    origin = get_origin(hint)
    if origin in (Union, types.UnionType):
        args = [a for a in get_args(hint) if a is not type(None)]
        if value is None:
            return None
        return _convert(value, args[0])
    if origin is tuple:
        (inner, *_) = get_args(hint)
        return tuple(_convert(v, inner) for v in value)
    if origin is list:
        (inner,) = get_args(hint)
        return [_convert(v, inner) for v in value]
    if isinstance(hint, type):
        if issubclass(hint, Enum):
            return hint(value)
        if dataclasses.is_dataclass(hint):
            return from_plain(hint, value)
    return value


def from_plain[T](cls: type[T], data: dict[str, Any]) -> T:
    hints = typing.get_type_hints(cls)
    kwargs = {
        f.name: _convert(data[f.name], hints[f.name])
        for f in dataclasses.fields(cls)  # type: ignore[arg-type]
        if f.name in data
    }
    return cls(**kwargs)


def from_json[T](cls: type[T], text: str) -> T:
    return from_plain(cls, json.loads(text))
