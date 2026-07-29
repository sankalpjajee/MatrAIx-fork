"""Communication-style narrative must join catalog label + value cleanly."""

from __future__ import annotations

import re

from matraix.agents.persona.loader import load_persona
from matraix.persona_dimension_catalog import build_dimension_narrative


def _find(paragraphs, needle):
    for para in paragraphs:
        if needle in para:
            return para
    return ""


def test_communication_style_uses_label_value_pairs():
    persona = load_persona("persona/datasets/bench-dev-sample/persona_0001.yaml")
    paragraphs = build_dimension_narrative(persona.dimensions)
    style = _find(paragraphs, "My voice")

    assert "verbosity: rambling" in style
    assert "formality: very formal" in style
    assert "directness: indirect" in style
    assert "visual vs verbal thinking: strongly visual" in style
    assert "question-asking: asks often" in style

    # No accidental adjacent-word echoes from "{value} {label}" joins.
    assert re.search(r"\b(\w+)\s+\1\b", style, flags=re.I) is None
    assert "visual visual" not in style
    assert "indirect directness" not in style
    assert "asks often question-asking" not in style


def test_coding_style_paragraph_renders_code_dimensions():
    # code_* dimensions must reach the narrative, else a code-writing task cannot
    # exercise them (the agent would not know how this persona writes code).
    dims = {
        "age_bracket": "25-34",
        "code_comment_style": "Extensive inline comments",
        "code_naming_verbosity": "Single-letter names",
        "code_summary_documentation": "Never includes TLDR",
    }
    paragraphs = build_dimension_narrative(dims)
    coding = _find(paragraphs, "When I write code")

    assert coding, "coding-style paragraph missing when code_* dimensions are present"
    assert "code comment style: extensive inline comments" in coding
    assert "code naming verbosity: single-letter names" in coding
    assert "code summary/tldr documentation: never includes tldr" in coding


def test_no_coding_paragraph_without_code_dimensions():
    dims = {"age_bracket": "25-34", "cog_verbosity": "Terse"}
    paragraphs = build_dimension_narrative(dims)
    assert _find(paragraphs, "When I write code") == ""
