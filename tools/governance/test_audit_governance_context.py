#!/usr/bin/env python3
"""Tests for deterministic governance-context accounting."""

import unittest

import audit_governance_context as A


class GovernanceContextAuditTests(unittest.TestCase):
    def test_estimator_is_deterministic_ceiling_chars_div_four(self):
        self.assertEqual(A.estimate_tokens(""), 0)
        self.assertEqual(A.estimate_tokens("a"), 1)
        self.assertEqual(A.estimate_tokens("abcd"), 1)
        self.assertEqual(A.estimate_tokens("abcde"), 2)

    def test_live_governance_context_audit_passes(self):
        result = A.audit()
        self.assertTrue(result["ok"], result["errors"])
        self.assertGreaterEqual(result["route_count"], 40)
        self.assertLessEqual(result["max_context"]["governance_context_tokens"], result["max_context"]["budget"])

    def test_audit_accounts_for_wrapper_and_eager_packet(self):
        result = A.audit()
        record = result["contexts"][0]
        self.assertEqual(record["governance_context_tokens"], record["wrapper_tokens"] + record["eager_packet_tokens"])


if __name__ == "__main__":
    unittest.main()
