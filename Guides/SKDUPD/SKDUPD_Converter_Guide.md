# SKDUPD Converter Guide

## 1. 🎯 Introduction

This guide explains the SKDUPD converter as a timetable-focused pipeline: how detailed NeTEx is mapped to EDIFACT, why key profile decisions were made, and what trade-offs are intentional. The goal is not only technical conversion, but controlled semantics where source authorities keep ownership of service identity and day-level operations.

In this guide you will learn:
- 🎯 Why SKDUPD is modelled separately from station publication
- 🧩 How ServiceJourney, JourneyPart, and DatedServiceJourney are transformed
- 🗂️ How operating days are converted to EDIFACT bitmasks
- 📝 Why DatedServiceJourney is required for calendar resolution

> [!NOTE]
> SKDUPD depends on the UIC contract defined in the [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md): every `ScheduledStopPoint` must resolve to a `StopPlace` carrying `privateCodes/PrivateCode[@type='uicCode']` (9-digit). Platform-level changes (new `Quay`, changed `PublicCode`) are carried per departure in SKDUPD and do **not** require a new TSDUPD baseline.

## 2. 🧠 Core Concepts

SKDUPD is a timetable message. It should represent planned operations with minimal semantic loss when moving from NeTEx to EDIFACT.

The converter applies three guiding principles:

1. Preserve source identifiers whenever practical.
2. Prefer explicit date-level data over inferred patterns.
3. Separate structural identity from enrichment.

### DatedServiceJourney requirement for calendar logic

The converter requires DatedServiceJourney and OperatingDay references to construct operating-day bitmasks.

Reasoning:

- DatedServiceJourney → OperatingDay is explicit and deterministic.
- It maps directly to bitmask construction between first_day and last_day.
- The source authority keeps full control over day-level identifiers and exceptions.
- Explicit date-level data is more reliable than inferred patterns.

This is the only supported calendar path; DayType-based derivation is not supported. EDIFACT output is always a binary bitmask string (UIC-specific compact format), never a DayType representation.

```mermaid
flowchart LR
    SJ["ServiceJourney"] --> DSJ["DatedServiceJourney"] --> OD["OperatingDay"] --> BM["Bitmask"] --> TR["SKDUPD TRAIN"]
    style SJ fill:#0D47A1,stroke:#0D47A1,color:#fff
    style DSJ fill:#1565C0,stroke:#1565C0,color:#fff
    style OD fill:#1976D2,stroke:#1976D2,color:#fff
    style BM fill:#1E88E5,stroke:#1E88E5,color:#fff
    style TR fill:#42A5F5,stroke:#42A5F5,color:#fff
```

## 3. 🧭 How It Works In NeTEx

### Domain/Object mapping

| Domain concern | NeTEx source | SKDUPD target |
|---|---|---|
| Train identity | ServiceJourney + TrainNumberRef | TRAIN service number and provider data |
| Stop timing | calls and stop assignments | POR rows with arrival/departure/platform |
| Calendar | DatedServiceJourney + OperatingDay | first_day, last_day, operation_days bitmask |
| Facility/on-demand info | ServiceFacilitySet and refs | ODI-related segments |

### Frame mapping

| Frame | Role in conversion |
|---|---|
| ServiceFrame | Routes, stop topology, assignments |
| TimetableFrame | ServiceJourney, DatedServiceJourney, timing |
| ServiceCalendarFrame | OperatingDay data only |
| ResourceFrame | Operator/provider references |

### Reference pattern used for stop UIC and platform

The converter resolves station/platform context through the chain documented in the [Location Handling Guide — Resolution chain](../LocationHandling/LocationHandling_Guide.md#resolution-chain-in-skdupd-conversion):

ScheduledStopPoint → PassengerStopAssignment → Quay (contained in) StopPlace

(`PassengerStopAssignment` may also resolve directly to a `StopPlace` without a `Quay`.) This yields:

- UIC for POR station identity (from `StopPlace/privateCodes/PrivateCode[@type='uicCode']`)
- Platform public code for arrival/departure platform fields (from `Quay/PublicCode`, when present)

### Converter internals (single-operator path)

In [NeTEx2EDIFACT/netex2skdupd.py](../../NeTEx2EDIFACT/netex2skdupd.py), the conversion logic is implemented around:

- `TimetableData`: parses shared and journey files and builds lookups
- `_build_station_index()`: builds `quay_id -> (uic, platform)` index from station source
- `build_trains_and_pors()`: creates `Meta`, `Train`, and `Por` rows

Detailed train/POR build flow:

1. Read all ServiceJourney elements.
2. Resolve service number from `PrivateCode` (fallback to ServiceJourney id).
3. Resolve provider from `OperatorRef` last segment.
4. Resolve service mode from `TransportSubmode` through `mapping_brand.txt`.
5. Resolve operating dates from `DatedServiceJourney -> OperatingDay` (required).
6. Compute `first_day`, `last_day`, and `operation_days` bitmask.
7. For each TimetabledPassingTime, resolve SPiJP order and map to POR row.

### Converter internals (batch path)

In [NeTEx2EDIFACT/run_conversion.py](../../NeTEx2EDIFACT/run_conversion.py), the batch converter extends this with:

- Auto-discovery of timetable ZIPs in `Source/`
- Global ID offsets across operators
- Facility set resolution for ODI generation (`_resolve_facility_sets()`)
- Optional legacy semantic mode (`--legacy-upload-parity`)

ODI specifics:

- JourneyPart facility values are tokenized (space-separated values split into individual tokens)
- Facilities are mapped through `mapping_facility.txt`
- Brand fallback ODI row is always emitted when brand exists

### Originator semantics (why examples show NSR vs FLB)

`--originator` sets the Meta originator for the whole EDIFACT delivery. It is a publisher identity, not a per-train operator identity.

| Scenario | Recommended originator |
|---|---|
| Single-operator file published by operator | operator code (for example `FLB`) |
| Multi-operator national batch publication | authority/integration owner (for example `NSR`) |
| Local test publication | test publisher code |

Important distinction:

- `originator` -> delivery-level publisher (Meta)
- `service_provider` -> per-train provider resolved from `OperatorRef`

So in a batch run, `originator=NSR` with train providers `FLB`, `NSB`, `VYG`, and others is expected and correct.

## 4. 🧪 Practical Examples

### Single operator direct conversion

```bash
python NeTEx2EDIFACT/netex2skdupd.py \
  --timetable "NeTEx2EDIFACT/Source/flb_2024-12-05T14_37_53.106.zip" \
  --stations "NeTEx2EDIFACT/Source/RailStations_latest.zip" \
  --output "NeTEx2EDIFACT/NEW_SKDUPD/new_SKDUPD.r" \
  --originator FLB
```

### Batch conversion for one combined delivery

```bash
python NeTEx2EDIFACT/run_conversion.py \
  --source-dir "NeTEx2EDIFACT/Source" \
  --stations "NeTEx2EDIFACT/Source/RailStations_latest.zip" \
  --output "NeTEx2EDIFACT/NEW_SKDUPD/new_SKDUPD_batch.r" \
  --originator NSR
```

### Legacy parity mode

```bash
python NeTEx2EDIFACT/run_conversion.py \
  --source-dir "NeTEx2EDIFACT/Source" \
  --stations "NeTEx2EDIFACT/Source/RailStations_latest.zip" \
  --output "NeTEx2EDIFACT/NEW_SKDUPD/new_SKDUPD_batch_legacy.r" \
  --originator NSR \
  --legacy-upload-parity
```

## 4.1. 📊 Before/After: NeTEx to EDIFACT Transformation

### Input: NeTEx ServiceJourney (TimetableFrame)

The converter reads a ServiceJourney with TimetabledPassingTime elements, departure/arrival times, and references to ScheduledStopPoints:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PublicationDelivery>
  <dataObjects>
    <TimetableFrame id="FLB:TF:2026-04-15" version="1">
      
      <!-- Operating days referenced by DatedServiceJourney -->
      <operatingDays>
        <OperatingDay id="FLB:OD:2026-04-15" version="1">
          <CalendarDate>2026-04-15</CalendarDate>
        </OperatingDay>
        <OperatingDay id="FLB:OD:2026-04-16" version="1">
          <CalendarDate>2026-04-16</CalendarDate>
        </OperatingDay>
      </operatingDays>

      <!-- Route structure (stop sequence) -->
      <journeyPatterns>
        <JourneyPattern id="FLB:JP:HE-TU" version="1">
          <RouteRef ref="FLB:Route:HelsinkiTurku" />
          <pointsInSequence>
            <StopPointInJourneyPattern id="FLB:SPIJP:001" order="1" version="1">
              <ScheduledStopPointRef ref="FLB:SSP:HKICC" />
              <ForBoarding>true</ForBoarding>
              <ForAlighting>false</ForAlighting>
            </StopPointInJourneyPattern>
            <StopPointInJourneyPattern id="FLB:SPIJP:002" order="2" version="1">
              <ScheduledStopPointRef ref="FLB:SSP:TURKU" />
              <ForBoarding>false</ForBoarding>
              <ForAlighting>true</ForAlighting>
            </StopPointInJourneyPattern>
          </pointsInSequence>
        </JourneyPattern>
      </journeyPatterns>

      <!-- Timetable for a specific train -->
      <vehicleJourneys>
        <ServiceJourney id="FLB:SJ:EC123" version="1">
          <PrivateCode typeOfCode="SERVICE_NUMBER">123</PrivateCode>
          <OperatorRef ref="FLB:Operator" />
          <JourneyPatternRef ref="FLB:JP:HE-TU" />
          <LineRef ref="FLB:Line:ExpressCoast" />
          <TransportSubmode>internationalTrain</TransportSubmode>
          
          <!-- Individual stop times -->
          <passingTimes>
            <TimetabledPassingTime>
              <StopPointInJourneyPatternRef ref="FLB:SPIJP:001" />
              <DepartureTime>08:00:00</DepartureTime>
            </TimetabledPassingTime>
            <TimetabledPassingTime>
              <StopPointInJourneyPatternRef ref="FLB:SPIJP:002" />
              <ArrivalTime>12:15:00</ArrivalTime>
            </TimetabledPassingTime>
          </passingTimes>
        </ServiceJourney>
      </vehicleJourneys>

      <!-- Calendar mapping: which operating days this train runs on -->
      <datedVehicleJourneys>
        <DatedServiceJourney id="FLB:DSJ:EC123-2026-04-15" version="1">
          <OperatingDayRef ref="FLB:OD:2026-04-15" />
          <ServiceJourneyRef ref="FLB:SJ:EC123" />
        </DatedServiceJourney>
        <DatedServiceJourney id="FLB:DSJ:EC123-2026-04-16" version="1">
          <OperatingDayRef ref="FLB:OD:2026-04-16" />
          <ServiceJourneyRef ref="FLB:SJ:EC123" />
        </DatedServiceJourney>
      </datedVehicleJourneys>
    </TimetableFrame>
  </dataObjects>
</PublicationDelivery>
```

### Output: EDIFACT SKDUPD Message

The converter transforms this NeTEx structure into a flat EDIFACT message with three main parts:

```edifact
UNA:*+.? '
UNB+UNOC:3+FLB+NSR+260415:1200+1'
UNH+1+SKDUPD:D:96A:UN'

# META: Delivery metadata
BGM+315+DELIVERY001++9'
DTM+137:20260415:102'
NAD+MR+FLB'

# TRAIN: First train service (EC123 on 2026-04-15)
TDT+1++123++++8++VR:EC:HLKJ47'
RFF+BN:FLB'
DTM+9:20260415:102'
DTM+10:20260416:102'

# POR: Passage of Record - stops for this train
LOC+9+0001::123:1'
DTM+186:0800:101'
CTA++DF:+0001'

LOC+12+0002::123:1'
DTM+185:1215:101'
CTA++DF:+0002'

# TRAIN: Second train service (EC123 on 2026-04-16)
TDT+2++123++++8++VR:EC:HLKJ48'
RFF+BN:FLB'
DTM+9:20260415:102'
DTM+10:20260416:102'

# POR: Same stops, same times
LOC+9+0001::123:1'
DTM+186:0800:101'
CTA++DF:+0001'

LOC+12+0002::123:1'
DTM+185:1215:101'
CTA++DF:+0002'

UNT+25+1'
UNZ+1+1'
```

### Key Transformation Details

| NeTEx Element | Converter Logic | EDIFACT Output |
|---|---|---|
| **ServiceJourney @id** | PrivateCode (if present) or last segment of id | TRAIN service number (TDT segment) |
| **OperatorRef** | Last segment becomes provider code | RFF:BN segment |
| **DatedServiceJourney + OperatingDay** | Explicit calendar: `first_day`, `last_day`, `operation_days` bitmask | DTM segments (9=from, 10=to, bitmask in MOA) |
| **TimetabledPassingTime** | Order-by-order from JourneyPattern | LOC + DTM rows (one LOC+DTM pair per stop) |
| **ForAlighting / ForBoarding** | Mapped to traffic restriction code (IM) | Implicit in DTM 186/185 (arrival/departure presence) |
| **ScheduledStopPoint + PassengerStopAssignment** | Resolved to UIC code | LOC segment position/UIC value |

### Handling Boarding Restrictions

When a stop has `ForBoarding=false` (alighting only):

**NeTEx:**
```xml
<StopPointInJourneyPattern id="FLB:SPIJP:003" order="3" version="1">
  <ScheduledStopPointRef ref="FLB:SSP:TURKU" />
  <ForBoarding>false</ForBoarding>
  <ForAlighting>true</ForAlighting>
</StopPointInJourneyPattern>
```

**EDIFACT (traffic restriction code):**
```edifact
LOC+12+0003::123:1'
DTM+185:1215:101'
IM+4'  # Traffic restriction: no boarding (code 4)
```

### Handling Request Stops (On-Demand)

When a stop is request-only:

**NeTEx:**
```xml
<StopPointInJourneyPattern id="FLB:SPIJP:004" order="4" version="1">
  <ScheduledStopPointRef ref="FLB:SSP:SMALLSTN" />
  <RequestStop>true</RequestStop>
  <RequestMethod>handSignal</RequestMethod>
</StopPointInJourneyPattern>
```

**EDIFACT:**
```edifact
LOC+9+0004::123:1'
DTM+186:1430:101'
CTA++ZZ:+0004'  # On-demand marker
```

### Design reasoning for ODI handling

ODI generation combines source facility sets and mapping configuration. The converter prefers explicit source semantics and avoids hardcoded business assumptions where data is absent.

Implication:

- You get reliable conversion from available source features.
- You may not reproduce historical enrichments added downstream in external import pipelines.

This is intentional: converter behavior should remain explainable and auditable from source + mapping files.

> [!WARNING]
> If historical reference deliveries contain import-side enrichments not present in current NeTEx source snapshots, exact parity can be impossible. Treat those as external enrichment layers, not converter defects.

## 5. ✅ Best Practices

> [!TIP]
> - Ensure DatedServiceJourney/OperatingDay data is complete and valid; it is required for calendar resolution.
> - Keep station mapping deterministic via shared station ZIP index.
> - Version and review facility mapping files as controlled profile artifacts.
> - Compare generated ODI signatures against reference deliveries to quantify semantic coverage.

> [!TIP]
> For large batch runs, keep operator-level metrics (train count, POR count, unresolved UIC count, ODI count) and monitor trend deltas over time.

## 6. 🔗 Related Resources

### Guides

- [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md) — UIC requirement, resolution chain, TSDUPD/SKDUPD delivery contract
- [Get Started Guide](../GetStarted/GetStarted_Guide.md)
- [Validation Guide](../Validation/Validation.md)
- [Tools Guide](../Tools/Tools_Guide.md)

### Frames and Objects

- [ServiceFrame](../../Frames/ServiceFrame/Description_ServiceFrame.md)
- [TimetableFrame](../../Frames/TimetableFrame/Description_TimetableFrame.md)
- [ServiceCalendarFrame](../../Frames/ServiceCalendarFrame/Description_ServiceCalendarFrame.md)
- [ServiceJourney](../../Objects/ServiceJourney/Description_ServiceJourney.md)
- [DatedServiceJourney](../../Objects/DatedServiceJourney/Description_DatedServiceJourney.md)
- [OperatingDay](../../Objects/OperatingDay/Description_OperatingDay.md)
- [JourneyPattern](../../Objects/JourneyPattern/Description_JourneyPattern.md)

### Converter modules

- [NeTEx2EDIFACT/netex2skdupd.py](../../NeTEx2EDIFACT/netex2skdupd.py)
- [NeTEx2EDIFACT/netex2skdupd_csv.py](../../NeTEx2EDIFACT/netex2skdupd_csv.py)
- [NeTEx2EDIFACT/csv2SKDUPD_merits.py](../../NeTEx2EDIFACT/csv2SKDUPD_merits.py)
- [NeTEx2EDIFACT/run_conversion.py](../../NeTEx2EDIFACT/run_conversion.py)
- [NeTEx2EDIFACT/compare_odi_raw.py](../../NeTEx2EDIFACT/compare_odi_raw.py)
