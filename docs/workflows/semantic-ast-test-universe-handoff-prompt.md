# Handoff Prompt: Semantic AST Test Universe

You are working in `F:\repos\lra-governance`.

Goal: use the local synthetic TeX universe generator to hone semantic AST
generation and parser coverage. The test harness generates TeX with a known
canonical formula and expected governed AST, then validates that both governance
parsers produce that AST from the rendered TeX.

Constraints:

- Do not call external LLMs unless explicitly requested.
- Use local Python/governance validators first.
- Fixes must be generic parser, renderer, validator, or registry behavior.
- Do not hand-edit generated cases just to quiet a validator.
- When parser behavior changes, add positive and negative unit tests before
  patching.
- Synthetic generated vocabulary must be materialized into canonical governance
  YAML when testing registry lookup, with `testing: true` on synthetic-only
  entries. Look up symbols as concrete registered surfaces, the same way real
  predicates such as `PeanoSystem` or `IsOpen...` are resolved. Do not infer
  families such as `P_n` or `R_n`.
- The `testing: true` flag is for knowledge extraction/export boundaries. Once
  TeX is handed to parsers, validator registry lookup, predicate signatures,
  operator metadata, and predicate leakage checks should treat those entries as
  ordinary registered vocabulary. Do not skip them in lookup code just because
  they are marked `testing: true`.

Primary files:

- Generator package:
  `tools/governance/test_tex_generator/`
- Generator configs:
  `tools/governance/fixtures/test_tex_generator/default.yaml`
  `tools/governance/fixtures/test_tex_generator/deep-quantifiers.yaml`
- Parser round-trip validator:
  `tools/governance/validate_test_tex_generator_ast.py`
- Hand parser:
  `tools/governance/semantic_latex_ast.py`
- Lark parser:
  `tools/governance/semantic_lark_logic_parser.py`
- Canonical registries:
  `predicates.yaml`, `structures.yaml`, `notation.yaml`, `relations.yaml`

Current workflow:

1. Ensure synthetic predicate, relation, structure, and notation symbols are
   registered in the canonical YAML files with `testing: true`.
2. Generate synthetic cases and a synthetic registry export from the registered
   test universe.
3. Run generator tests.
4. Run hand-parser and Lark-parser tests.
5. Run `validate_test_tex_generator_ast.py` against the generated case YAML.
6. Cluster failures by root cause.
7. Add focused positive and negative tests.
8. Patch the generic parser, renderer, validator, or registry behavior.
9. Re-run focused tests and the parser round-trip validator.

Useful commands:

```powershell
cd F:\repos\lra-governance
python tools\governance\test_test_tex_generator.py
python tools\governance\test_semantic_latex_ast.py
python tools\governance\test_semantic_lark_logic_parser.py
```

```powershell
cd F:\repos\lra-governance
python -m tools.governance.test_tex_generator.cli --config tools\governance\fixtures\test_tex_generator\deep-quantifiers.yaml --state build\semantic-audit\test-tex-generator\deep-generator-state.json --output build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --coverage-report build\semantic-audit\test-tex-generator\deep-coverage-report.json --registry-output build\semantic-audit\test-tex-generator\deep-synthetic-registry.json --count 500
```

```powershell
cd F:\repos\lra-governance
python tools\governance\validate_test_tex_generator_ast.py --cases build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --output build\semantic-audit\test-tex-generator\deep-parser-roundtrip-report.json
```

Known failure classes from the first deep run:

- Symbolic connective rendering was too tight in places, producing TeX-like
  strings such as `\rightarrowx_{16}` or `\landR_{8}`.
- Text connective rendering used `\text{implies}` and
  `\text{if and only if}`, which parser normalization did not fully cover.
- Expanded quantifier forms such as
  `(\forall x)(x\in A\rightarrow ...)` need broader parser support.
- Lark remains stricter than the hand parser on deeply nested generated
  formulas.

The intended end state is not that every generated string is accepted by
weakening validation. The intended end state is that generated TeX, canonical
formula JSON, expected governed AST, hand-parser AST, and Lark-parser AST can be
compared mechanically, and disagreements drive focused parser and registry
improvements.
