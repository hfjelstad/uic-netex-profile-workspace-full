# Facility Mapping Guide — ServiceFacilitySet → EDIFACT ASD / SER

## 1. Introduction

This guide explains how on-board service information in NeTEx reaches UIC EDIFACT 916-1 SKDUPD. It covers:

- Where NeTEx facility data lives (`ServiceFacilitySet`)
- How it attaches to a journey at two scopes: whole-train and per-segment
- What EDIFACT segments carry it (`ODI` bracket → `ASD` / `SER`)
- How `mapping_facility.txt` translates NeTEx vocabulary to MERITS codes
- A worked example using real VYG data

---

## 2. The NeTEx Side: ServiceFacilitySet

A `ServiceFacilitySet` is an object that groups together a list of service attributes. A single set might say: *"this part of the journey has economy class seats, snacks, and reservations are recommended."*

The set can be referenced from two places in the journey hierarchy:

### 2a. ServiceJourney level (whole-train scope)

```xml
<ServiceJourney id="VYG:ServiceJourney:60_465604-R">
  <!-- ... passing times ... -->
  <facilities>
    <ServiceFacilitySetRef ref="VYG:ServiceFacilitySet:F4-21" version="0" />
  </facilities>
</ServiceJourney>
```

This covers the entire journey from first to last stop.

### 2b. JourneyPart level (per-segment scope)

```xml
<ServiceJourney id="VYG:ServiceJourney:2502_443759-R">
  <parts>
    <JourneyPart id="VYG:JourneyPart:2502_443759_1">
      <FromStopPointRef ref="VYG:ScheduledStopPoint:BRG-1" />
      <ToStopPointRef ref="VYG:ScheduledStopPoint:ARN-2" />
      <facilities>
        <ServiceFacilitySetRef ref="VYG:ServiceFacilitySet:L4-15" version="0" />
      </facilities>
    </JourneyPart>
  </parts>
</ServiceJourney>
```

`FromStopPointRef` and `ToStopPointRef` define which portion of the train's route the attributes apply to. This is the correct model for through-coach services or trains that change their service level mid-route (e.g. restaurant car detached at a border).

### 2c. ServiceFacilitySet content

```xml
<ServiceFacilitySet id="VYG:ServiceFacilitySet:L4-15">
  <CateringFacilityList>snacks</CateringFacilityList>
  <FareClasses>economyClass</FareClasses>
  <ServiceReservationFacilityList>noReservationsPossible</ServiceReservationFacilityList>
</ServiceFacilitySet>
```

Each child element carries one or more space-separated tokens from the relevant NeTEx enumeration. The converter reads these tokens and maps them via `mapping_facility.txt`.

---

## 3. The EDIFACT Side: ODI Bracket + ASD / SER

In SKDUPD, facility information is attached to a stop-range using the **ODI bracket pattern**:

```
ODI+fromUIC*toUIC+fromSeqNo*toSeqNo'
ASD+code'
```

or for service-type codes:

```
ODI+fromUIC*toUIC+fromSeqNo*toSeqNo'
SER+code'
```

**One code per ODI bracket.** Each attribute gets its own `ODI` line, even when the stop range is the same. This matches MERITS production behaviour.

### 3a. Which segment carries which code list?

| mapping_facility.txt prefix | MERITS code list | EDIFACT segment |
|-----------------------------|------------------|-----------------|
| `S{n}` | 7161 — Special services | `ASD+{n}'` |
| `F{n}` | 9039 — Facility types | `SER+{n}'` |
| `R{n}` | 7037 — Reservation characteristics | `SER+{n}'` |

The `Odi` dataclass field `tff_or_asd_or_ser` uses this same letter convention. The MERITS library (`_handle_odi`) routes `S`-prefixed values to `ASD` and `F`-prefixed values to `SER`.

> [!NOTE]
> Both `F` and `R` codes produce a `SER` segment. The converter translates `R{n}` to the `F{n}` encoding when building `Odi` rows, since that is what the MERITS library expects for SER emission.

### 3b. Stop range in ODI

For a **JourneyPart-level** facility set, the ODI bracket uses the stop sequence numbers corresponding to the JourneyPart's `FromStopPointRef` / `ToStopPointRef`.

For a **ServiceJourney-level** facility set (no JourneyParts), the bracket spans stop 1 to stop N (the full route).

---

## 4. The Mapping File: `mapping_facility.txt`

`Configuration/mapping_facility.txt` maps every NeTEx facility enumeration token to its MERITS code.

Format:

```
netexToken:PrefixCode
```

Examples:

```
freeWifi:S46           # → ASD+46
snacks:S26             # → ASD+26
economyClass:F5        # → SER+5
suitableForWheelchairs:F28   # → SER+28
reservationsRecommended:R14  # → SER+14
reservationsCompulsory:R13   # → SER+13
noReservationsPossible:R19   # → SER+19
```

Inline comments (everything after `#` on a value line) are stripped automatically by the loader.

Tokens with no suitable EDIFACT equivalent are left as comment-only entries with an explanation. Example: `coffeeShop` has no MERITS equivalent.

---

## 5. Worked Example: VYG Bergensbanen (F4)

A Bergensbanen day train (`VYG:ServiceJourney:60_465604-R`) runs Oslo→Bergen (16 stops). It has one JourneyPart covering the whole route with facility set `VYG:ServiceFacilitySet:F4-21`.

**ServiceFacilitySet F4-21 content:**
```xml
<CateringFacilityList>snacks coffeeShop</CateringFacilityList>
<FareClasses>businessClass economyClass</FareClasses>
<MobilityFacilityList>suitableForWheelchairs suitableForPushchairs</MobilityFacilityList>
<LuggageCarriageFacilityList>cyclesAllowed</LuggageCarriageFacilityList>
<PassengerCommsFacilityList>publicWifi</PassengerCommsFacilityList>
<ServiceReservationFacilityList>reservationsRecommended</ServiceReservationFacilityList>
```

**Mapping result:**

| NeTEx token | Mapping | Odi encoding | EDIFACT output |
|-------------|---------|--------------|----------------|
| `snacks` | `S26` | `S26` | `ASD+26'` |
| `coffeeShop` | *(unmapped)* | — | *(omitted)* |
| `businessClass` | `F4` | `F4` | `SER+4'` |
| `economyClass` | `F5` | `F5` | `SER+5'` |
| `suitableForWheelchairs` | `F28` | `F28` | `SER+28'` |
| `suitableForPushchairs` | `F28` | `F28` | *(deduplicated — same code as wheelchair)* |
| `cyclesAllowed` | `F26` | `F26` | `SER+26'` |
| `publicWifi` | `S47` | `S47` | `ASD+47'` |
| `reservationsRecommended` | `R14` | `F14` | `SER+14'` |

**SKDUPD output fragment (stops 1–16):**

```
ODI+007601000*007604300+1*16'
ASD+26'
ODI+007601000*007604300+1*16'
SER+4'
ODI+007601000*007604300+1*16'
SER+5'
ODI+007601000*007604300+1*16'
SER+28'
ODI+007601000*007604300+1*16'
SER+26'
ODI+007601000*007604300+1*16'
ASD+47'
ODI+007601000*007604300+1*16'
SER+14'
```

---

## 6. JourneyPart Scope: Per-Segment Facility Overrides

A through-coach with a restaurant car only on the German leg, and snacks only on the Polish leg, would be modelled as:

```xml
<ServiceJourney id="PKP:ServiceJourney:EC123-R">
  <parts>
    <JourneyPart id="PKP:JourneyPart:EC123_DE">
      <FromStopPointRef ref="PKP:ScheduledStopPoint:HH-1" />
      <ToStopPointRef ref="PKP:ScheduledStopPoint:FRA-1" />
      <facilities>
        <ServiceFacilitySetRef ref="PKP:ServiceFacilitySet:restaurant-leg" />
      </facilities>
    </JourneyPart>
    <JourneyPart id="PKP:JourneyPart:EC123_PL">
      <FromStopPointRef ref="PKP:ScheduledStopPoint:WAW-1" />
      <ToStopPointRef ref="PKP:ScheduledStopPoint:KRK-1" />
      <facilities>
        <ServiceFacilitySetRef ref="PKP:ServiceFacilitySet:snacks-leg" />
      </facilities>
    </JourneyPart>
  </parts>
</ServiceJourney>
```

The converter resolves `FromStopPointRef`/`ToStopPointRef` to the stop sequence numbers within the train's sorted passing-time list, then emits separate ODI brackets for each segment.

**SKDUPD output:**

```
ODI+8001000*8002000+1*5'    ← Hamburg → Frankfurt (stops 1–5)
SER+9'                       ← restaurant car (F9)
ODI+8003000*8004000+6*12'   ← Warsaw → Kraków (stops 6–12)
ASD+26'                      ← snacks (S26)
```

This is the mechanically correct way to reflect partial-route service provision without asserting that the whole train has attributes it only carries on one leg.

---

## 7. Converter Behaviour

### Current implementation

The converter (`netex2skdupd.py`) emits ODI/ASD/SER as follows:

1. **ServiceFacilitySet indexing**: all `ServiceFacilitySet` elements from all files in the timetable ZIP are indexed by `id` during `TimetableData` construction.

2. **Per-SJ emission**: for each `ServiceJourney`, the converter:
   - Finds any `JourneyPart` children (in `<parts>` container) and emits per-range Odi rows for those with a `ServiceFacilitySetRef`
   - Then checks the SJ-level `<facilities>` container for a whole-journey `ServiceFacilitySetRef` and emits stop-1-to-N Odi rows

3. **Deduplication**: within a single `ServiceFacilitySet`, duplicate EDIFACT codes (e.g. `suitableForWheelchairs` and `suitableForPushchairs` both mapping to `F28`) are emitted only once.

4. **Unmapped tokens**: any NeTEx token not in `mapping_facility.txt` is silently skipped.

### Open items

| Item | Status |
|------|--------|
| SJ-level `<facilities>` refs (whole journey) | ✅ Implemented |
| JourneyPart-level `<facilities>` refs (per-segment range) | ✅ Implemented |
| `mapping_facility.txt` inline comment stripping | ✅ Implemented |
| `noReservationsPossible` mapping | ✅ Added |
| SJ-level facility sets when file is treated as "shared" | ⚠️ SJs in the shared file are not iterated — known limitation of the shared-file fallback logic |

---

## 8. Adding New Mappings

To add a new NeTEx token to the mapping:

1. Open `Configuration/mapping_facility.txt`
2. Find the relevant section (CATERING, ACCOMMODATION, etc.)
3. Add a line: `netexToken:PrefixCode  # optional comment`
4. Pick the prefix based on the MERITS code list:
   - `S{n}` for code list 7161 (special services) → will emit `ASD+{n}`
   - `F{n}` for code list 9039 (facility types) → will emit `SER+{n}`
   - `R{n}` for code list 7037 (reservation characteristics) → will emit `SER+{n}`
5. If no suitable EDIFACT code exists, add it as a comment entry with an explanation.

The mapping file is loaded on each converter run — no recompile needed.
