# 📅 Calendar Guide

## 1. 🎯 Introduction

NeTEx supports several ways of expressing *when* a service runs: explicit calendar dates (`OperatingDay` + `DatedServiceJourney`), repeating day-of-week patterns (`DayType` with `PropertyOfDay`), and compact binary calendars (bitmasks, used in EDIFACT). They look interchangeable on the surface, but they are not symmetric — and the choice of source representation determines what you can produce downstream and what you can preserve over time.

This profile chooses **`DatedServiceJourney` over explicit `OperatingDay`s as the single source of truth**. Every other calendar form is derived. This guide explains why, and what that means in practice.

In this guide you will learn:
- 🎯 Why explicit dates are the only loss-free source representation
- 🔁 Which conversion directions are easy, and which are lossy or ambiguous
- 🧩 How the calendar layer connects to stable identity for `DatedServiceJourney`
- 🗂️ How the profile maps to EDIFACT bitmasks (and why DayType is not used as a source)

---

## 2. 🧠 Core Principle

### Three calendar representations

| Representation | What it stores | Strength | Weakness |
|---|---|---|---|
| **Explicit dates** (`OperatingDay` + `DatedServiceJourney`) | One concrete object per running date | Carries every exception, holiday, ad-hoc cancellation and addition exactly | Verbose; many objects per service |
| **DayType + PropertyOfDay** | Day-of-week / period rules (e.g. "Mon–Fri") | Compact, expressive of intent | Cannot represent date-specific exceptions without auxiliary structures; what counts as a "weekday" depends on the calendar context |
| **Bitmask** (EDIFACT operating-days string) | One bit per day between `first_day` and `last_day` | Tiny on the wire; deterministic | Has no notion of intent, journey identity, or exception semantics — just bits |

### Conversion is asymmetric

The conversions form a one-way ladder:

```
explicit dates  ──(easy, lossless)──►  bitmask
explicit dates  ──(easy, lossless)──►  DayType + PropertyOfDay (when a clean rule actually exists)

bitmask         ──(lossy)──►          explicit dates  (you recover dates, but not journey identity, not intent)
DayType         ──(ambiguous)──►      explicit dates  (you must apply a calendar context, holiday rules, validity period…)
DayType         ──(lossy)──►          bitmask         (you must first materialise to dates, inheriting the ambiguity above)
```

Going **down** the ladder (explicit → derived) is mechanical. Going **up** (derived → explicit) requires either guessing intent or replaying calendar rules that may not be available to the consumer. Once you have published a bitmask or a DayType, you cannot reliably reconstruct the original `DatedServiceJourney` set from it alone.

> [!TIP]
> If the source data is rich, every consumer can have what they need. If the source data is already collapsed, no consumer can recover what was lost. Always model at the highest fidelity available — `DatedServiceJourney` — and let the converters compress.

---

## 3. 🧭 How It Works in This Profile

### `DatedServiceJourney` is the calendar anchor

Each running journey is modelled as one `DatedServiceJourney`, binding a `ServiceJourney` to exactly one `OperatingDay`:

```xml
<OperatingDay id="NP:OperatingDay:20260514" version="1">
  <CalendarDate>2026-05-14</CalendarDate>
</OperatingDay>

<DatedServiceJourney id="VYG:DatedServiceJourney:20260514:R601:1" version="1">
  <ServiceJourneyRef ref="VYG:ServiceJourney:R601-2026-001"/>
  <OperatingDayRef ref="NP:OperatingDay:20260514"/>
</DatedServiceJourney>
```

There is no profile-level use of `DayType` for derivation. `DayType` may exist for descriptive purposes, but the converter pipeline does not consume it.

### Derivation rules used by the converters

| Output | Source | Notes |
|---|---|---|
| EDIFACT bitmask (SKDUPD) | Set of `OperatingDay` dates resolved from `DatedServiceJourney` | Bit *n* = 1 iff `first_day + n` is in the date set |
| `DayType` + `PropertyOfDay` (optional, descriptive) | Same date set | Only emitted when a clean weekly pattern exists across the validity period; otherwise the date set is left explicit |

The arrows always point **out from** explicit dates, never into them.

### Why this fits the SKDUPD format

EDIFACT SKDUPD encodes operating days as `first_day`, `last_day`, and a binary bitmask between them. That is mechanically a projection of the explicit-date set. See [SKDUPD Converter Guide § 2](../SKDUPD/SKDUPD_Converter_Guide.md) for the conversion details.

---

## 4. 🔗 Calendar Identity And Stable Identity

The calendar layer is also an identity layer. A `DatedServiceJourney` is the long-term replacement for the legacy `TrainNumber + Date` key — and that role only works if its `id` is stable.

The profile rule (see [Stable Identity Guide § 3](../StableIdentity/StableIdentity_Guide.md#datedservicejourney--instance-identity)) is:

> A `DatedServiceJourney` `id` must be stable across re-publications of the same operating day. Real-time, disruption management, reservations, and analytics all reference it.

What this means concretely for calendar handling:

- A re-publication that adds, cancels, or shifts dates **MUST NOT** silently regenerate the `DatedServiceJourney` ids for dates that are unchanged.
- A re-publication that adds a new running date adds a new `DatedServiceJourney` for that date — it does not invalidate the existing ones.
- A cancellation removes the `DatedServiceJourney` (or marks it cancelled), but does not touch the ids of other dates.
- The `ServiceJourney` `id` (the *traveler opportunity*) is also stable across timetable periods. The `DatedServiceJourney` `id` is stable across re-publications within a period. Both layers carry identity, at different scopes.

This is why the profile insists on explicit dates: a bitmask has no identifier per bit, and a DayType has no identifier per materialised date. **Only `DatedServiceJourney` carries the per-instance identity that downstream systems depend on across the lifecycle of a running service.**

> [!NOTE]
> Bitmask and DayType are *delivery formats*. `DatedServiceJourney` is *identity*. Treat them in those roles and the conversion direction follows automatically.

---

## 5. 📝 Practical Examples

📄 **Reference example:** [Example_ServiceCalendarFrame.xml](../../Frames/ServiceCalendarFrame/Example_ServiceCalendarFrame.xml)

### A weekday service with one cancelled date

Source (explicit, in NeTEx):

```xml
<OperatingDay id="NP:OperatingDay:20260518" version="1"><CalendarDate>2026-05-18</CalendarDate></OperatingDay>
<OperatingDay id="NP:OperatingDay:20260519" version="1"><CalendarDate>2026-05-19</CalendarDate></OperatingDay>
<OperatingDay id="NP:OperatingDay:20260520" version="1"><CalendarDate>2026-05-20</CalendarDate></OperatingDay>
<!-- 2026-05-21 deliberately absent: the service does not run that day -->
<OperatingDay id="NP:OperatingDay:20260522" version="1"><CalendarDate>2026-05-22</CalendarDate></OperatingDay>

<DatedServiceJourney id="VYG:DatedServiceJourney:20260518:R601:1" version="1">
  <ServiceJourneyRef ref="VYG:ServiceJourney:R601-2026-001"/>
  <OperatingDayRef ref="NP:OperatingDay:20260518"/>
</DatedServiceJourney>
<!-- …one DSJ per running date… -->
```

Derived bitmask between `first_day=2026-05-18` and `last_day=2026-05-22`:

```
1 1 1 0 1
```

Derived DayType for the same period:

```
"Mon–Fri except 2026-05-21"
```

Note that the DayType form already needs an *exception list*. As soon as exceptions accumulate, the DayType expression stops being a compact win.

### What you cannot do reliably

Going from `11101` back to "the four runs of R601 between 18 and 22 May" is mechanical — **the dates are recoverable, the journey identity is not.** A consumer that only ever saw the bitmask cannot answer "what is the stable id of the run on 2026-05-20?". That answer only exists in the source NeTEx.

And note that even the human-readable label `R601` is not a safe substitute for that identity. The train number is a `PrivateCode` — it can be reassigned for marketing, regulatory, or operational reasons, sometimes mid-season. The legacy `TrainNumber + Date` key inherits that instability: if R601 is renumbered to R603 between publications, every downstream system that keyed on `(R601, 2026-05-20)` loses its handle on the run, even though the run itself did not change. The whole point of `DatedServiceJourney` having a stable opaque `id` is to break this dependency — see [Stable Identity Guide § 3 — ServiceJourney](../StableIdentity/StableIdentity_Guide.md#servicejourney--traveler-opportunity-identity) and the `DatedServiceJourney` section that follows.

So the bitmask loses identity, and the train number was never a stable identity to begin with. `DatedServiceJourney.id` is the only thing that survives both.

---

## 6. ✅ Best Practices

> [!TIP]
> - Model calendar at source as `DatedServiceJourney` + `OperatingDay`, one DSJ per running date.
> - Treat bitmask as an output format, not a storage format.
> - Do not introduce `DayType`-derived calendars into the producer pipeline; they cannot represent exceptions cleanly and they discard per-date identity.
> - Keep `DatedServiceJourney` ids stable across re-publications of the same operating day.
> - When a service runs every day in a period, still emit one `DatedServiceJourney` per date. Do not "compress" at source.
> - When a date is cancelled, remove or cancel the `DatedServiceJourney` for that date. Do not silently re-mint ids for the remaining dates.

❌ Avoid:
- Using `DayType` as the source of truth for which dates a service runs.
- Re-deriving `DatedServiceJourney` ids on every publication.
- Treating the EDIFACT bitmask as the canonical calendar — it is a delivery encoding only.

---

## 7. 🔗 Related Resources

### Guides
- [Stable Identity Guide](../StableIdentity/StableIdentity_Guide.md) — `DatedServiceJourney` id stability across re-publications
- [SKDUPD Converter Guide](../SKDUPD/SKDUPD_Converter_Guide.md) — how the bitmask is built from the explicit date set
- [Get Started Guide](../GetStarted/GetStarted_Guide.md) — frame layout including `ServiceCalendarFrame` and `TimetableFrame`
- [Glossary](../Glossary/Glossary.md) — `OperatingDay`, `DatedServiceJourney`, `DayType`

### Frames & Objects
- [ServiceCalendarFrame](../../Frames/ServiceCalendarFrame/Description_ServiceCalendarFrame.md)
- [TimetableFrame](../../Frames/TimetableFrame/Description_TimetableFrame.md)
- [DatedServiceJourney](../../Objects/DatedServiceJourney/Description_DatedServiceJourney.md)
- [ServiceJourney](../../Objects/ServiceJourney/Description_ServiceJourney.md)
- [OperatingDay](../../Objects/OperatingDay/Description_OperatingDay.md)
