#!/usr/bin/env python3
"""Tests for the generated human task index."""

import unittest

import yaml

import generate_task_index as G


class TaskIndexTests(unittest.TestCase):
    def test_generated_index_is_current(self):
        manifest = yaml.safe_load(G.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(G.DEFAULT_OUTPUT.read_text(encoding="utf-8"), G.render(manifest))

    def test_index_marks_itself_generated_and_resolver_first(self):
        text = G.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertIn("GENERATED FILE. DO NOT EDIT BY HAND", text)
        self.assertIn("capabilities/resolve.py", text)
        self.assertIn("Agents should not\npreload this document", text)


if __name__ == "__main__":
    unittest.main()
