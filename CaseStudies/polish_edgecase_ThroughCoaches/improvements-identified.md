# Identified Improvements

## 1. Train number changes inside one traveler opportunity

### Problem
Eksemplet modellerer `ServiceJourney` med `JourneyPart`, men uttrykker ikke eksplisitt tognummer per delstrekning. Dette gjør det vanskelig for EDIFACT-konverteren å vite hvilket tognummer som gjelder på hver strekning av en gjennom-togtur.

### Solution Implemented ✅
Profilert TimetableFrame-eksempel som viser:
- **ServiceJourney level**: Stabil identitet (`id="sj:406"`) og navn (`406 CHOPIN`) som passasjeren ser
- **JourneyPart level**: Eksplisitt `<PrivateCode type="trainNumber">` for hver delstrekning
  - `jp:406_part1` (München→Breclav) → Train `406`
  - `jp:406_part2` (Breclav→Bohumín) → Train `406x` (loco-/crewbytte)
  - `jp:406_part3` (Bohumín→Warszawa) → Train `406y` (polsk jernbane)

**File**: `timetable-profile-sj406.xml`

### Pattern
```xml
<ServiceJourney id="sj:406">
  <Name>406 CHOPIN</Name>
  <privateCodes>
    <PrivateCode type="trainNumber">406</PrivateCode>
  </privateCodes>
  <journeyParts>
    <JourneyPart id="jp:406_part1">
      <privateCodes>
        <PrivateCode type="trainNumber">406</PrivateCode>
      </privateCodes>
    </JourneyPart>
    <JourneyPart id="jp:406_part2">
      <privateCodes>
        <PrivateCode type="trainNumber">406x</PrivateCode>
      </privateCodes>
    </JourneyPart>
  </journeyParts>
</ServiceJourney>
```

### Why This Works
1. **Stable Identity**: Passengers book ONE ticket (ServiceJourney 406)
2. **Train Number Transparency**: Crew/systems can extract operational train numbers per leg
3. **EDIFACT Conversion**: Converters can now map each JourneyPart to correct EDIFACT train numbers
4. **Nordic Profile Alignment**: Uses standard NeTEx PrivateCode pattern for extensible attributes

## 2. Location modeling alignment

### Problem
Lokasjoner i eksemplet er i dag representert som `ScheduledStopPoint` med UIC-kode i `id`.

### Solution Implemented ✅
Profilert SiteFrame-eksempel med:
- **Opak, stabil id**: `id="PE:StopPlace:sp001"` (not tied to any real-world code)
- **UIC-kode som PrivateCode**: `<PrivateCode type="uicCode">008020347</PrivateCode>`
- **Coordinates**: Centroid elements populated from OSM Overpass API (18/33 matched)

**File**: `Locations/locations-profile-v2.0.xml`

**Status**: 54.5% coordinate coverage (18/33 stations); see `locations-coordinate-gaps.md` for missing entries.

### Pattern
```xml
<StopPlace id="PE:StopPlace:sp001" version="1">
  <Name>München Hbf</Name>
  <PrivateCode type="uicCode">008020347</PrivateCode>
  <Centroid>
    <Location>
      <Longitude>11.558307</Longitude>
      <Latitude>48.140278</Latitude>
    </Location>
  </Centroid>
</StopPlace>
```
