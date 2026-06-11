# Governance Parity Fixtures

These fixtures are the safety net for retiring legacy validators and prompt code.
Each fixture is a small volume/chapter tree with known defects and a manifest of
issue codes that the thin validators must continue to catch.

Retirement rule:

- do not delete a legacy validator/prompt path until the relevant behavior is
  represented here or intentionally documented as dropped;
- keep fixtures small and single-purpose;
- prefer adding a new fixture over weakening a validator test.
