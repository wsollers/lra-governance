#!/usr/bin/env python3
"""Tests for decoration_rules: math-box wrapper, ported legacy rules, breadcrumb
placement, toolkit placement/content/format, and structural-roadmap purge flags.
Runs under pytest, or standalone: `python test_decoration_rules.py`.
"""
import decoration_rules as dr

def _codes(issues): return {i.code for i in issues}

# ---------- math box wrapper (block rules) ----------
def _block(text):
    bs = dr.extract_blocks(text); assert bs, "no block parsed"; return bs[0]

def test_semantic_box_ok():
    t = "\\begin{definitionbox}{Definition (X)}\n\\begin{definition}[X]\n\\label{def:x}\nbody\n\\end{definition}\n\\end{definitionbox}"
    assert "raw_tcolorbox_wrapper" not in _codes(dr.run_rules(_block(t), dr.Context()))

def test_raw_tcolorbox_flagged():
    t = "\\begin{tcolorbox}[colback=thmbox,\n  arc=2pt]\n\\begin{theorem}[Y]\n\\label{thm:y}\nbody\n\\end{theorem}\n\\end{tcolorbox}"
    assert "raw_tcolorbox_wrapper" in _codes(dr.run_rules(_block(t), dr.Context()))

def test_unwrapped_flagged_when_required():
    t = "\\begin{lemma}[Z]\n\\label{lem:z}\nbody\n\\end{lemma}"
    assert "unwrapped_math_env" in _codes(dr.run_rules(_block(t), dr.Context(require_box=True)))

def test_unwrapped_ok_when_plain_style():
    t = "\\begin{lemma}[Z]\n\\label{lem:z}\nbody\n\\end{lemma}"
    assert "unwrapped_math_env" not in _codes(dr.run_rules(_block(t), dr.Context(require_box=False)))

# ---------- ported legacy rules ----------
def test_missing_label():
    t = "\\begin{definitionbox}{D}\n\\begin{definition}[X]\nbody\n\\end{definition}\n\\end{definitionbox}"
    assert "missing_label" in _codes(dr.run_rules(_block(t), dr.Context()))

def test_wrong_label_prefix():
    t = "\\begin{definitionbox}{D}\n\\begin{definition}[X]\n\\label{thm:x}\nbody\n\\end{definition}\n\\end{definitionbox}"
    assert "wrong_label_prefix" in _codes(dr.run_rules(_block(t), dr.Context()))

def test_dependencies_env_recognized():
    # the canonical \begin{dependencies} environment must satisfy the dependencies check
    t = ("\\begin{lemmabox}{L}\n\\begin{lemma}[X]\n\\label{lem:x}\nbody\n\\end{lemma}\n\\end{lemmabox}\n"
         "\\begin{remark*}[Interpretation]\ny\n\\end{remark*}\n"
         "\\begin{dependencies}\n\\begin{itemize}\\item \\hyperref[def:y]{Y}\\end{itemize}\n\\end{dependencies}")
    assert "missing_dependencies" not in _codes(dr.run_rules(_block(t), dr.Context()))

# ---------- breadcrumb placement (file rules) ----------
CI = dr.FileInfo("vol/bounds/index.tex", "chapter_index")
SN = dr.FileInfo("vol/bounds/notes/sec/notes-sec.tex", "section_note")

def test_bc_valid_heading_then_breadcrumb():
    t = "\\chapter{Bounds}\n\\breadcrumb{bounds}{}{Bounds}{}\n\\section{Intro}\nprose"
    assert dr.run_file_rules(t, CI, dr.Context()) == []

def test_bc_valid_first_no_heading():
    t = "\\label{ch:bounds}\n\\breadcrumb{bounds}{}{Bounds}{}\nbody"
    assert dr.run_file_rules(t, CI, dr.Context()) == []

def test_bc_prose_before_is_not_first():
    t = "\\chapter{Bounds}\nintro prose\n\\breadcrumb{bounds}{}{Bounds}{}"
    assert "breadcrumb_not_first" in _codes(dr.run_file_rules(t, CI, dr.Context()))

def test_bc_exposition_before_flagged_strict():
    t = "\\chapter{Bounds}\n\\begin{exposition}\nx\n\\end{exposition}\n\\breadcrumb{bounds}{}{Bounds}{}"
    assert "breadcrumb_leading_exposition" in _codes(dr.run_file_rules(t, CI, dr.Context()))

def test_bc_exposition_before_ok_when_knob_set():
    t = "\\chapter{Bounds}\n\\begin{exposition}\nx\n\\end{exposition}\n\\breadcrumb{bounds}{}{Bounds}{}"
    assert dr.run_file_rules(t, CI, dr.Context(breadcrumb_max_leading_exposition=1)) == []

def test_bc_missing():
    t = "\\chapter{Bounds}\nno breadcrumb here"
    assert "breadcrumb_missing" in _codes(dr.run_file_rules(t, CI, dr.Context()))

def test_bc_duplicate():
    t = "\\chapter{Bounds}\n\\breadcrumb{b}{}{B}{}\nx\n\\breadcrumb{b}{}{B}{}"
    assert "breadcrumb_duplicate" in _codes(dr.run_file_rules(t, CI, dr.Context()))

def test_bc_misplaced_in_section_note():
    t = "\\subsection{Sup}\n\\breadcrumb{b}{}{B}{}"
    assert "breadcrumb_misplaced" in _codes(dr.run_file_rules(t, SN, dr.Context()))

def test_bc_section_note_clean():
    t = "\\subsection{Sup}\nprose and a definition"
    assert dr.run_file_rules(t, SN, dr.Context()) == []

def test_section_note_top_level_figure_allowed():
    t = "\\subsection{Diagram}\n\\begin{figure}[h]\n\\centering\n\\end{figure}"
    assert "unexpected_top_level_environment" not in _codes(
        dr.run_file_rules(t, SN, dr.Context())
    )

def test_bc_hand_rolled_palette():
    t = "\\chapter{Bounds}\n\\begin{tcolorbox}[colback=breadcrumb,colframe=breadcrumbborder]\nx\n\\end{tcolorbox}"
    assert "breadcrumb_hand_rolled" in _codes(dr.run_file_rules(t, CI, dr.Context()))

# ---------- toolkit placement / content / format ----------
SN2 = dr.FileInfo("vol/bounds/notes/sec/notes-sec.tex", "section_note")

def test_toolkit_valid_after_subsection():
    t = "\\subsection{Open Balls}\n\\begin{toolkitbox}{Toolkit: Open Balls}\norients def:open-ball\n\\end{toolkitbox}"
    assert dr.run_file_rules(t, SN2, dr.Context()) == []

def test_toolkit_valid_one_exposition_between():
    t = ("\\subsection{Open Balls}\n\\begin{exposition}\nwhy balls\n\\end{exposition}\n"
         "\\begin{toolkitbox}{Toolkit}\norients def:open-ball\n\\end{toolkitbox}")
    assert dr.run_file_rules(t, SN2, dr.Context()) == []

def test_toolkit_misplaced_after_section():
    t = "\\section{Topology}\n\\begin{toolkitbox}{Toolkit}\nx\n\\end{toolkitbox}"
    assert "toolkit_misplaced" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

def test_toolkit_misplaced_prose_between():
    t = "\\subsection{Open Balls}\nintro prose\n\\begin{toolkitbox}{Toolkit}\nx\n\\end{toolkitbox}"
    assert "toolkit_misplaced" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

def test_toolkit_too_many_expositions():
    t = ("\\subsection{X}\n\\begin{exposition}\na\n\\end{exposition}\n"
         "\\begin{exposition}\nb\n\\end{exposition}\n\\begin{toolkitbox}{T}\nx\n\\end{toolkitbox}")
    assert "toolkit_leading_exposition" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

def test_toolkit_contains_formal():
    t = ("\\subsection{X}\n\\begin{toolkitbox}{T}\n\\begin{definition}[Y]\n\\label{def:y}\nz\n"
         "\\end{definition}\n\\end{toolkitbox}")
    assert "toolkit_contains_formal" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

def test_toolkit_hand_rolled():
    t = "\\subsection{X}\n\\begin{tcolorbox}[colback=gray!6, title={Toolkit: X}]\nx\n\\end{tcolorbox}"
    assert "toolkit_hand_rolled" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

# ---------- structural roadmap / role purge flags ----------
def test_structural_roadmap_flagged():
    t = "\\subsection*{Structural Roadmap}\nThe global progression is: 1. ... 2. ..."
    codes=_codes(dr.run_file_rules(t, dr.FileInfo("x/index.tex","chapter_index"), dr.Context()))
    assert "structural_roadmap_present" in codes

def test_structural_role_flagged():
    t = "Some prose about the Structural Role of this object."
    assert "structural_role_present" in _codes(dr.run_file_rules(t, SN2, dr.Context()))

def test_no_false_positive_roadmap():
    t = "\\subsection{Open Balls}\nA normal section with no roadmap block."
    codes=_codes(dr.run_file_rules(t, SN2, dr.Context()))
    assert "structural_roadmap_present" not in codes and "structural_role_present" not in codes

# ---------- formal_reading_required ----------
def _fr_ctx():
    return dr.Context(concept_surface_forms=["cauchy sequence","metric space","bounded sequence"])
def _fr_codes(t):
    out=[]
    for b in dr.extract_blocks(t): out += [i.code for i in dr.run_rules(b, _fr_ctx())]
    return set(out)

def test_fr_concept_trigger_without_reading_errors():
    t = "\\begin{lemma}[L]\n\\label{lem:x}\nA Cauchy sequence of real numbers is bounded.\n\\end{lemma}"
    assert "formal_reading_missing" in _fr_codes(t)

def test_fr_with_reading_ok():
    t = ("\\begin{lemma}[L]\n\\label{lem:x}\nA Cauchy sequence of real numbers is bounded.\n\\end{lemma}\n"
         "\\begin{remark*}[Standard quantified statement]\n$x$\n\\end{remark*}")
    assert "formal_reading_missing" not in _fr_codes(t)

def test_fr_logic_word_trigger():
    t = "\\begin{theorem}[T]\n\\label{thm:t}\nFor all $x$ there exists $y$.\n\\end{theorem}"
    assert "formal_reading_missing" in _fr_codes(t)

def test_fr_genuinely_simple_ok():
    t = "\\begin{definition}[N]\n\\label{def:n}\nWe call this object a widget.\n\\end{definition}"
    assert "formal_reading_missing" not in _fr_codes(t)

def test_fr_simple_but_concept_errors():
    t = "\\begin{definition}[D]\n\\label{def:d}\n% lra:simple\nA metric space is the setting.\n\\end{definition}"
    assert "simple_but_triggers" in _fr_codes(t)

def test_fr_wholeword_no_substring_match():
    t = "\\begin{definition}[U]\n\\label{def:u}\nThe staircase is unbounded near the boundary.\n\\end{definition}"
    assert "formal_reading_missing" not in _fr_codes(t)

# ---------- proof_stub_structure_blank ----------
_PI = dr.FileInfo("vol/c/proofs/sec/prf-x.tex", "other")
_PNON = dr.FileInfo("vol/c/notes/sec/notes-sec.tex", "section_note")
_STUB_BLANK = ("\\label{prf:x}\n\\begin{proof}[Professional Standard Proof]\nTODO\n\\end{proof}\n"
    "\\begin{proof}[Detailed Learning Proof]\nTODO\n\\end{proof}\n\\begin{remark*}[Proof structure]\n\n\\end{remark*}\n")
_STUB_FILLED = _STUB_BLANK.replace("[Proof structure]\n\n","[Proof structure]\nThe planned proof uses induction.\n")
_FULL = ("\\label{prf:x}\n\\begin{proof}[Professional Standard Proof]\nReal proof.\n\\end{proof}\n"
    "\\begin{proof}[Detailed Learning Proof]\nReal expanded proof.\n\\end{proof}\n\\begin{remark*}[Proof structure]\nInduction on n.\n\\end{remark*}\n")
def _pcodes(t,info): return {i.code for i in dr.run_file_rules(t,info,dr.Context())}
def test_psb_blank_stub_ok():
    assert "proof_stub_structure_not_blank" not in _pcodes(_STUB_BLANK,_PI)
def test_psb_filled_stub_flagged():
    assert "proof_stub_structure_not_blank" in _pcodes(_STUB_FILLED,_PI)
def test_psb_full_proof_ok():
    assert "proof_stub_structure_not_blank" not in _pcodes(_FULL,_PI)
def test_psb_scoped_to_proof_files():
    assert "proof_stub_structure_not_blank" not in _pcodes(_STUB_FILLED,_PNON)

if __name__ == "__main__":
    tests=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed=0
    for t in tests:
        try: t(); passed+=1; print(f"PASS {t.__name__}")
        except AssertionError as e: print(f"FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    raise SystemExit(0 if passed==len(tests) else 1)
