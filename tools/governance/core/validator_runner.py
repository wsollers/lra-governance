from __future__ import annotations

import inspect
from pathlib import Path
from typing import Iterable

from .formal_blocks import clear_formal_block_cache
from .file_inventory import files_to_validate
from .tex import clear_text_cache


def default_file_inventory(volume_root: Path | str) -> list[Path]:
    clear_text_cache()
    clear_formal_block_cache()
    return files_to_validate([volume_root], only_reachable=False)


def run_validator(validator, volume_root: Path | str, files: Iterable[Path] | None = None):
    root = Path(volume_root)
    inventory = list(files) if files is not None else default_file_inventory(root)
    if "files" in inspect.signature(validator.validate).parameters:
        return validator.validate(root, files=inventory)
    return validator.validate(root)


def run_validators(validators, volume_root: Path | str, files: Iterable[Path] | None = None):
    root = Path(volume_root)
    inventory = list(files) if files is not None else default_file_inventory(root)
    findings = []
    for _name, validator in validators:
        findings.extend(run_validator(validator, root, inventory))
    return findings
