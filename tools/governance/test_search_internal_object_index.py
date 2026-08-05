from __future__ import annotations

from tools.governance.search_internal_object_index import search_records


def test_search_ranks_rough_suprema_sum_query() -> None:
    records = [
        {
            "object_id": "tex:prop:bounds-sum-set",
            "source_family": "tex",
            "kind": "proposition",
            "name": "Bounds for Suprema and Infima Under Set Addition",
            "label": "prop:bounds-sum-set",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/bounding/notes/bounds-algebra/source.tex",
            "line": 1,
            "statement": "The supremum of a sum set is bounded by the sum of the suprema.",
            "search_text": "proposition Bounds for Suprema and Infima Under Set Addition prop:bounds-sum-set",
        },
        {
            "object_id": "tex:def:upper-darboux-sum",
            "source_family": "tex",
            "kind": "definition",
            "name": "Upper Darboux Sum",
            "label": "def:upper-darboux-sum",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-integration/notes/source.tex",
            "line": 10,
            "statement": "An upper Darboux sum is defined using a partition.",
            "search_text": "definition Upper Darboux Sum def:upper-darboux-sum",
        },
    ]

    results = search_records(records, "suprema of a sum", source_family="tex", limit=2)

    assert results[0]["label"] == "prop:bounds-sum-set"


def test_search_handles_typo_with_ngram_overlap() -> None:
    records = [
        {
            "object_id": "tex:thm:supremum-subadditivity",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Supremum Subadditivity",
            "label": "thm:supremum-subadditivity",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/functions/notes/source.tex",
            "line": 42,
            "statement": "The supremum of the sum is at most the sum of the suprema.",
            "search_text": "theorem Supremum Subadditivity thm:supremum-subadditivity",
        }
    ]

    results = search_records(records, "sumpremum sum", source_family="tex")

    assert results
    assert results[0]["label"] == "thm:supremum-subadditivity"


def test_search_normalizes_latex_inequality_symbols() -> None:
    records = [
        {
            "object_id": "tex:thm:supremum-subadditivity",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Supremum Subadditivity",
            "label": "thm:supremum-subadditivity",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/functions/notes/source.tex",
            "line": 42,
            "statement": r"\[ \sup_A(f+g)\leq \sup_A f+\sup_A g. \]",
            "search_text": "theorem Supremum Subadditivity thm:supremum-subadditivity",
        }
    ]

    results = search_records(records, "supremum sum at most sum suprema", source_family="tex")

    assert results
    assert results[0]["label"] == "thm:supremum-subadditivity"


def test_search_boosts_rational_bezout_domain_terms() -> None:
    records = [
        {
            "object_id": "tex:thm:unrelated-linear-combination",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Linear Combination Approximation",
            "label": "thm:unrelated-linear-combination",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/functions/notes/source.tex",
            "line": 12,
            "statement": "A linear combination of two functions has the expected limit.",
            "search_text": "theorem Linear Combination Approximation",
        },
        {
            "object_id": "tex:thm:bezout-identity-on-z",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Bezout Identity on Z",
            "label": "thm:bezout-identity-on-z",
            "repo_root": "F:/repos/lra-volume-ii",
            "path": "volume-ii/book-discrete-algebraic/integers/notes/source.tex",
            "line": 30,
            "statement": "If gcd(a,b)=1, then there exist integers m,n such that ma+nb=1.",
            "search_text": "theorem Bezout Identity on Z integer divisibility gcd coprime linear combination",
        },
    ]

    results = search_records(records, "relatively prime coprime integers linear combination equals one iff gcd one", source_family="tex")

    assert results[0]["label"] == "thm:bezout-identity-on-z"


def test_search_boosts_unique_limit_wording() -> None:
    records = [
        {
            "object_id": "tex:lem:rational-limit-unique",
            "source_family": "tex",
            "kind": "lemma",
            "name": "Rational Limit Unique",
            "label": "lem:rational-limit-unique",
            "repo_root": "F:/repos/lra-volume-ii",
            "path": "volume-ii/book-continuum/rationals/source.tex",
            "line": 4,
            "statement": "A rational limit representation is unique.",
            "search_text": "lemma rational limit unique",
        },
        {
            "object_id": "tex:thm:uniqueness-of-limits",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Uniqueness of Limits",
            "label": "thm:uniqueness-of-limits",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/sequences/notes/source.tex",
            "line": 10,
            "statement": "If a real sequence converges to L1 and to L2, then L1=L2.",
            "search_text": "theorem uniqueness of limits convergent sequence unique limit real sequence",
        },
    ]

    results = search_records(records, "convergent sequence has unique limit", source_family="tex")

    assert results[0]["label"] == "thm:uniqueness-of-limits"


def test_search_boosts_constant_comparison_wording() -> None:
    records = [
        {
            "object_id": "tex:thm:ratio-limit",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Ratio Limit",
            "label": "thm:ratio-limit",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/sequences/notes/source.tex",
            "line": 8,
            "statement": "A ratio limit theorem for sequences.",
            "search_text": "theorem ratio limit sequence",
        },
        {
            "object_id": "tex:thm:constant-comparison-sequence-limits",
            "source_family": "tex",
            "kind": "theorem",
            "name": "Constant Comparison for Sequence Limits",
            "label": "thm:constant-comparison-sequence-limits",
            "repo_root": "F:/repos/lra-volume-iii",
            "path": "volume-iii/book-analysis-i/sequences/notes/source.tex",
            "line": 20,
            "statement": r"If x_n converges to L and eventually x_n \leq B, then L \leq B.",
            "search_text": "theorem constant comparison sequence limits eventually bounded above by constant",
        },
    ]

    results = search_records(records, "limit respects upper bound sequence all terms less than equal M limit less than equal M", source_family="tex")

    assert results[0]["label"] == "thm:constant-comparison-sequence-limits"
