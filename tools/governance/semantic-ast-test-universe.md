# Semantic AST Test Universe

The semantic AST test universe is a deterministic local generator for parser
calibration. It creates governed synthetic mathematical vocabulary, generated
TeX displays, canonical formula JSON, and a known governed AST for each case.

The purpose is not to prove generated mathematics. The purpose is to expose
parser and AST generation bugs with controlled input where the intended AST is
known before parsing.

## Location

- Generator package:
  `tools/governance/test_tex_generator/`
- Generator configs:
  `tools/governance/fixtures/test_tex_generator/`
- Parser comparison validator:
  `tools/governance/validate_test_tex_generator_ast.py`

## Workflow

1. Generate test cases and the synthetic registry.
2. Materialize the generated predicate, relation, structure, and notation
   entries into the canonical governance YAML when testing registry lookup.
3. Run focused generator unit tests.
4. Run focused parser unit tests for the newly materialized surfaces.
5. Run `validate_test_tex_generator_ast.py` against the generated cases.
6. Cluster failures by parser behavior, then add focused positive and negative
   parser tests before patching the generic parser behavior.

The synthetic registry is a source of truth for generated tests. The parsers
must resolve concrete registered surfaces such as `P_{14}` and `R_{5}` through
the canonical YAML registry, not by family inference.

## Commands

Generate a small batch:

```powershell
cd F:\repos\lra-governance
python -m tools.governance.test_tex_generator.cli --config tools\governance\fixtures\test_tex_generator\default.yaml --state build\semantic-audit\test-tex-generator\generator-state.json --output build\semantic-audit\test-tex-generator\generated-tests.yaml --coverage-report build\semantic-audit\test-tex-generator\coverage-report.json --registry-output build\semantic-audit\test-tex-generator\synthetic-registry.json
```

Generate a deeper batch:

```powershell
cd F:\repos\lra-governance
python -m tools.governance.test_tex_generator.cli --config tools\governance\fixtures\test_tex_generator\deep-quantifiers.yaml --state build\semantic-audit\test-tex-generator\deep-generator-state.json --output build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --coverage-report build\semantic-audit\test-tex-generator\deep-coverage-report.json --registry-output build\semantic-audit\test-tex-generator\deep-synthetic-registry.json --count 500
```

Compare generated TeX against known ASTs:

```powershell
cd F:\repos\lra-governance
python tools\governance\validate_test_tex_generator_ast.py --cases build\semantic-audit\test-tex-generator\deep-generated-tests.yaml --output build\semantic-audit\test-tex-generator\deep-parser-roundtrip-report.json
```

Run focused tests:

```powershell
cd F:\repos\lra-governance
python tools\governance\test_test_tex_generator.py
python tools\governance\test_semantic_latex_ast.py
python tools\governance\test_semantic_lark_logic_parser.py
```

## Failure Interpretation

- `hand_parse_error` or `lark_parse_error`: the parser cannot parse the
  generated display.
- `hand_ast_mismatch` or `lark_ast_mismatch`: the parser produced an AST, but
  it does not match the canonical formula-derived AST.
- `parser_disagreement`: both parser witnesses parsed successfully, but their
  ASTs differ.
- `display_missing`: the generated discourse did not contain a display formula.

Failures should be treated as parser, renderer, or registry-contract signals.
Do not patch individual generated cases by hand to quiet the report.
