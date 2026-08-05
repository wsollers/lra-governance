from __future__ import annotations

from pathlib import Path

from tools.governance.index_cpp_objects import build_index
from tools.governance.search_internal_object_index import search_records


def test_indexes_cpp_types_functions_and_comments(tmp_path: Path) -> None:
    root = tmp_path / "lra-nurbs"
    source = root / "src" / "numeric" / "surface.hpp"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace ndde::numeric {

// Evaluates a NURBS surface patch at parameter coordinates.
struct SurfacePatch {
  double weight{};
};

// Compute a basis value for the requested knot span.
[[nodiscard]] double basis_value(int span, double u);

} // namespace ndde::numeric
""",
        encoding="utf-8",
    )

    payload = build_index([root])

    names = {record["name"]: record for record in payload["objects"]}
    assert names["SurfacePatch"]["kind"] == "struct"
    assert names["SurfacePatch"]["declaration"] == "ndde::numeric::SurfacePatch"
    assert "NURBS surface patch" in names["SurfacePatch"]["statement"]
    assert names["basis_value"]["kind"] == "function"
    assert "knot span" in names["basis_value"]["search_text"]


def test_cpp_records_are_searchable_by_ranked_search(tmp_path: Path) -> None:
    root = tmp_path / "lra-numerical-analysis"
    source = root / "include" / "lra" / "numeric" / "interval.hpp"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
namespace lra::numeric {

// Directed rounding real interval enclosure.
class RealInterval {};

} // namespace lra::numeric
""",
        encoding="utf-8",
    )
    payload = build_index([root])

    results = search_records(payload["objects"], "directed rounding interval", source_family="cpp")

    assert results
    assert results[0]["declaration"] == "lra::numeric::RealInterval"
