# Key Source Excerpts (MERITS)

Source repository:
- https://github.com/UnionInternationalCheminsdeFer/MERITS-open-source-tools

## A. Definitions expose stable file contracts

From src/merits/skdupd/definition.py (excerpt):

- EDIFACT_FILE_NAME = "SKDUPD.r"
- META_FILE_NAME = "meta.csv"
- ODI_FILE_NAME = "SKDUPD_ODI.csv"
- RELATION_FILE_NAME = "SKDUPD_RELATION.csv"
- POR_FILE_NAME = "SKDUPD_POR.csv"
- TRAIN_FILE_NAME = "SKDUPD_TRAIN.csv"

Why it matters:
- A UIC profile can benefit from similarly explicit canonical file/object contracts.

## B. Mapping logic is centralized

From src/merits/skdupd/csv_handler_to_edifact_collector.py (excerpt):

- "This class contains the mapping from SKDUPD CSV's to EDIFACT."
- Example path writes include:
  - 2_PRD/4_POP/7_POR/8_RFR/RFR
  - 2_PRD/4_POP/7_POR/8_RFR/RLS
  - 2_PRD/4_POP/7_POR/8_RFR/TCE

Why it matters:
- Keep profile-specific business mapping in one deterministic layer.

## C. CLI conversion matrix is explicit

From src/merits/cmd/README.md (excerpt):

- Supports both EDIFACT <-> CSV for SKDUPD and TSDUPD.
- Supports single and multi-file conversion modes.
- Supports zipped CSV mode via --csv-zip.

Why it matters:
- A UIC profile toolchain should support repeatable batch processing and predictable defaults.

## D. Test strategy is contract-driven

From doc/development.md (excerpt):

- Unit tests compare expected and actual artifacts.
- Typical pattern: load fixture -> convert -> write actual -> compare to expected.

Why it matters:
- This is a strong pattern for profile conformance and regression safety.
