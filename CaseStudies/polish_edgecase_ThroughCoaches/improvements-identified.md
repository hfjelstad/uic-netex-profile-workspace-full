# Identified Improvements

Concrete improvements applied to the source data when producing the
profiled NeTEx 2.0 files in this case study.

## 1. Explicit train number per JourneyPart

**Problem.** The original `wagony_bezposrednie_2026-04-23.xml` models
`ServiceJourney` with `JourneyPart` but does not state the operational
train number per leg. EDIFACT/MERITS consumers cannot tell which train
number applies on each segment of a through-coach service.

**Solution.** Carry train numbers in `privateCodes` at two levels:

- `ServiceJourney`: the passenger-facing primary number (e.g. `406`).
- `JourneyPart`: the per-leg operational number (e.g. `406`, `406x`,
  `406y` across München → Breclav → Bohumín → Warszawa).

```xml
<ServiceJourney id="PE:ServiceJourney:sj003" version="1">
  <privateCodes>
    <PrivateCode type="trainNumber">406</PrivateCode>
    <PrivateCode type="rics">1251</PrivateCode>
  </privateCodes>
  <Name>406 CHOPIN</Name>
  ...
  <parts>
    <JourneyPart id="PE:JourneyPart:sj003_p01" version="1">
      <privateCodes><PrivateCode type="trainNumber">406</PrivateCode></privateCodes>
      ...
    </JourneyPart>
    <JourneyPart id="PE:JourneyPart:sj003_p02" version="1">
      <privateCodes><PrivateCode type="trainNumber">406x</PrivateCode></privateCodes>
      ...
    </JourneyPart>
    <JourneyPart id="PE:JourneyPart:sj003_p03" version="1">
      <privateCodes><PrivateCode type="trainNumber">406y</PrivateCode></privateCodes>
      ...
    </JourneyPart>
  </parts>
</ServiceJourney>
```

See `timetable-profile-explanation.md` for the full rationale.

## 2. Stable, opaque IDs for stops and journeys

**Problem.** The source uses `id="uic:008020347"`, embedding the UIC code
in the identifier. This violates the Stable Identity principle — any
change to the underlying coding system would break references.

**Solution.**

- Stops use opaque IDs (`PE:ScheduledStopPoint:ssp016`,
  `PE:StopPlace:sp016`).
- The UIC code is carried in `privateCodes/PrivateCode[@type='uicCode']`
  on `StopPlace`.
- ServiceJourneys, JourneyParts, JourneyPatterns, BlockParts etc. all
  use the `PE:` codespace prefix with sequential opaque suffixes.

## 3. NeTEx 2.0 schema-correct element ordering

**Problem.** The source mixes element orders that are not valid against
the NeTEx 2.0 XSD (e.g. `journeyParts` placed where the schema expects
`parts`, `PrivateCode` after `Name`).

**Solution.**

- `privateCodes` placed **before** `Name` (DataManagedObjectGroup).
- `parts` placed **after** `passingTimes` (ServiceJourneyPartsGroup).
- `journeyPartCouples` reside in `TimetableFrame`; `blocks` reside in a
  dedicated `VehicleScheduleFrame`.
- `JourneyPartCouple` uses `journeyParts/JourneyPartRef` instead of the
  non-existent `CoupledPartRef`.
- `BlockPart` uses `journeyParts/JourneyPartRef` (the schema choice
  alongside `JourneyPartCoupleRef`).

## 4. Strict-converter prerequisites

**Problem.** The source lacks elements required by the strict
NeTEx → SKDUPD converter (`PassengerStopAssignment`, `JourneyPattern`,
`StopPointInJourneyPattern`, `id`/`version` on `TimetabledPassingTime`,
`DatedServiceJourney` per `OperatingDay`).

**Solution.** All of these are added in the profiled file. The result is
that `run_conversion.ps1` produces:

- `ConverterOutput/new_SKDUPD.r` — 6 trains, 51 POR records.
- `ConverterOutput/new_TSDUPD.r` — 33 stop records with coordinates.

## 5. Source-data correction

`sj006_p02` (train 443) had `ToStopPointRef` pointing to Košice
(`ssp032`); the `EndTime 10:29` and the original timetable confirm
Humenné (`ssp033`). Corrected during the profile build.

## Open items

1. **Real-world train numbers**: `406x`, `406y`, etc. are placeholders;
   replace with actual operational numbers from DB / ČD / PKP.
2. **Couples and blocks → EDIFACT**: the converter currently emits one
   `Train` per `ServiceJourney` and does not project
   `JourneyPartCouple` or `Block`/`BlockPart` to dedicated SKDUPD
   segments. Extending the converter is the next step in this branch.
