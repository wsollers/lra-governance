from __future__ import annotations

import argparse
import json
from pathlib import Path
import yaml

from .config import GenerationConfig
from .generator import UniverseTestGenerator
from .state import GeneratorState


def parse_csv_int(value: str) -> list[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def parse_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a persistent synthetic universe of syntactically valid mathematical TeX tests.")
    p.add_argument("--config")
    p.add_argument("--state", default="generator-state.json")
    p.add_argument("--output", default="generated-tests.yaml")
    p.add_argument("--count", type=int)
    p.add_argument("--seed", type=int)
    p.add_argument("--strategy", choices=["least-covered", "random"])
    p.add_argument("--max-formula-depth", type=int)
    p.add_argument("--max-quantifier-depth", type=int)
    p.add_argument("--predicate-arities", type=parse_csv_int)
    p.add_argument("--function-arities", type=parse_csv_int)
    p.add_argument("--connectives", type=parse_csv)
    p.add_argument("--quantifiers", type=parse_csv)
    p.add_argument("--discourse-forms", type=parse_csv)
    p.add_argument("--renderers", type=parse_csv)
    p.add_argument("--append", action="store_true")
    p.add_argument("--coverage-report")
    p.add_argument("--registry-output")
    return p


def main() -> None:
    args = build_parser().parse_args()
    config = GenerationConfig.from_yaml(args.config) if args.config else GenerationConfig()
    for key in ["count", "seed", "strategy", "max_formula_depth", "max_quantifier_depth", "predicate_arities", "function_arities", "connectives", "quantifiers", "discourse_forms", "renderers"]:
        value = getattr(args, key)
        if value is not None:
            setattr(config, key, value)

    state = GeneratorState.load(args.state)
    cases = UniverseTestGenerator(config, state).generate()
    out = Path(args.output)
    existing = []
    if args.append and out.exists():
        existing = yaml.safe_load(out.read_text(encoding="utf-8")) or []
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(existing + [case.to_dict() for case in cases], sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    state.save(args.state)

    report_path = Path(args.coverage_report) if args.coverage_report else out.with_name("coverage-report.json")
    report_path.write_text(json.dumps({"universe_version": state.universe_version, "case_count": state.case_count, "coverage": state.coverage}, indent=2, sort_keys=True), encoding="utf-8")
    if args.registry_output:
        registry_path = Path(args.registry_output)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(state.synthetic_registry(), indent=2, sort_keys=True), encoding="utf-8")
        print(f"Synthetic registry saved to {registry_path}")
    print(f"Generated {len(cases)} cases into {out}")
    print(f"State saved to {args.state}")
    print(f"Coverage report saved to {report_path}")


if __name__ == "__main__":
    main()
