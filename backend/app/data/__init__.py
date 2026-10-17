"""CareerGraph AI — curated reference data.

This package holds the deterministic, human-curated data sets that power
skill extraction (Phase 3), skill-gap analysis (Phase 4) and the skill
dependency graph (Phase 5).

Data-source policy
------------------
Everything in this package is tagged with a ``source`` field. The value
``"curated"`` means the data was authored/edited by the CareerGraph AI team
as an internal, project-specific taxonomy. It is **not** an official ESCO or
O*NET export, and no official ESCO/O*NET identifiers are invented or claimed.

If real ESCO/O*NET data is later imported, it must be added with its own
explicit source tag and genuine identifiers from the upstream dataset.
"""

DATA_SOURCE_CURATED = "curated"

__all__ = ["DATA_SOURCE_CURATED"]
