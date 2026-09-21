# Lean Knowledge Explorer Records

## Purpose

This standard defines the extraction-facing record needed to explain a Lean
declaration in its environment. The Knowledge Explorer implementation remains
owned by the `lra-knowledge-explorer` repository. This document owns the
cross-repository semantic contract.

## Declaration Record

Each extracted declaration should support these fields when available:

- stable declaration name, source file, source span, namespace, and layer;
- declaration kind and proof/completion status;
- compilation status (`compiled` or `source-only`) and status provenance;
- imported modules needed for visibility;
- explicit, implicit, strict-implicit, and instance binders in source order;
- elaborated type and a human-readable quantified form;
- outer definition or structure fields and an unfolded proposition view;
- specializations from generic carrier/policy/relation parameters to the
  declaration's concrete arguments;
- hidden instances and the projections whose types depend on them;
- type and ambient dependencies;
- observed proof dependencies, separately labeled from type dependencies;
- provider, backend, or construction when relevant;
- related declarations and learner pain-point tags;
- source authority and extraction revision.

Unavailable data must be explicit. In particular, absence of compiled unfold
data is `unavailable`, not permission to repeat the folded form and label it
unfolded without qualification.

## Edge Kinds

Use distinct, visible edge kinds:

- `imports`;
- `mentions-in-type`;
- `unfolds-to`;
- `field-of`;
- `constructs`;
- `satisfies`;
- `instance-supplied-by`;
- `specializes`;
- `proof-observed-to-use`;
- `related-to`.

Import and type edges may be extracted before proofs are complete. A proof-use
edge exists only when observed in a completed proof term or other authoritative
proof source. Never infer it from file order or a plausible theorem name.

## Quantified And Unfolded Views

The quantified view must expose theorem-header binders in order and distinguish
ordinary universal parameters from instance search:

```text
implicit parameter -> explicit parameter -> instance parameter -> result
```

The unfolded view should unfold only the outer public wrapper required to make
the goal's structure visible. It must preserve inner named concepts unless a
deeper view is explicitly requested. Every view records its provenance:

- compiled elaboration;
- source elaboration;
- deterministic source expansion;
- source fallback.

Source fallback must be labeled and must not claim unavailable compiled data.

## Partial Compilation

The explorer extraction workflow must remain usable while formalization is in
progress. A failed aggregate Lean target does not authorize stale compiled
records and does not remove current source declarations from the explorer.

Use a clean project build directory. After a best-effort build:

- dump every declaration whose current module compiled successfully;
- recover missing proof-like declarations from current source;
- label recovered records `source-only` and never mark them checked merely
  because their source body lacks `sorry`;
- prefer a documented predicate-logic block when available, otherwise label
  the declaration header as a source-signature fallback;
- report compiled and source-fallback counts plus `complete` or `partial`
  compilation coverage in dataset metadata.

A source-only declaration may be `pending`, `assumed`, or `unverified`. It may
not be presented as compiled or checked until the current Lean environment
accepts it.

## Search And Filters

The explorer should support search by declaration name, source path, namespace,
logical level, construction/provider, declaration kind, proof status,
dependency edge kind, and pain-point tag.

Each result should open a declaration detail view with:

1. signature and quantified form;
2. theorem environment;
3. structure/unfolded view;
4. dependency graph with typed edges;
5. proof status and observed proof dependencies;
6. related learning notes and source links.

## Identity Pilot

The Identity pilot must preserve the independent dimensions of logical level
and provider/construction. It should expose `Interface`, `Laws`,
`Constructions`, `Satisfies`, and `Interop` as ownership layers and distinguish
generic identity, FOL formula-definable substitution, Henkin SOL, full SOL,
equality presentation, equivalence, and congruence.

Proof-pending declarations may still participate in import, type, unfolds,
field, construction, satisfaction, specialization, and instance edges. Their
proof-use dependency set remains `unobserved` until a proof exists.
