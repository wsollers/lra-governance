# Phase 5: Generated Agent Wrapper Preview Review

## Commands

Generated previews with:

```powershell
python tools/governance/generate_agent_wrappers.py --dry-run --out reports/generated-agent-wrapper-preview
```

Validated previews with:

```powershell
python tools/governance/validate_repo_rules.py --preview reports/generated-agent-wrapper-preview
```

Validator result: passed.

Total preview files generated: 60.

## Overlay Routing

| Repository | Overlay |
| --- | --- |
| `Learning-Real-Analysis` | `learning-real-analysis.md` |
| `lra-common` | `lra-common.md` |
| `lra-volume-i` | `lra-volume.md` |
| `lra-volume-ii` | `lra-volume.md` |
| `lra-volume-iii` | `lra-volume.md` |
| `lra-volume-iv` | `lra-volume.md` |
| `lra-volume-v` | `lra-volume.md` |
| `lra-lean` | `lra-lean.md` |
| `lra-nurbs` | `lra-nurbs.md` |
| `lra-knowledge-explorer` | `lra-knowledge-explorer.md` |
| `lra-numerical-analysis` | `lra-numerical-analysis.md` |
| `lra-pdf-extractor` | `lra-pdf-extractor.md` |

All preview directories contained:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.github/instructions/lra.instructions.md`

## Header Review

Representative wrapper files contained:

- `GENERATED FILE — DO NOT EDIT BY HAND`
- source repo `wsollers/lra-governance`
- source document list
- the repo overlay path used
- emergency-edit upstreaming language

No machine-local paths were found in generated previews. The words `secret`
and `token` appear only in negative guard rails instructing generated files not
to contain secrets, credentials, or token values.

## Provider Wrapper Assessment

| Provider file | Assessment | Notes |
| --- | --- | --- |
| `AGENTS.md` | acceptable | Suitable Codex entrypoint with global rules, overlay, and provider note. |
| `CLAUDE.md` | acceptable | Includes `@AGENTS.md` plus readable fallback text. |
| `GEMINI.md` | acceptable | Contains the same essential guard rails and overlay content. |
| `.github/copilot-instructions.md` | acceptable | Concise enough for initial Copilot use, though future versions may point more aggressively to canonical docs. |
| `.github/instructions/lra.instructions.md` | acceptable | Concise generated repo instruction file with the same guard rails. |

## Volume Preview Safety

The `lra-volume-*` previews receive volume-content guidance and the
`lra-volume.md` overlay. They do not receive positive Lean, NURBS/Vulkan,
numerical-analysis benchmark/plotting, or PDF-extractor workflow instructions.

Negative guard rails are preserved, including the warning that specialist rules
do not belong in volume repos. This is correct and should remain allowed by the
validator.

## Specialist Repo Assessment

- `lra-lean` receives Lean-specific guidance.
- `lra-nurbs` receives C++ / Vulkan / geometry / simulation guidance.
- `lra-numerical-analysis` receives numerical methods, benchmark, plotting, and
  report guidance.
- `lra-pdf-extractor` receives PDF/source ingestion, bibliography extraction,
  GUI, staging, and local-model safety guidance.
- `lra-knowledge-explorer` receives theorem explorer and extraction pipeline
  guidance.
- `lra-common` receives shared LaTeX infrastructure and bibliography guidance.
- `Learning-Real-Analysis` receives monorepo, canonical YAML, and integration
  hub guidance.

## Verbosity Assessment

| Provider file | Verbosity |
| --- | --- |
| `AGENTS.md` | acceptable |
| `CLAUDE.md` | acceptable |
| `GEMINI.md` | acceptable |
| `.github/copilot-instructions.md` | acceptable |
| `.github/instructions/lra.instructions.md` | acceptable |

The previews are short enough for Phase 5 review. Future Copilot-specific
iterations may reduce embedded overlay text if provider limits require it, but
no immediate reduction is required before the next planning phase.

## Defects Found

No blocking defects were found.

No template, generator, or validator changes were needed in this phase.

## Recommended Fixes Before Downstream Sync

- Add an explicit drift-report command before any write mode exists.
- Add a generated-preview manifest containing repo, overlay, provider file, and
  source commit.
- Consider provider-size limits before committing to full Copilot wrapper
  content.
- Keep write mode blocked until preview review and drift checks are stable.

## Final Verdict

APPROVE PREVIEW SHAPE

