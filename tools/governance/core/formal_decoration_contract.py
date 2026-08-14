"""Canonical structural contract for theorem-like support decoration."""

DECORATION_ORDER = {
    "proof_link": 10,
    "standard quantified statement": 20,
    "predicate reading": 30,
    "negated quantified statement": 40,
    "negation predicate reading": 50,
    "failure modes": 60,
    "contrapositive quantified statement": 70,
    "contrapositive predicate reading": 80,
    "interpretation": 100,
    "notation": 102,
    "historical note": 105,
    "source comparison": 105,
    "exposition": 110,
    "examples": 120,
    "non-examples": 130,
    "dependencies": 140,
}

DEPENDENT_DECORATION_PARENTS = {
    "negation predicate reading": "negated quantified statement",
    "contrapositive predicate reading": "contrapositive quantified statement",
}

DEPENDENT_DECORATION_CHILDREN = {
    "negated quantified statement": "negation predicate reading",
    "contrapositive quantified statement": "contrapositive predicate reading",
}

FAILURE_MODE_DECOMPOSITION_TRIGGERS = {
    "negated quantified statement",
    "negation predicate reading",
    "contrapositive quantified statement",
    "contrapositive predicate reading",
}

REPEATABLE_DECORATION_BLOCKS = {"failure modes", "exposition", "examples", "non-examples"}

FORBIDDEN_DECORATION_BY_ENV = {
    "definition": {"contrapositive quantified statement", "contrapositive predicate reading"},
    "axiom": {"contrapositive quantified statement", "contrapositive predicate reading", "examples", "non-examples"},
    "theorem": {"examples", "non-examples"},
    "lemma": {"examples", "non-examples"},
    "proposition": {"examples", "non-examples"},
    "corollary": {"examples", "non-examples"},
}
