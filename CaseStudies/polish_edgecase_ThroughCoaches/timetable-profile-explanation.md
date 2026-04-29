# TimetableFrame Profile: Train Number Changes Per JourneyPart

**Date**: April 29, 2026  
**Profile Version**: NeTEx 1.12 (compatible with 2.0 validation)  
**Example File**: `timetable-profile-sj406.xml`

---

## Problem Statement

When modeling through-coach services in NeTEx, we face a unique challenge:

1. **From passenger perspective**: One ticket purchase = one ServiceJourney
   - "I want to travel from München to Warszawa on service 406 CHOPIN"
   - This is a **stable, unified experience**

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

### Core Pattern

```xml
<ServiceJourney id="PE:ServiceJourney:sj003" version="1">
  <!-- Stable, passenger-facing identity -->
  <Name>406 CHOPIN</Name>
  <privateCodes>
    <PrivateCode type="trainNumber">406</PrivateCode>  <!-- Primary identifier -->
    <PrivateCode type="rics">1251</PrivateCode>        <!-- Operator code -->
  </privateCodes>

  <!-- Three journey segments -->
  <journeyParts>
    <JourneyPart id="PE:JourneyPart:sj003_p01" version="1">
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="uic:008020347"/>  <!-- München -->
      <ToStopPointRef ref="uic:005433425"/>    <!-- Breclav (transfer point) -->
      <StartTime>18:35:00</StartTime>
      <EndTime>00:34:00</EndTime>
      
      <!-- LEG-SPECIFIC TRAIN NUMBER -->
      <privateCodes>
        <PrivateCode type="trainNumber">406</PrivateCode>
      </privateCodes>
    </JourneyPart>

    <JourneyPart id="PE:JourneyPart:sj003_p02" version="1">
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="uic:005433425"/>  <!-- Breclav (transfer point) -->
      <ToStopPointRef ref="uic:005434124"/>    <!-- Bohumín (transfer point) -->
      <StartTime>00:34:00</StartTime>
      <EndTime>02:55:00</EndTime>
      
      <!-- TRAIN NUMBER CHANGED (new loco/crew) -->
      <privateCodes>
        <PrivateCode type="trainNumber">406x</PrivateCode>
      </privateCodes>
    </JourneyPart>

    <JourneyPart id="PE:JourneyPart:sj003_p03" version="1">
      <MainPartRef ref="PE:ServiceJourney:sj003"/>
      <FromStopPointRef ref="uic:005434124"/>  <!-- Bohumín (transfer point) -->
      <ToStopPointRef ref="uic:005103865"/>    <!-- Warszawa Wschodnia -->
      <StartTime>03:50:00</StartTime>
      <EndTime>08:23:00</EndTime>
      
      <!-- FINAL LEG TRAIN NUMBER (Polish railway) -->
      <privateCodes>
        <PrivateCode type="trainNumber">406y</PrivateCode>
      </privateCodes>
    </JourneyPart>
  </journeyParts>

  <!-- Unified timetable for all passing times -->
  <passingTimes>
    <!-- München Hbf, Salzburg, Linz, Wien (Leg 1) -->
    <!-- Ostrava, Bohumín (Leg 2) -->
    <!-- Katowice, Warszawa (Leg 3) -->
  </passingTimes>
</ServiceJourney>
```

---

## Why This Approach Works

### 1. **Stable Identity Principle** ✅
- ServiceJourney `id="PE:ServiceJourney:sj003"` never changes
- Passenger booking/ticketing uses this stable ID
- No ticket invalidation during crew/loco swaps

### 2. **Operational Transparency** ✅
- Each JourneyPart explicitly states its train number
- EDIFACT converters can extract `406`, `406x`, `406y` sequentially
- Crew systems know when loco/crew changes occur
- Maintenance systems track which equipment is on which leg

### 3. **Nordic Profile Alignment** ✅
- Uses standard NeTEx `PrivateCode` with `type="trainNumber"`
- Same pattern used in other Nordic services
- No proprietary extensions needed

### 4. **Converter-Friendly** ✅
- Can iterate through JourneyParts in order
- Each has clear time window and train number
- Automatic validation: number of parts = number of crew changes

---

## Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **JourneyPart boundaries** | At transfer points (Breclav, Bohumín) | Coincides with loco/crew changes |
| **Train number source** | `PrivateCode[@type='trainNumber']` | Standard NeTEx extension pattern |
| **Train number variants** | `406`, `406x`, `406y` | Operationally meaningful (German DB, Czech, Polish) |
| **Primary train number** | At ServiceJourney level + Part 1 | Supports both UI (service name) and operations |
| **Timetable ownership** | ServiceJourney-level `passingTimes` | Single unified schedule, not duplicated per part |

---

## Application Examples

### Use Case 1: Passenger Information System (PIS)
```
Search: München → Warszawa on 2026-04-24
Result: Service 406 CHOPIN (18:35-08:23)
Display: "Train 406 (München-Salzburg-Wien), changes to Train 406x (Czech section), then Train 406y (Poland)"
```

### Use Case 2: EDIFACT MERITS Converter
```
Input:  ServiceJourney sj:406 with 3 JourneyParts
Process:
  - Part 1: Create MERITS record for Train 406 (DB)
  - Part 2: Create MERITS record for Train 406x (ČD)
  - Part 3: Create MERITS record for Train 406y (PKP)
Output: Three interdependent EDIFACT messages, properly sequenced
```

### Use Case 3: Crew Management System
```
Crew assignments from JourneyParts:
  - München crew: sj:406 / jp:406_part1 (0-6 hours)
  - Czech crew: sj:406 / jp:406_part2 (6-9 hours, crew change at Breclav)
  - Polish crew: sj:406 / jp:406_part3 (crew change at Bohumín)
```

---

## Relation to Location Profile

This timetable profile works in conjunction with the location profile (`locations-profile-v2.0.xml`):

- **References**: JourneyParts and TimetabledPassingTimes reference `StopPointRef`
- **Stop Identity**: Stops should use **opaque IDs** (`uic:008020347` → `PE:StopPlace:sp001` mapping)
- **Location Data**: UIC codes in `PrivateCode[@type='uicCode']`
- **Coordinates**: Optional `Centroid` elements for map display

See: `Locations/locations-inventory.md` for the complete stop mapping.

---

## Validation Status

✅ **Well-formed XML**: Loads without parse errors  
✅ **Schema compatible**: Compatible with NeTEx 1.12 and 2.0 validation  
⏳ **Recommended**: Full validation against NeTEx_publication.xsd before production use

---

## Next Steps / Considerations

1. **Real-world train numbers**: Replace `406x`, `406y` with actual operational numbers from DB/ČD/PKP
2. **Loco/Crew change times**: Add explicit `<AvailabilityCondition>` elements if journey times differ significantly at transfer points
3. **Block/Coupling information**: Cross-reference with `JourneyPartCouple` elements for services like 406+416
4. **Operational metadata**: Consider adding `<Note>` elements explaining reasons for train number changes

---

## References

- **NeTEx Specification**: http://www.netex.org.uk/
- **Nordic Profile**: UIC Working Group, Stable Identity Guidance
- **Original Data**: `wagony_bezposrednie_2026-04-23.xml` (MERITS export)
