# Polish Edge Case: Through Coaches

This case study captures a demanding NeTEx scenario: through coaches with
coupling/splitting at transfer hubs, on the night of April 23/24, 2026.
Source data is the provided NeTEx example `wagony_bezposrednie_2026-04-23.xml`,
derived from a MERITS EDIFACT export of 2026-04-21.

## Contents

### Source data
- `wagony_bezposrednie_2026-04-23.xml` — provided NeTEx example
  (derived from a MERITS EDIFACT export of 2026-04-21), used as the canonical input.

### Profiled NeTEx 2.0 (XSD-validated)
- `timetable-profile-standalone-servicejourneys.xml` — full profile of the
  six ServiceJourneys (476, 456, 406, 416, 576, 443) with:
  - opaque stable IDs (`PE:ServiceJourney:sj001` … `sj006`)
  - `privateCodes` (trainNumber, rics) per ServiceJourney and per JourneyPart
  - `JourneyPattern` + `StopPointInJourneyPattern` for every stop
  - `TimetabledPassingTime` referencing SPiJP (with `id`/`version`)
  - `PassengerStopAssignment` mapping every SSP to a Quay
  - `parts` (JourneyParts) after `passingTimes`, in schema order
  - `journeyPartCouples` for the 406+416 coupled section (München→Bohumín)
  - `blocks` (W1–W6) in a `VehicleScheduleFrame` for the through-coach paths
  - `DatedServiceJourney` per `OperatingDay` (2026-04-23)
- `timetable-profile-sj406.xml` — single-service excerpt focused on
  ServiceJourney 406 CHOPIN with three JourneyParts.
- `Locations/locations-profile-v2.0.xml` — SiteFrame with 33 StopPlaces,
  UIC code in `PrivateCode[@type='uicCode']`, coordinates where available,
  and Quay refs.

### Documentation
- `timetable-profile-explanation.md` — design and rationale for explicit
  per-JourneyPart train numbers; current converter behaviour.
- `improvements-identified.md` — list of profile improvements applied.

### Converter pipeline
- `run_conversion.ps1` — reproducible build:
  1. Re-pack `Timetable_profile.zip` and `RailStations_profile.zip`
     from the canonical XML.
  2. Run NeTEx → SKDUPD (`run_conversion.py`).
  3. Run NeTEx → TSDUPD (`netex2tsdupd.py`).
- `ConverterInput/Timetable_profile.zip` — generated.
- `ConverterInput/RailStations_profile.zip` — generated.
- `ConverterOutput/new_SKDUPD.r` — 6 trains, 51 PORs.
- `ConverterOutput/new_TSDUPD.r` — 33 stops with UIC + coordinates.

## Goals (status)

| Component | Status | Notes |
|-----------|--------|-------|
| Locations (StopPlace + Quay) | Profiled | XSD valid; coords for the matched subset |
| Timetable (ServiceJourney) | Profiled | XSD valid; per-part train numbers |
| Through-coach semantics | Profiled | `parts`, `journeyPartCouples`, `blocks` retained |
| SKDUPD output | Generated | 1 PRD per ServiceJourney |
| TSDUPD output | Generated | 33 ALS records (UTF-8 with diacritics) |
| Couples/blocks → EDIFACT | Open | Not yet projected by the converter |

## Reproduce

```powershell
pwsh -File .\run_conversion.ps1
```

Outputs are written to `ConverterOutput\`.

## Validate against NeTEx 2.0 XSD

```powershell
# From the repository root
.\scripts\validate_xml_dotnet.ps1 `
    -XmlPath "CaseStudies\polish_edgecase_ThroughCoaches\timetable-profile-standalone-servicejourneys.xml"

.\scripts\validate_xml_dotnet.ps1 `
    -XmlPath "CaseStudies\polish_edgecase_ThroughCoaches\Locations\locations-profile-v2.0.xml"
```

Both files report `valid=True`, `error_count=0`.
