You are classifying a LaTeX theorem-like block for LRA decoration compliance.

Do not rewrite the block.
Do not invent labels.
Do not invent predicates.
Do not infer missing dependencies unless the label is visible.
Return strict JSON only.

Classify whether the block has:
- stable label
- correct label prefix
- interpretation remark
- quantified/formal statement block if applicable
- predicate reading block if applicable
- negated quantified statement block if applicable
- dependencies remark
- dependency targets using hyperref to statement labels
- no prf: labels used as dependencies
- no predicate leakage into theorem body
- no invented predicate names

Return JSON schema:
{
  "classification": "compliant | mostly_compliant | non_compliant | needs_human_review | not_applicable",
  "severity": "info | warning | error",
  "confidence": 0.0,
  "detected": {
    "environment": "...",
    "label": "...",
    "label_prefix_ok": true,
    "has_interpretation": true,
    "has_quantified_statement": true,
    "has_predicate_reading": true,
    "has_negation": true,
    "has_dependencies": true,
    "dependencies_use_hyperref": true,
    "dependencies_use_statement_labels": true,
    "uses_prf_as_dependency": false,
    "predicate_leakage_suspected": false
  },
  "issues": [
    {
      "code": "missing_dependencies",
      "message": "Dependencies remark is missing.",
      "severity": "warning"
    }
  ],
  "recommended_human_action": "..."
}

