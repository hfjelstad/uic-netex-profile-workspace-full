# 🔑 Stable Identity Guide

## 1. 🎯 Introduction

NeTEx gives every object a machine identifier (`id`) and a set of human-readable codes (`privateCodes`, `Name`). These are different things, serving different purposes, and the profile treats them accordingly.

This guide explains the separation, why it matters in practice, and what it means concretely for stops, services, and any object that has both a machine reference and a human-facing code.

Profile context:
- Status: UIC NeTEx Profile working guidance for producers and consumers in this repository.
- Scope: identity discipline for location and service objects (`StopPlace`, `ServiceJourney`, `DatedServiceJourney`).
- Non-goals: full identity governance for fare products, organisation master-data, and infrastructure assets. Those are handled in companion object/frame documentation.

In this guide you will learn:
- 🎯 Why `id` must be opaque and stable, independent of all human-readable codes
- 🧩 Where UIC station codes, train numbers, and reservation codes actually belong
- 🗂️ The three-layer model: `id` / `privateCodes` / `Name`
- 📝 The practical consequences for producers and for inter-system references

---

## 2. 🧠 Core Principle

### Human-facing codes are not identifiers

Human-readable codes — train numbers, UIC station codes, reservation codes, commercial service names — are **user interface**. Identifiers are **infrastructure**. Conflating them means every UI or editorial decision becomes an infrastructure migration.

Train numbers get reassigned for marketing reasons. Commercial service codes change when a brand rebrands. Path IDs change when the IM reorganises capacity planning. Station codes change when somebody decides the old code was confusing. None of these are technical changes — they are business or operational decisions made by humans for human reasons. Under a model where the human-readable code *is* the system reference, every one of them ripples through every machine system that referenced the old value.

The correct layering is:

| Layer | Field | Owner | Stability | Purpose |
|---|---|---|---|---|
| Machine identifier | `id` | Authoritative producer | Permanent | Machine references, cross-system linking |
| Human-readable codes | `privateCodes/PrivateCode[@type='…']` | Relevant authority | Changes on editorial decisions | Lookup, display, ticketing, operations |
| Display text | `Name`, `ShortName`, `alternativeNames` | Producer | Changes on editorial decisions | Passenger-facing UI, labels |

The `id` never appears in human contexts. It appears in machine references. Human codes never appear in machine references. The two coexist in the same object, used in different contexts.

### What "opaque and stable" means

**Opaque**: The `id` value carries no semantic content. `NSR:StopPlace:59977` tells a machine nothing about the station it represents — and that is correct. The moment an `id` encodes a code (e.g. `NSR:StopPlace:OsloS` or `NSR:StopPlace:007600100`) it inherits the instability of that code. If the station naming policy changes (for example from OsloS to OsloSentralstasjon), you must either change the `id` and break references, or keep a misleading identifier forever. Consumers may be tempted to parse `id` values to extract meaning (station name, date, operator code), but this is an anti-pattern: treat `id` as an opaque key only, and use explicit fields (`privateCodes`, `Name`, dates, refs) for semantics.

**Stable**: Once minted, an `id` refers to that object permanently, even if everything human-visible about the object changes. If a service is renamed, rebranded, renumbered, or transferred between operators, the `id` does not change. The relationships built on the `id` — bookings, tracking, historical records — survive every editorial change.

---

## 3. 🧭 Application to Specific Object Types

### StopPlace — station identity

The current intermediate state is that UIC station numbers are carried in `privateCodes/PrivateCode[@type='uicCode']`. This is explicitly a bridge: it makes the UIC code findable and typed, so conversion pipelines and MERITS consumers can resolve it, while the stable `id` (`NSR:StopPlace:59977`) is already in place as the long-term machine reference. See the [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md) for the full UIC carrier model and the TSDUPD/SKDUPD delivery contract.

The direction of travel is that downstream EDIFACT consumers, reservation systems, and real-time pipelines progressively learn to resolve against the NeTEx `id` directly — at which point the UIC code in `privateCodes` becomes a display/legacy attribute rather than the interoperability key.

Until then: `privateCodes/PrivateCode[@type='uicCode']` carries the UIC value, `id` carries the stable machine reference.

```xml
<StopPlace id="NSR:StopPlace:59977" version="1">
  <!-- id: opaque, stable, machine reference — never changes -->
  <privateCodes>
    <!-- uicCode: typed human code — changes if UIC reassigns it -->
    <PrivateCode type="uicCode">007600100</PrivateCode>
    <!-- reservationCode: typed human code for booking systems -->
    <PrivateCode type="reservationCode">OSL</PrivateCode>
  </privateCodes>
  <Name lang="nor">Oslo S</Name>
</StopPlace>
```

### ServiceJourney — traveler opportunity identity

A `ServiceJourney` describes a traveler opportunity: the possibility to travel from point A to point Z and remain seated on the same operating service. It has an `id` and typically one or more `PrivateCode` values (for example `trainNumber`, `commercialServiceID`, `pathID`).

By nature it is more editorially unstable than a dated operating instance, and should not be treated as the primary calendar anchor or as the long-term replacement for a `TrainNumber + Date` key.

Current state in many feeds (both fields are volatile in practice):

- The **train number** (`PrivateCode`) changes for marketing, regulatory, or operational reasons — sometimes mid-season.
- The **`id`** itself is regenerated by many operators each timetable period, destroying cross-period continuity.

Target state required by this profile:

- `id` should be kept stable for the same traveler opportunity across timetable periods whenever possible. Structural changes (a service splitting into two, two services merging) are handled with explicit deprecation, not silent reassignment.
- `PrivateCode[@type='trainNumber']` carries the operator-assigned public service number — the human code passengers see on displays and tickets.
- `PrivateCode[@type='commercialServiceID']` carries the commercial branding code if distinct from the train number.
- `PrivateCode[@type='pathID']` carries the IM path/slot identifier if applicable.
- `DatedServiceJourney` is the primary operational identifier in the long run, replacing the legacy habit of identifying runs via `TrainNumber + Date`.

Calendar derivation policy:

- Use `DatedServiceJourney` as the canonical source for operating days and calendar extraction.
- Derive compact bitmask calendars for interchange from that richer dated representation.
- Do not optimize for file size by collapsing source semantics too early. NeTEx is a rich model and should preserve fidelity at source.
- See the [Calendar Guide](../Calendar/Calendar_Guide.md) for the full asymmetry between explicit dates, `DayType`, and bitmask, and why only `DatedServiceJourney` carries per-instance identity.

```xml
<ServiceJourney id="VYG:ServiceJourney:R601-2026-001" version="1">
  <!-- id: stable across rebranding — if R601 becomes R603 next season,
       the id stays and only the PrivateCode changes -->
  <privateCodes>
    <PrivateCode type="trainNumber">R601</PrivateCode>
    <PrivateCode type="commercialServiceID">VY-Bergensbanen-morning</PrivateCode>
  </privateCodes>
  <Name lang="nor">R601 Oslo S – Bergen</Name>
</ServiceJourney>
```

### DatedServiceJourney — instance identity

A `DatedServiceJourney` is the specific run of a `ServiceJourney` on a particular operating day. In this profile, it is the long-term replacement for `TrainNumber + Date` as the primary operational reference. Its `id` must be stable across re-publications of the same timetable period. Real-time systems, disruption management, and historical archives reference `DatedServiceJourney` ids and break if they are regenerated across publications.

Identity scope relationship:
- `ServiceJourney` identity supports continuity of the same traveler opportunity across timetable periods.
- `DatedServiceJourney` identity supports continuity of concrete operations across repeated publications within a period.
- Both layers need stable ids, but for different scopes.

For this profile, `DatedServiceJourney` is the authoritative calendar source because it maps cleanly to bitmask deliveries without information loss:

- `DatedServiceJourney` → bitmask calendar (only output format)

This keeps source data semantically complete while producing compact, deterministic downstream encodings.

Illustrative DSJ identity example:

```xml
<DatedServiceJourney id="VYG:DatedServiceJourney:20260514:R601:1" version="1">
  <ServiceJourneyRef ref="VYG:ServiceJourney:R601-2026-001"/>
  <OperatingDayRef ref="VYG:OperatingDay:2026-05-14"/>
  <!-- Long-term primary operational key: DSJ id (replaces TrainNumber + Date) -->
</DatedServiceJourney>
```

---

## 4. 📐 Profile Requirements

The following are **SHALL** requirements in this profile, not recommendations:

1. **`id` values MUST NOT be derived from any human-readable code** in a way that creates a dependency. `NSR:StopPlace:59977` is correct. `NSR:StopPlace:007600100` is not.

2. **`id` values MUST NOT change when human-readable codes change.** Renaming, rebranding, or renumbering an object is not grounds for reassigning its `id`.

3. **Human-readable codes MUST be carried as typed `privateCodes` entries**, never as the `id` value, never as the primary reference field in cross-system communication.

4. **Inter-system references** (`StopPlaceRef`, `ServiceJourneyRef`, `DatedServiceJourneyRef`, etc.) MUST resolve via `id`. Resolution by `privateCodes` value is a lookup convenience, not a reference mechanism.

5. **Producers MUST maintain `id` stability across timetable periods** for service objects that continue to exist as the same logical service. Structural changes (merge, split) require explicit versioning and deprecation, not silent `id` replacement.

6. **Calendar publication and conversion MUST be anchored in `DatedServiceJourney` semantics.** Bitmask is the derived output format; DatedServiceJourney is the primary truth.

7. **Producers MUST use a collision-safe codespace discipline for ids in shared delivery contexts.** Codespace ownership and identifier ranges must be coordinated so two producers cannot mint the same id for different objects.

8. **`id` and `version` MUST be treated as separate concerns.** Edits increment `version` while keeping `id` stable. Creating a new `id` is a structural identity event, not a normal content update.

9. **Structural identity changes (merge/split/replacement) MUST use an explicit deprecation and replacement policy.** Producers must publish the transition path so consumers can remap references safely.

---

## 5. 🔄 Versioning And Deprecation

Versioning model:
- `id` is the persistent identity key.
- `version` is the revision of that same identity.
- A `version` increment is not a new object identity.

Deprecation model:
- Use deprecation when one logical identity is superseded by another due to structural changes.
- Publish replacement mappings in the same delivery cycle as the new ids.
- Avoid silent id churn; consumers must be able to follow a deterministic migration path.

---

## 6. 🧪 Practical Consequences

### For a reservation system

A booking for "the 08:42 from Oslo to Bergen on 2026-05-14" references a `DatedServiceJourneyRef`. If the operator renumbers the service from R601 to R603 before departure, the booking's reference remains valid — it points to the same `DatedServiceJourney` object, whose `PrivateCode` is updated to R603. The ticket reprint shows R603; the system reference never breaks.

Under a model where the train number *is* the identifier, the renumbering invalidates every booking that referenced the old number.

### For a real-time tracking system

A SIRI ET message tracking a delay references a `DatedServiceJourneyRef`. The IM can reassign the path number mid-day for operational reasons without breaking the real-time chain, because the ET message uses the NeTEx `id`, not the path number.

### For analytics and historical continuity

Year-on-year punctuality trends require that the same logical service has the same identifier across years. With stable opaque `id`, trend lines are continuous across editorial code changes. With code-as-id, every renumbering fragments the time series.

### Example of failure without stable ids

In one typical failure pattern, an operator republishes a timetable where service numbers are renumbered for commercial reasons and ids are regenerated from those numbers. Booking references still point to old ids, real-time events point to new ids, and analytics treat the same service as two unrelated series. The operational cost is duplicate reconciliation logic and manual incident handling that would be unnecessary with stable id discipline.

---

## 7. 💬 Common Push-back

**"But humans need to know what train it is."**  
Yes — that is what `PrivateCode` and `Name` are for. The `id` never appears in passenger-facing contexts.

**"Our existing systems use the train number as the primary key."**  
That is the technical debt this profile helps pay down. New integrations should be built against `id`; existing systems have a clear migration direction.

**"Generating opaque ids is extra work."**  
UUIDs or sequential integers within a codespace cost nothing to generate. The "extra work" is the discipline of not reusing a human code as an identifier — which is exactly the discipline whose absence created the current fragility.

**"How do I debug if ids are opaque?"**  
By joining through to the human-readable codes when you need them, exactly as relational database practitioners have done with surrogate keys for decades.

**"We do not have budget to rework internal systems right now."**  
The profile does not require immediate replacement of internal primary keys. It requires that exported NeTEx data conforms at the boundary. Internal migration can be phased, while boundary mapping enforces stable `id` and typed `privateCodes` now.

**"Our upstream IM/RU supplier emits ids derived from train numbers; we cannot control that."**  
Apply a boundary translation layer: mint stable opaque ids on first ingest, persist the mapping, and reuse those ids on every re-import. Upstream instability is then absorbed once, instead of propagating to all downstream consumers.

---

## 8. 🔗 Related Resources

### Guides
- [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md) — UIC station codes as typed `privateCodes`; the intermediate step toward id-based resolution
- [Calendar Guide](../Calendar/Calendar_Guide.md) — why `DatedServiceJourney` is the only calendar form that carries per-instance identity, and how bitmask/`DayType` are derived from it
- [PrivateCode Type Conventions](../Validation/PrivateCode_Type_Conventions.md) — canonical `@type` token list
- [Glossary](../Glossary/Glossary.md) — definitions for IM, RU, OperatingDay, Codespace, and related terms

Stable id discipline is the foundation that makes typed `privateCodes` and responsibility assignments reliable across publications.

### Objects
- [StopPlace](../../Objects/StopPlace/Description_StopPlace.md)
- [ServiceJourney](../../Objects/ServiceJourney/Description_ServiceJourney.md)
- [DatedServiceJourney](../../Objects/DatedServiceJourney/Description_DatedServiceJourney.md)
- [ResponsibilitySet](../../Objects/ResponsibilitySet/Description_ResponsibilitySet.md)
