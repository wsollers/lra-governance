r"""TeX <-> base64 codec for extracted/structured artifacts.

Rationale: TeX payloads (backslashes, braces, pipes, dollar signs) are a perennial
escaping hazard inside YAML/JSON -- e.g. an unquoted `formal: |x - c| < r` breaks
yaml.safe_load. base64-encoding a TeX payload makes it an opaque, always-safe scalar.

Convention: an encoded value carries a `b64:` prefix, so it is self-marking -- a
consumer decodes iff the value starts with the prefix, and plain values pass through
unchanged. This lets a record mix plain structural fields (name, id, arity -- kept
readable and used by validators) with encoded long-form fields (formal, reading_template).

USE FOR: machine-extracted TeX (extractor output, knowledge-graph payloads) where
robustness matters more than human readability.
DO NOT blanket-encode hand-authored canonical registries: that destroys the
readability that is their purpose. There, quote the offending scalar instead
(formal: "|x - c| < r"), or encode ONLY the genuinely long-form non-validation fields.
"""
from __future__ import annotations
import base64

PREFIX = "b64:"

def encode_tex(s: str) -> str:
    return PREFIX + base64.b64encode(s.encode("utf-8")).decode("ascii")

def decode_tex(s: str) -> str:
    if isinstance(s, str) and s.startswith(PREFIX):
        return base64.b64decode(s[len(PREFIX):]).decode("utf-8")
    return s

def is_encoded(s) -> bool:
    return isinstance(s, str) and s.startswith(PREFIX)

def encode_fields(record: dict, fields) -> dict:
    """Return a copy of record with the named string fields base64-encoded."""
    out = dict(record)
    for f in fields:
        if isinstance(out.get(f), str):
            out[f] = encode_tex(out[f])
    return out

def decode_fields(record: dict, fields=None) -> dict:
    """Return a copy with encoded fields decoded (all fields if `fields` is None)."""
    out = dict(record)
    keys = fields if fields is not None else list(out.keys())
    for f in keys:
        if is_encoded(out.get(f)):
            out[f] = decode_tex(out[f])
    return out
