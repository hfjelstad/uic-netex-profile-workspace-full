# UIC Profile Extraction Checklist (Nordic-aligned)

Use this checklist to extract reusable design from MERITS into UIC NeTEx profile work.

## A. Structural profile blueprint

1. Lift hierarchy patterns from:
   - src/merits/skdupd/definition.py
   - src/merits/tsdupd/definition.py
2. Define UIC equivalents for:
   - mandatory root/header envelope
   - repeatable service/location groups
   - controlled optionality and multiplicity
3. Document default values separately from source payload values.

## B. Mapping rule layer

1. Mirror MERITS mapping style:
   - input object model -> deterministic output path
2. Keep all profile rules in dedicated mapping modules.
3. Add explicit handling for:
   - relationship semantics
   - time offsets / transfer semantics
   - provider and responsibility fields

## C. Bidirectional conversion strategy

1. Define profile import (external -> canonical model).
2. Define profile export (canonical model -> profile output).
3. Ensure round-trip testability on representative fixtures.

## D. Contract-driven testing

1. Create fixture folders equivalent to tests/EDIFACT_examples.
2. Add tests that compare exact output text/artifacts.
3. Keep expected artifacts versioned; ignore generated actuals where useful.

## E. Tooling workflow

1. Recreate conversion command patterns:
   - single file mode
   - bulk/multi mode
2. Keep defaults explicit and documented.
3. Emit logs and user-friendly validation errors.

## F. Recommended first extraction order

1. README.md and doc/development.md
2. src/merits/skdupd/definition.py
3. src/merits/tsdupd/definition.py
4. src/merits/skdupd/csv_handler_to_edifact_collector.py
5. src/merits/tsdupd/csv_handler_to_edifact_collector.py
6. tests/EDIFACT_examples and tests/merits/*

## Suggested immediate next implementation task

- Create a UIC profile definition module in this workspace that mirrors the MERITS separation of:
  - definition (structure + defaults)
  - mapping handlers
  - conversion entrypoints
  - regression fixtures

## Progress note in this workspace

- Added a new converter script: NeTEx2EDIFACT/csv2TSDUPD.py
- Added output folder: NeTEx2EDIFACT/NEW_TSDUPD/
- Updated usage docs: NeTEx2EDIFACT/README.md
