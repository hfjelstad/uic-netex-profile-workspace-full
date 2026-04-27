<!-- LLM-focused material is documented separately: see LLM/README.md -->

# 🚂 UIC NeTEx Profile

A **working profile** for NeTEx (Network and Timetable Exchange) data in the UIC rail context. This repository defines how to structure, validate, and exchange rail timetable and station data across European systems using NeTEx XML, with conversion tooling to EDIFACT (SKDUPD/TSDUPD).

**Status:** Working guidance for producers and consumers in a European UIC profile context.

---

## 🎯 Quick Start

**Depending on what you're doing:**

| I want to… | Start here |
|---|---|
| **Understand NeTEx basics** | [Get Started Guide](Guides/GetStarted/GetStarted_Guide.md) |
| **Learn about station/stop identity** | [Location Handling Guide](Guides/LocationHandling/LocationHandling_Guide.md) |
| **Learn about stable identifiers** | [Stable Identity Guide](Guides/StableIdentity/StableIdentity_Guide.md) |
| **Convert timetables to SKDUPD** | [SKDUPD Converter Guide](Guides/SKDUPD/SKDUPD_Converter_Guide.md) |
| **Convert stations to TSDUPD** | [TSDUPD Converter Guide](Guides/TSDUPD/TSDUPD_Converter_Guide.md) |
| **Validate XML against schema** | [Validation Guide](Guides/Validation/Validation.md) |
| **Look up a term or concept** | [Glossary](Guides/Glossary/Glossary.md) |

---

## 📚 What This Profile Covers

### ✅ In Scope
- **Station/stop identity:** StopPlace, Quay, and UIC code resolution
- **Timetable structure:** ServiceJourney, DatedServiceJourney, OperatingDay
- **Interchange semantics:** JourneyPattern, stop assignments, timing
- **Identity discipline:** Opaque stable ids + typed privateCodes (not human-readable codes as identifiers)
- **Calendar handling:** DatedServiceJourney-driven, bitmask output
- **Conversion to EDIFACT:** SKDUPD (timetables), TSDUPD (stations)

### ❌ Out of Scope
- Fare products and tariff structures (handled in companion object documentation)
- Organization master-data governance beyond this profile boundary
- Real-time data (covered by SIRI specification)
- Vehicle schedules and block assignments (minimal support)

---

## 🏗️ Repository Structure

```
📁 Guides/
   ├─ GetStarted/              ← Start here if new to NeTEx
   ├─ StableIdentity/          ← Core architectural principle
   ├─ LocationHandling/        ← UIC station codes and privateCodes
   ├─ SKDUPD/                  ← Timetable conversion to EDIFACT
   ├─ TSDUPD/                  ← Station conversion to EDIFACT
   ├─ Validation/              ← XSD validation and checks
   ├─ Glossary/                ← Definitions and terminology
   └─ Tools/                   ← Tool installation and setup

📁 Objects/                    ← Object-level documentation
   ├─ StopPlace/               ← Station definitions
   ├─ ServiceJourney/          ← Timetabled services
   ├─ DatedServiceJourney/     ← Date-specific instances
   ├─ OperatingDay/            ← Calendar dates
   ├─ Quay/                    ← Platform/berth definitions
   ├─ JourneyPattern/          ← Stop sequences
   └─ ... (40+ objects documented)

📁 Frames/                     ← Frame-level reference
   ├─ CompositeFrame/          ← Envelope for all data
   ├─ SiteFrame/               ← Station/infrastructure
   ├─ ServiceFrame/            ← Routes and patterns
   ├─ ServiceCalendarFrame/    ← Operating days
   ├─ TimetableFrame/          ← Journeys and timetables
   ├─ ResourceFrame/           ← Operators and organizations
   └─ FareFrame/               ← Fare products

📁 NeTEx2EDIFACT/             ← Conversion tooling
   ├─ netex2skdupd.py         ← Timetable converter
   ├─ netex2tsdupd.py         ← Station converter
   ├─ run_conversion.py        ← Batch converter
   ├─ Legacy/                  ← Historical converters (reference)
   ├─ scripts/debugging/       ← QA and inspection tools
   └─ README.md                ← Converter documentation

📁 XSD/                       ← NeTEx schema reference
   └─ xsd/                     ← Official CEN schema files
```

---

## 🔑 Key Architectural Decisions

### 1. **Opaque Stable Identifiers**
- `id` is a collision-safe, human-invisible key (e.g. `NSR:StopPlace:59977`)
- Never derived from or dependent on human-readable codes
- Persists unchanged across editorial decisions (renaming, rebranding, renumbering)
- References always resolve via `id`, not by code lookup

**Why:** Decouples identity infrastructure from UI/operational decisions; prevents cascading updates when codes change.

### 2. **Typed Private Codes**
- Human-readable codes live in `privateCodes/PrivateCode[@type='…']`
- Each code type has explicit purpose: `uicCode`, `trainNumber`, `commercialServiceID`, `pathID`, `reservationCode`
- Codes change when business/operational logic changes — `id` does not

**Why:** Clear separation of concerns; enables multi-system lookup without breaking references.

### 3. **DatedServiceJourney as Calendar Truth**
- DatedServiceJourney (concrete date-specific run) is the primary calendar source
- OperatingDay provides explicit calendar dates
- Calendar outputs (bitmask) are derived one-way from DSJ, never reconstructed back
- Simple, deterministic, no ambiguity

**Why:** Explicit > inferred; one-way derivation prevents round-trip loss and semantic drift.

### 4. **Single-Path Identity Resolution**
- UIC codes: `privateCodes/PrivateCode[@type='uicCode']` only (9-digit format)
- No fallbacks to legacy singleton codes or keyList structures
- Enforces data quality; eliminates converter ambiguity

**Why:** Consistency; converters don't need to guess or choose between fallback paths.

### 5. **Bitmask-Only Calendar Output**
- EDIFACT output is pure bitmask (UIC-specific compact format)
- DayType is not emitted (profile-deprecated)
- Deterministic conversion: DSJ → dates → bitmask

**Why:** UIC systems expect bitmask; no feature bloat; minimal options.

---

## 🔄 Conversion Workflow

```
Input: NeTEx XML
       ├─ SiteFrame (stations)
       └─ TimetableFrame (journeys)
              ↓
       Validation (XSD schema)
              ↓
       Converter (netex2skdupd / netex2tsdupd)
              ├─ Extract: UIC codes, journey ids, dates
              ├─ Transform: Apply identity/calendar rules
              └─ Derive: Bitmask calendars, field mappings
              ↓
       Output: EDIFACT (SKDUPD / TSDUPD)
              ├─ TRAIN records (services + operating dates)
              ├─ POR records (stop times + platforms)
              └─ META, ODI records (metadata + facilities)
```

### Running Converters

```bash
# Single operator timetable → SKDUPD
python NeTEx2EDIFACT/netex2skdupd.py \
  --timetable "path/to/timetable.zip" \
  --stations "path/to/stations.zip" \
  --output "output.r" \
  --originator NSR

# Single operator stations → TSDUPD
python NeTEx2EDIFACT/netex2tsdupd.py \
  --input "path/to/stations.zip" \
  --output "output.r" \
  --originator NSR

# Batch: all operators in Source/ → single SKDUPD
python NeTEx2EDIFACT/run_conversion.py \
  --source-dir Source/ \
  --output "output.r" \
  --originator NSR
```

See [NeTEx2EDIFACT/README.md](NeTEx2EDIFACT/README.md) for detailed examples.

---

## 📖 How to Read This Repository

### **For Data Producers** (creating NeTEx files)
1. Start: [Get Started Guide](Guides/GetStarted/GetStarted_Guide.md)
2. Read: [Stable Identity Guide](Guides/StableIdentity/StableIdentity_Guide.md)
3. Read: [Location Handling Guide](Guides/LocationHandling/LocationHandling_Guide.md)
4. Reference: Object descriptions under `Objects/` as needed
5. Validate: [Validation Guide](Guides/Validation/Validation.md)

### **For Data Consumers** (consuming exported files)
1. Start: [Get Started Guide](Guides/GetStarted/GetStarted_Guide.md) to understand structure
2. Reference: [Glossary](Guides/Glossary/Glossary.md) for terms
3. Check: Object descriptions under `Objects/` for specific element details
4. Validate: Use `scripts/validate-xml.sh` to check input files

### **For Converter Operators** (running NeTEx→EDIFACT pipelines)
1. Reference: [SKDUPD Converter Guide](Guides/SKDUPD/SKDUPD_Converter_Guide.md) (timetables)
2. Reference: [TSDUPD Converter Guide](Guides/TSDUPD/TSDUPD_Converter_Guide.md) (stations)
3. Operationalize: [NeTEx2EDIFACT/README.md](NeTEx2EDIFACT/README.md) for CLI usage
4. Debug: Use scripts under `NeTEx2EDIFACT/scripts/debugging/` for QA

### **For System Developers** (integrating with your tools)
1. Understand: [Stable Identity Guide](Guides/StableIdentity/StableIdentity_Guide.md)
2. Reference: Frame and Object documentation for data model
3. Integrate: Use converter as Python library or command-line tool
4. Store: Map stable ids to your internal keys; cache for cross-period continuity

---

## 🧪 Validation

All XML examples in this repository are validated against the official NeTEx schema.

```bash
# Validate all examples
./scripts/validate-xml.sh

# Validate specific file
./scripts/validate-xml.sh Objects/StopPlace/Example_StopPlace_NP.xml
```

Requires `xmllint` (Linux/Mac) or Python `lxml` (Windows). See [Validation Guide](Guides/Validation/Validation.md).

---

## 📋 Profile Requirements & SHALLs

Key normative requirements (SHALL statements):

| Requirement | Where | Impact |
|---|---|---|
| id must be opaque and stable | [StableIdentity](Guides/StableIdentity/StableIdentity_Guide.md#4-profile-requirements) | Structural identity |
| Human codes in privateCodes, not id | [StableIdentity](Guides/StableIdentity/StableIdentity_Guide.md#4-profile-requirements) | Data quality |
| UIC in `privateCodes[@type='uicCode']` | [LocationHandling](Guides/LocationHandling/LocationHandling_Guide.md) | Converter contract |
| Calendar anchored in DatedServiceJourney | [StableIdentity](Guides/StableIdentity/StableIdentity_Guide.md#4-profile-requirements) | Calendar derivation |
| Codespace discipline for shared delivery | [StableIdentity](Guides/StableIdentity/StableIdentity_Guide.md#4-profile-requirements) | ID collision safety |

See individual guides for full requirement sets.

---

## 🔗 Related Resources

- **Official NeTEx Standard:** https://www.netex-cen.eu/
- **Transmodel (Conceptual Model):** https://www.transmodel-cen.eu/
- **MERITS (Conversion Tools):** https://github.com/entur/merits
- **XSD Schema:** [XSD/ folder](XSD/) or https://github.com/NeTEx-CEN/NeTEx

---

## 📝 Contributing & Feedback

This is a **working profile** intended for shared producer/consumer usage. For questions, clarifications, or refinements:

1. Check [Glossary](Guides/Glossary/Glossary.md) for definitions
2. Review relevant guide (e.g., [Stable Identity](Guides/StableIdentity/StableIdentity_Guide.md) for identity questions)
3. Examine examples under `Objects/` or `Frames/`
4. Consult converter README for tool-specific issues

### Profile Evolution
This profile is actively refined based on:
- Converter experience and real-world data challenges
- Feedback from operators and integrators
- Changes in upstream standards (NeTEx CEN, Transmodel)

Last significant updates:
- **2026-04**: Removed DayType fallback; enforced single-path UIC and DSJ-only calendar
- **2026-04**: Expanded StableIdentity guide with organizational objections and edge cases
- **2026-04**: Created LocationHandling guide with 9-digit UIC normalization

---

## ✅ Quick Checklist for Data Producers

Before publishing NeTEx:

- [ ] All StopPlace ids are opaque (e.g. `NSR:StopPlace:59977`, not `NSR:StopPlace:OsloS`)
- [ ] UIC codes in `privateCodes/PrivateCode[@type='uicCode']` (9-digit format, zero-padded)
- [ ] All ServiceJourney ids stable across timetable periods (structural changes have explicit deprecation)
- [ ] DatedServiceJourney entries present for all services (required for calendar resolution)
- [ ] OperatingDay entries for all dates referenced by DatedServiceJourney
- [ ] No DayType references (profile-deprecated; use OperatingDay instead)
- [ ] All id values are globally unique within codespace (collision-safe)
- [ ] Validation passes: `./scripts/validate-xml.sh`

---

## 📞 Questions?

- **Identity questions** → [Stable Identity Guide](Guides/StableIdentity/StableIdentity_Guide.md)
- **Location/UIC questions** → [Location Handling Guide](Guides/LocationHandling/LocationHandling_Guide.md)
- **Converter questions** → [SKDUPD](Guides/SKDUPD/SKDUPD_Converter_Guide.md) or [TSDUPD](Guides/TSDUPD/TSDUPD_Converter_Guide.md) guides
- **Terminology** → [Glossary](Guides/Glossary/Glossary.md)
- **Element details** → Object descriptions under `Objects/`

---

**Last Updated:** April 2026  
**Maintenance:** UIC NeTEx Profile documentation and tooling maintainers
