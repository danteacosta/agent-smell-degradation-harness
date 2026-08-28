"""T4-only join between pre-final lineage and independently reviewed criteria."""
from __future__ import annotations
from typing import Any, Iterable, Mapping

def join_constraint_lineage_at_t4(lineage: Iterable[Mapping[str, Any]], final_criteria: Mapping[str, str], reference_constraints: Mapping[str, str]) -> list[dict[str, Any]]:
    """Create a label-plane audit view; never import this from feature_plane."""
    joined=[]
    for row in lineage:
        cid=str(row["constraint_id"])
        joined.append({"constraint_id":cid,"pre_final_status":str(row["status"]),"final_criterion":final_criteria.get(cid),"reference_constraint":reference_constraints.get(cid),"plane":"label"})
    return joined
