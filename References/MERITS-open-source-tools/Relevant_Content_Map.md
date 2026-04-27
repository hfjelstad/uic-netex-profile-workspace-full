# Relevant Content Map

Repository:
- https://github.com/UnionInternationalCheminsdeFer/MERITS-open-source-tools

## 1) Core format definitions (most useful first)

- src/merits/skdupd/definition.py
  - Why relevant: explicit segment tree and field-level defaults for SKDUPD (service/timetable style data).
  - Reuse idea: use as a pattern for deterministic profile structures and required/optional cardinalities.

- src/merits/tsdupd/definition.py
  - Why relevant: location/footpath/synonym-style structures that map well to station and interchange profile concepts.
  - Reuse idea: model stable, machine-readable profile grammar with explicit node IDs and segment formats.

- src/merits/skdupd/csv_model.py and src/merits/tsdupd/csv_model.py
  - Why relevant: compact row models show normalized payload fields used by conversions.
  - Reuse idea: derive profile-facing tabular extraction contracts from object models first.

## 2) Mapping logic (business rules)

- src/merits/skdupd/csv_handler_to_edifact_collector.py
  - Why relevant: concrete rule mapping from structured rows to EDIFACT segment paths.
  - Reuse idea: replicate this style as NeTEx profile mapping rules from source models to frame/object structures.

- src/merits/tsdupd/csv_handler_to_edifact_collector.py
  - Why relevant: detailed handling of stop/location/timezone/footpath relation logic.
  - Reuse idea: isolate profile-specific transforms in one place and keep converters deterministic.

- src/merits/skdupd/data_handler_to_csv_collector.py and src/merits/tsdupd/data_handler_to_csv_collector.py
  - Why relevant: reverse mapping logic reveals assumptions and edge-case behavior.
  - Reuse idea: design profile ingest/export as bidirectional from day 1.

## 3) Conversion entry points and CLI workflow

- src/merits/skdupd/edifact_to_csvs.py and src/merits/skdupd/csvs_to_edifact.py
- src/merits/tsdupd/edifact_to_csvs.py and src/merits/tsdupd/csvs_to_edifact.py
  - Why relevant: clean top-level conversion interfaces.
  - Reuse idea: expose similarly narrow APIs for profile validation/transformation in UIC tooling.

- src/merits/cmd/arg_definition.py
- src/merits/cmd/worker.py
- src/merits/cmd/main.py
- src/merits/cmd/README.md
  - Why relevant: practical conversion modes, defaults, and multi-file handling.
  - Reuse idea: match this CLI architecture for profile tooling pipelines.

## 4) Generic EDIFACT engine pieces (design inspiration)

- src/merits/edifact/edifact_writer.py
- src/merits/edifact/definition_model.py
- src/merits/edifact/state_machine.py
  - Why relevant: robust format rendering and path/state validation.
  - Reuse idea: build similar strict validation layers for UIC profile conformance checks.

## 5) Tests and fixtures (golden reference behavior)

- tests/EDIFACT_examples/*
  - Why relevant: realistic fixtures for edge cases and baseline expected outputs.

- tests/merits/test_csvs_to_edifact.py
- tests/merits/test_edifact_to_csvs.py
- tests/merits/test_edifact_reader.py
- tests/merits/test_data_helper.py
  - Why relevant: end-to-end test patterns and regression strategy.

## 6) Documentation anchors

- README.md
  - Why relevant: assumptions, limits, and extra specifications.

- doc/development.md
  - Why relevant: architecture, mapping touchpoints, and testing approach.

## Concise excerpts that matter for profile design

- Mapping location from source models to path-based output is centralized in handler classes.
- Format definitions capture both hierarchy and default values.
- Tests compare actual versus expected transformed artifacts as contract tests.
- CLI supports single and multi conversion modes with predictable defaults.
