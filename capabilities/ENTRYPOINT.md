# LRA Agent Execution Contract

This file applies after the resolver selects a task route. The manifest owns
routing; this file defines behavior shared by every route.

## Execute

1. Work within the user's request, resolved repository, and selected route.
2. Load the eager instruction files in the returned order.
3. Treat lazy references, tools, schemas, examples, and generated indexes as
   pointers. Open or run only what a concrete step requires.
4. Perform the capability action. Re-resolve if the task materially changes.
5. Run every returned verification command. Report success only when all
   required gates pass; identify any skipped or failing gate explicitly.

## Respect Authority

- Edit the canonical owner, not a generated artifact or downstream delegate.
  If ownership is unclear, follow the smallest relevant reference pointer
  before editing.
- Query canonical registries through the routed lookup or vocabulary tool. Do
  not invent names, notation, relations, labels, structures, or dependencies.
  Report a missing canonical entry.
- Preserve mathematical substance during structural, mechanical, migration,
  build, and governance work. Change mathematics only when the user explicitly
  requests mathematical authoring or correction through an applicable route.
- Keep generated structure separate from authored substance. Do not duplicate
  canonical formulas, signatures, policies, or routing tables in generated
  files.

## Stop

Stop and report the blocking condition when:

- governance, a required canonical source, or a required registry is missing;
- resolution is unknown, ambiguous, invalid, or over budget;
- instructions conflict or ownership remains ambiguous;
- completion requires work outside the user's authorized scope; or
- a required verification gate still fails after safe in-scope correction.
