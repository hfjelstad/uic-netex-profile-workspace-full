# TimetableFrame Profile: Train Number Changes Per JourneyPart

**Profile Version**: NeTEx 2.0 (XSD-validated)
**Canonical File**: `timetable-profile-standalone-servicejourneys.xml`

---

## Problem Statement

When modeling through-coach services in NeTEx, we face a unique challenge:

1. **From passenger / sales perspective**: One ticket purchase = one `DatedServiceJourney`
   - "I want to travel from München to Warszawa on service 406 CHOPIN on 2026-04-23"
   - The booking references a `DatedServiceJourneyRef` — the long-term replacement
     for the legacy `TrainNumber + Date` key (see
     [Guides/StableIdentity/StableIdentity_Guide.md](../../Guides/StableIdentity/StableIdentity_Guide.md)).
   - The `ServiceJourney` it instantiates is the reusable **schedule template**.

2. **From operational perspective**: The physical train may change multiple times
   - München→Breclav: Train 406 (German DB loco)
   - Breclav→Bohumín: Train 406x (Czech loco swap)
   - Bohumín→Warszawa: Train 406y (Polish PKP loco)
   - Same **wagon coaches** stay coupled, but **train identity** (tognummer) changes

3. **For EDIFACT converters**: Critical to know which train number applies on each leg
   - Otherwise they cannot generate correct operational schedules
   - May miss loco/crew changes that require advance warnings

---

## Solution: Explicit TrainNumber Per JourneyPart

### Core Pattern (NeTEx 2.0 schema-valid)

Element ordering follows the NeTEx 2.0 `DataManagedObjectGroup`
(`privateCodes` precedes `Name`) and `ServiceJourneyPartsGroup`
(`parts` follows `passingTimes`).

```xml
<ServiceJourney id="PE:ServiceJourney:sj003" version="1">
  <!-- DataManagedObjectGroup: privateCodes BEFORE Name -->
  <privateCodes>
    <PrivateCode type="trainNumber">406</PrivateCode>  <!-- Primary identifier -->
    <PrivateCode type="rics">1251</PrivateCode>        <!-- Operator code -->
  </privateCodes>
  <!-- Stable, passenger-facing identity -->
  <Name>406 CHOPIN</Name>

  <!-- Unified timetable for all passing times (must precede <parts>) -->
  <passingTimes>
    <TimetabledPassingTime id="PE:TimetabledPassingTime:sj003_001" version="1">
      <StopPointInJourneyPatternRef ref="PE:StopPointInJourneyPattern:sj003_001" version="1"/>
      <DepartureTime>18:35:00</DepartureTime>
    </TimetabledPassingTime>
    <!-- ... 9 more stops: München -> ... -> Warszawa Wschodnia -->
  </passingTimes>

  <!-- Three journey segments (parts), AFTER passingTimes -->
  <parts>
    <JourneyPart id="PE:JourneyPart:sj003_p01" version="1">
      <privateCodes>
        <PrivateCode type="trainNumber">406</PrivateCode>
      </privateCodes>
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="PE:ScheduledStopPoint:ssp016"/>  <!-- München -->
      <ToStopPointRef ref="PE:ScheduledStopPoint:ssp007"/>    <!-- Breclav -->
      <StartTime>18:35:00</StartTime>
      <EndTime>00:34:00</EndTime>
    </JourneyPart>

    <JourneyPart id="PE:JourneyPart:sj003_p02" version="1">
      <!-- TRAIN NUMBER CHANGED (new loco/crew) -->
      <privateCodes>
        <PrivateCode type="trainNumber">406x</PrivateCode>
      </privateCodes>
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="PE:ScheduledStopPoint:ssp007"/>  <!-- Breclav -->
      <ToStopPointRef ref="PE:ScheduledStopPoint:ssp020"/>    <!-- Bohumín -->
      <StartTime>00:34:00</StartTime>
      <EndTime>02:55:00</EndTime>
    </JourneyPart>

    <JourneyPart id="PE:JourneyPart:sj003_p03" version="1">
      <!-- FINAL LEG TRAIN NUMBER (Polish railway) -->
      <privateCodes>
        <PrivateCode type="trainNumber">406y</PrivateCode>
      </privateCodes>
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="PE:ScheduledStopPoint:ssp020"/>  <!-- Bohumín -->
      <ToStopPointRef ref="PE:ScheduledStopPoint:ssp023"/>    <!-- Warszawa Wschodnia -->
      <StartTime>03:50:00</StartTime>
      <EndTime>08:23:00</EndTime>
    </JourneyPart>
  </parts>
</ServiceJourney>
```

Coupling between two parallel ServiceJourneys (e.g. 406+416 München→Bohumín)
is expressed in `TimetableFrame/journeyPartCouples`, and through-coach blocks
in `VehicleScheduleFrame/blocks`. See the canonical file for examples.

---

## Why This Approach Works

### 1. Stable Identity Principle
- `DatedServiceJourney` (e.g. `PE:DatedServiceJourney:sj003_20260423`) is the
  **stable sales/operational identifier** that holds bookings — the long-term
  replacement for `TrainNumber + Date`.
- `ServiceJourney` (`PE:ServiceJourney:sj003`) is the reusable **schedule
  template**; its `id` should also be stable across re-publications, but it is
  not what bookings reference.
- Renumbering the train (e.g. 406 → 408) updates the `PrivateCode`/`Name` on
  the SJ/DSJ but does not break the booking's `DatedServiceJourneyRef`.
- Crew/loco swaps within a journey are modelled as `JourneyPart` boundaries
  and never invalidate either identifier.
- See [Guides/StableIdentity/StableIdentity_Guide.md](../../Guides/StableIdentity/StableIdentity_Guide.md)
  for the authoritative profile rules.

### 2. Operational Transparency
- Each JourneyPart explicitly states its train number
- EDIFACT converters can extract `406`, `406x`, `406y` sequentially
- Crew systems know when loco/crew changes occur
- Maintenance systems track which equipment is on which leg

### 3. Schema-aligned
- Uses standard NeTEx `PrivateCode` with `type="trainNumber"`
- All elements ordered per NeTEx 2.0 XSD groups
- No proprietary extensions needed

### 4. Converter-Friendly
- Iterate JourneyParts in `<parts>` order
- Each has clear time window, train number, and `From/ToStopPointRef`
- Couples and blocks reference parts by `JourneyPartRef`

---

## Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| JourneyPart boundaries | At transfer points (Breclav, Bohumín) | Coincides with loco/crew changes |
| Train number source | `PrivateCode[@type='trainNumber']` | Standard NeTEx extension pattern |
| Train number variants | `406`, `406x`, `406y` | Operationally meaningful (German DB, Czech, Polish) |
| Primary train number | At ServiceJourney level + first Part | Supports both UI (service name) and operations |
| Timetable ownership | ServiceJourney-level `passingTimes` | Single unified schedule, not duplicated per part |
| Couples / blocks | `TimetableFrame/journeyPartCouples` and `VehicleScheduleFrame/blocks` | Schema-correct placement in NeTEx 2.0 |

---

## Application Examples

### Use Case 1: Passenger Information System (PIS) / Sales
```
Search:   München -> Warszawa on 2026-04-23
Result:   Service 406 CHOPIN (18:35-08:23)
Booking:  DatedServiceJourneyRef = PE:DatedServiceJourney:sj003_20260423
          (this is what the ticket holds — not the trainNumber + date)
Display:  "Train 406 (München-Wien-Breclav), changes to Train 406x
          (Breclav-Bohumín), then Train 406y (Bohumín-Warszawa)"
```

### Use Case 2: EDIFACT MERITS Converter (current state)
```
Input:  ServiceJourney sj003 with 3 JourneyParts
Today:  Converter emits a single SKDUPD Train per ServiceJourney
        (one PRD + 10 POR records). The per-part train number is
        not yet projected into the EDIFACT output.
Future: Per-part PRD records (or wagon/TCD segments) using
        JourneyPart trainNumber and JourneyPartCouple/Block links.
```

### Use Case 3: Crew Management System
```
Crew assignments derivable from JourneyParts:
  - Munich crew:  sj003 / sj003_p01 (München -> Breclav)
  - Czech crew:   sj003 / sj003_p02 (Breclav -> Bohumín, change at Breclav)
  - Polish crew:  sj003 / sj003_p03 (Bohumín -> Warszawa, change at Bohumín)
```

---

## Relation to Location Profile

This timetable profile works in conjunction with the location profile
(`Locations/locations-profile-v2.0.xml`):

- **References**: `TimetabledPassingTime` references `StopPointInJourneyPattern`,
  which references `ScheduledStopPoint`; `PassengerStopAssignment` then maps
  the SSP to a `Quay` defined in the SiteFrame.
- **Stop Identity**: Stops use opaque IDs (`PE:ScheduledStopPoint:ssp016`,
  `PE:StopPlace:sp016`).
- **UIC code**: Carried in `StopPlace/privateCodes/PrivateCode[@type='uicCode']`.
- **Coordinates**: `Centroid/Location` on `StopPlace` where available.

---

## Validation Status

- Well-formed XML: yes
- NeTEx 2.0 XSD: validated (`valid=True`, `error_count=0`) against
  `XSD/xsd/NeTEx_publication.xsd`.
- Strict-converter prerequisites: present
  (`PassengerStopAssignment`, `JourneyPattern` + `StopPointInJourneyPattern`,
  `TimetabledPassingTime` with `id`/`version`, `DatedServiceJourney` per
  `OperatingDay`).

---

## Open Items

1. **Real-world train numbers**: `406x`, `406y` are placeholders; replace with
   actual numbers from DB/ČD/PKP operational schedules.
2. **EDIFACT projection of through-coaches**: Extend the converter to map
   `JourneyPartCouple` and `Block`/`BlockPart` to the appropriate SKDUPD
   segments (or another MERITS message). Currently these are preserved in
   the NeTEx source but not emitted in `new_SKDUPD.r`.
3. **Notes / availability**: Optional `<Note>` elements explaining loco/crew
   change reasons; `<AvailabilityCondition>` if dwell times vary by date.

---

## References

- **NeTEx Specification**: http://www.netex.org.uk/
- **Original MERITS data**: `wagony_bezposrednie_2026-04-23.xml`
- **Canonical profile output**: `timetable-profile-standalone-servicejourneys.xml`
- **Sub-profile sample**: `timetable-profile-sj406.xml` (single-service excerpt)
