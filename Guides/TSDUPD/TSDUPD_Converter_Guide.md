# TSDUPD Converter Guide

## 1. 🎯 Introduction

This guide explains how the TSDUPD converter works, why specific modelling choices were made, and how NeTEx profile data is transformed into EDIFACT station updates. The focus is separation of concerns: TSDUPD is treated as a station/infrastructure publication, independent from timetable lifecycle complexity.

In this guide you will learn:
- 🎯 Why TSDUPD is separated from SKDUPD in this repository
- 🧩 How station data is extracted from NeTEx SiteFrame
- 🗂️ How UIC, names, and coordinates map into EDIFACT fields
- ⏱️ How per-station Minimum Connection Time (MCT) flows from `SiteConnection` self-loops to `TSDUPD_MCT.csv`
- 📝 Which profile and converter decisions reduce downstream ambiguity

> [!NOTE]
> The UIC requirement, the typed `privateCodes/PrivateCode[@type='uicCode']` form, and the per-station MCT model used by this converter are defined in the [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md). Read that guide first if you need the contract — this guide focuses on how the converter consumes it.

## 2. 🧠 Core Concepts

TSDUPD is a location message. It should answer: where is a stop, what is its identifier, and how is it named? It should not encode timetable semantics.

This separation gives two practical benefits:

- Station data can be republished on its own cadence, without forcing timetable publication.
- Timetable conversion can evolve independently (for example operating-day logic), while station identity remains stable.

### Why separation matters

| Concern | TSDUPD | SKDUPD |
|---|---|---|
| Main purpose | Stop/place identity and geography | Train schedules and operating dates |
| Typical update driver | Stop data change in source registry | New timetable or date updates |
| Primary risk | Identifier inconsistency | Calendar and journey consistency |
| Best publication strategy | Independent and conservative | Frequent and operational |

> [!TIP]
> Keep station publication stable and predictable. Consumers commonly cache TSDUPD longer than timetable payloads.

```mermaid
flowchart LR
    SF["SiteFrame"] --> EX["Station extraction"] --> MAP["UIC and naming mapping"] --> TS["TSDUPD EDIFACT"]
    style SF fill:#0D47A1,stroke:#0D47A1,color:#fff
    style EX fill:#1565C0,stroke:#1565C0,color:#fff
    style MAP fill:#1976D2,stroke:#1976D2,color:#fff
    style TS fill:#42A5F5,stroke:#42A5F5,color:#fff
```

## 3. 🧭 How It Works In NeTEx

The TSDUPD pipeline consumes the station export (NeTEx SiteFrame) and builds station rows for EDIFACT.

### Domain/Object mapping

| Domain concern | NeTEx source | TSDUPD output role |
|---|---|---|
| Station identity | StopPlace | Station record (UIC key, country context) |
| Platform-level artifacts | Quay | Optional enrichment context (not primary station key) |
| Alternative naming | AlternativeName | Synonym rows |
| Coordinates | StopPlace centroid / location | Geographic fields in stop record |

### Frame mapping

| Frame | Why used |
|---|---|
| SiteFrame | Authoritative place infrastructure and naming |
| CompositeFrame wrapper | Delivery envelope and structural context |

### UIC resolution (required format)

The converter requires UIC codes to be carried in `privateCodes/PrivateCode[@type='uicCode']` with the full 9-digit format. This is the single supported path — no fallbacks.

**Why:** Station identity is the foundation of TSDUPD. Enforcing a single, well-formed path ensures data quality and consistency across all producers.

> [!WARNING]
> Missing or malformed UIC codes (wrong format or missing privateCodes) will cause station records to be skipped. Verify UIC resolution before publishing.

### Converter internals (what actually happens in code)

The direct TSDUPD converter in [NeTEx2EDIFACT/netex2tsdupd.py](../../NeTEx2EDIFACT/netex2tsdupd.py) follows a strict sequence:

1. Parse SiteFrame XML and iterate all StopPlace nodes.
2. Resolve UIC using `_uic_code()` with ordered fallback logic.
3. Resolve reservation code (if present) using `_reservation_code()`.
4. Resolve centroid coordinates using `_coordinates()`.
5. Resolve validity period using `_validity()`.
6. Build MERITS dataclasses:
   - `Meta`
   - `Stop`
   - `Synonym`
7. Serialize through `RowsInMemory` and MERITS `CsvsToEdifact`.

Key implementation decisions:

- Rows with missing UIC are skipped, because UIC is the station identity key.
- Country is derived from UIC prefix (`uic[:2]`) to avoid duplicate source dependency.
- `Mct` and `Footpath` tables are emitted as empty rows unless modelled in source.

### Originator semantics (why examples used NSR)

`--originator` writes the EDIFACT Meta originator field. In these guides, `NSR` was used because the source registry context here is NSR/Entur.

Use this rule:

| Scenario | Recommended originator |
|---|---|
| Official authority publication from NSR pipeline | `NSR` |
| Publication by another data owner/infrastructure authority | that authority code |
| Local test run | your test publisher code |

> [!NOTE]
> `originator` identifies the publisher of the message, not the operator of each train service (that distinction is mainly relevant in SKDUPD).

## 4. 🧪 Practical Examples

### Direct conversion (SiteFrame XML -> EDIFACT)

```bash
python NeTEx2EDIFACT/netex2tsdupd.py \
  --input "Nordic source material/tiamat-export-RailStations-202604262300285592.xml" \
  --output "NeTEx2EDIFACT/NEW_TSDUPD/new_TSDUPD.r" \
  --originator NSR
```

### CSV intermediate flow (inspect before final EDIFACT)

```bash
python NeTEx2EDIFACT/netex2tsdupd_csv.py \
  --input "Nordic source material/tiamat-export-RailStations-202604262300285592.xml" \
  --csv-dir "NeTEx2EDIFACT/CSV" \
  --originator NSR

python NeTEx2EDIFACT/csv2TSDUPD.py \
  --csv-dir "NeTEx2EDIFACT/CSV" \
  --output "NeTEx2EDIFACT/NEW_TSDUPD/new_TSDUPD.r"
```

### If your source is a ZIP export

The TSDUPD scripts consume XML. If you receive a ZIP export, extract the SiteFrame XML first, then pass that XML file to `--input`.

```mermaid
flowchart LR
    Z["Station ZIP"] --> X["Extract SiteFrame XML"] --> C["netex2tsdupd.py"] --> R["TSDUPD .r"]
    style Z fill:#0D47A1,stroke:#0D47A1,color:#fff
    style X fill:#1565C0,stroke:#1565C0,color:#fff
    style C fill:#1976D2,stroke:#1976D2,color:#fff
    style R fill:#42A5F5,stroke:#42A5F5,color:#fff
```

### Reasoning behind CSV intermediate support

The CSV stage is kept for quality control and profile governance:

- You can verify UIC uniqueness before delivery.
- You can inspect synonym coverage and language quality.
- You can compare source registry changes over time.

This is especially useful for authority workflows where station data stewardship is organizationally separate from timetable production.

## 4.1. 📊 Before/After: NeTEx to EDIFACT Station Transformation

### Input: NeTEx SiteFrame (StopPlace Data)

The converter reads a SiteFrame with StopPlace definitions, UIC codes, coordinates, and alternative names:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PublicationDelivery>
  <dataObjects>
    <SiteFrame id="NSR:SF:2026-04-15" version="1">
      
      <stopPlaces>
        <StopPlace id="NSR:StopPlace:0011" version="1">
          <Name>Helsinki Central Station</Name>
          <Centroid>
            <Location>
              <Longitude>24.9428</Longitude>
              <Latitude>60.1719</Latitude>
            </Location>
          </Centroid>
          <privateCodes>
            <PrivateCode type="uicCode">6000087</PrivateCode>
          </privateCodes>
          <alternativeNames>
            <AlternativeName>
              <Name>Helsingin päärautatieasema</Name>
              <NameType>official</NameType>
            </AlternativeName>
            <AlternativeName>
              <Name>Centralstationen</Name>
              <NameType>alias</NameType>
            </AlternativeName>
          </alternativeNames>
          <quays>
            <Quay id="NSR:Quay:0011-1" version="1">
              <Name>Platform 1</Name>
              <PublicCode>1</PublicCode>
            </Quay>
            <Quay id="NSR:Quay:0011-2" version="1">
              <Name>Platform 2</Name>
              <PublicCode>2</PublicCode>
            </Quay>
          </quays>
        </StopPlace>

        <StopPlace id="NSR:StopPlace:0021" version="1">
          <Name>Turku Central Station</Name>
          <Centroid>
            <Location>
              <Longitude>22.2712</Longitude>
              <Latitude>60.4295</Latitude>
            </Location>
          </Centroid>
          <privateCodes>
            <PrivateCode type="uicCode">6001316</PrivateCode>
          </privateCodes>
          <alternativeNames>
            <AlternativeName>
              <Name>Turun päärautatieasema</Name>
              <NameType>official</NameType>
            </AlternativeName>
          </alternativeNames>
        </StopPlace>

        <StopPlace id="NSR:StopPlace:0099" version="1">
          <Name>Small Station</Name>
          <Centroid>
            <Location>
              <Longitude>25.1234</Longitude>
              <Latitude>60.5678</Latitude>
            </Location>
          </Centroid>
          <privateCodes>
            <PrivateCode type="uicCode">6012345</PrivateCode>
          </privateCodes>
        </StopPlace>
      </stopPlaces>

    </SiteFrame>
  </dataObjects>
</PublicationDelivery>
```

### Output: EDIFACT TSDUPD Message

The converter transforms the StopPlace hierarchy into a flat station-focused EDIFACT message:

```edifact
UNA:*+.? '
UNB+UNOC:3+NSR+NSR+260415:1200+1'
UNH+1+TSDUPD:D:96A:UN'

# META: Delivery metadata
BGM+320+DELIVERY001++9'
DTM+137:20260415:102'
NAD+MR+NSR'

# LOC: Station records
LOC+4+6000087++++++++24.9428'
LOC+4+6000087++++++++60.1719'
CTA++FC'

# SYN: Synonym records (alternative names)
SYN+Helsinki Central Station+EN'
SYN+Helsingin päärautatieasema+FI'
SYN+Centralstationen+SV'

# Next station
LOC+4+6001316++++++++22.2712'
LOC+4+6001316++++++++60.4295'
CTA++FC'

SYN+Turku Central Station+EN'
SYN+Turun päärautatieasema+FI'

# Third station (minimal data)
LOC+4+6012345++++++++25.1234'
LOC+4+6012345++++++++60.5678'
CTA++FC'

SYN+Small Station+EN'

UNT+17+1'
UNZ+1+1'
```

### Key Transformation Details

| NeTEx Element | Converter Logic | EDIFACT Output |
|---|---|---|
| **StopPlace @id** | StopPlace identifier (internal tracking) | Not directly in output; UIC is the key |
| **privateCodes/PrivateCode[@type='uicCode']** | 9-digit UIC code extraction (required) | LOC segment, UIC field |
| **Name** | Primary stop name | SYN segment, default language |
| **alternativeNames** | Language-tagged synonyms | SYN segment per name + language tag |
| **Centroid / Location** | Longitude, latitude | LOC segments for coordinates |
| **Quays** | Optional context (platforms) | Not emitted; used for resolution only |

### Handling Missing UIC (Data Quality)

Stops without proper UIC codes are **skipped with a warning**:

**NeTEx (problematic):**
```xml
<StopPlace id="NSR:StopPlace:0050" version="1">
  <Name>Invalid Station</Name>
  <!-- Missing privateCodes/PrivateCode[@type='uicCode'] -->
</StopPlace>
```

**Converter Behavior:**
```
⚠️  Skipping StopPlace NSR:StopPlace:0050: UIC code not found or malformed
```

**Remedy:**
- Add the missing UIC code as `<PrivateCode type="uicCode">XXXXXXXXX</PrivateCode>`
- Ensure the 9-digit format is correct (example: 6000087)

### Handling Multilingual Names

The converter preserves language diversity in alternative names:

**NeTEx:**
```xml
<alternativeNames>
  <AlternativeName>
    <Name>Gare Centrale de Paris</Name>
    <NameType>official</NameType>
  </AlternativeName>
  <AlternativeName>
    <Name>Pariser Hauptbahnhof</Name>
    <NameType>alias</NameType>
  </AlternativeName>
</alternativeNames>
```

**EDIFACT:**
```edifact
SYN+Gare Centrale de Paris+FR'
SYN+Parizer Hauptbahnhof+DE'
```

Each AlternativeName becomes a separate SYN row. Language tags are derived from the metadata context or file encoding.

### CSV Intermediate Example (for inspection)

When using the `netex2tsdupd_csv.py` workflow, you can inspect the CSV output before EDIFACT generation:

**stops.csv:**
```
id,uic,name,latitude,longitude,country
NSR:StopPlace:0011,6000087,Helsinki Central Station,60.1719,24.9428,FI
NSR:StopPlace:0021,6001316,Turku Central Station,60.4295,22.2712,FI
NSR:StopPlace:0099,6012345,Small Station,60.5678,25.1234,FI
```

**synonyms.csv:**
```
stop_id,name,language
NSR:StopPlace:0011,Helsinki Central Station,EN
NSR:StopPlace:0011,Helsingin päärautatieasema,FI
NSR:StopPlace:0011,Centralstationen,SV
NSR:StopPlace:0021,Turku Central Station,EN
NSR:StopPlace:0021,Turun päärautatieasema,FI
NSR:StopPlace:0099,Small Station,EN
```

This intermediate format allows you to:
- Audit UIC uniqueness across the dataset
- Verify synonym coverage by language
- Detect data quality issues before EDIFACT serialization

### Minimum Connection Time (MCT)

Per-station MCT is published in `TSDUPD_MCT.csv` from `SiteConnection` self-loops. The model and rationale live in the [Location Handling Guide — §4 MCT](../LocationHandling/LocationHandling_Guide.md#4-️-minimum-connection-time-mct); this section shows what the converter consumes and produces.

**NeTEx input** (sibling `ServiceFrame` in the same delivery as the SiteFrame):

```xml
<ServiceFrame id="NSR:ServiceFrame:mct" version="1">
  <connections>
    <SiteConnection id="NSR:SiteConnection:007600100-mct" version="1">
      <Name>MERITS Default Transfer Time</Name>
      <TransferDuration>
        <DefaultDuration>PT8M</DefaultDuration>
      </TransferDuration>
      <BothWays>true</BothWays>
      <From><StopPlaceRef ref="NSR:StopPlace:59977" version="1"/></From>
      <To>  <StopPlaceRef ref="NSR:StopPlace:59977" version="1"/></To>
    </SiteConnection>
  </connections>
</ServiceFrame>
```

**Converter behaviour** — `build_uic_to_mct` walks every `SiteConnection`, keeps only self-loops, parses `TransferDuration/DefaultDuration` as ISO 8601 (`PTnM`), and keys the result by the resolved StopPlace's 9-digit `uicCode`.

**TSDUPD_MCT.csv output:**

```
uic_code;mct_minutes
007600100;8
```

## 5. ✅ Best Practices

> [!TIP]
> - Publish TSDUPD on infrastructure-change events, not timetable events.
> - Treat UIC extraction rules as versioned profile behavior.
> - Keep synonym population deterministic and language-tag aware.
> - Validate station count and identifier uniqueness before export.
> - Prefer the CSV path when onboarding new source feeds.

> [!NOTE]
> TSDUPD deliberately avoids timetable semantics. This keeps message responsibilities clean and reduces accidental coupling between station and journey pipelines.

## 6. 🔗 Related Resources

### Guides

- [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md) — UIC requirement, typed `privateCodes` form, MCT model
- [Get Started Guide](../GetStarted/GetStarted_Guide.md)
- [Validation Guide](../Validation/Validation.md)
- [PrivateCode Type Conventions](../Validation/PrivateCode_Type_Conventions.md)

### Frames and Objects

- [SiteFrame](../../Frames/SiteFrame/Description_SiteFrame.md)
- [StopPlace](../../Objects/StopPlace/Description_StopPlace.md)
- [Quay](../../Objects/Quay/Description_Quay.md)
- [AlternativeName](../../Objects/AlternativeName/Description_AlternativeName.md)

### Converter modules

- [NeTEx2EDIFACT/netex2tsdupd.py](../../NeTEx2EDIFACT/netex2tsdupd.py)
- [NeTEx2EDIFACT/netex2tsdupd_csv.py](../../NeTEx2EDIFACT/netex2tsdupd_csv.py)
- [NeTEx2EDIFACT/csv2TSDUPD.py](../../NeTEx2EDIFACT/csv2TSDUPD.py)
