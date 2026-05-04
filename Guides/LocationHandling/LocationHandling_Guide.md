# 📍 Location Handling Guide

## 1. 🎯 Introduction

Every NeTEx delivery that involves stop locations — whether TSDUPD (station publication) or SKDUPD (timetable) — depends on one thing being consistently true: every stop can be uniquely identified by a stable, internationally recognised code. In the UIC EDIFACT world, that code is the **9-digit UIC station number**, and in NeTEx it lives in `privateCodes/PrivateCode[@type='uicCode']`.

This guide establishes the profile requirement, explains the format, and defines the delivery contract so that SKDUPD can be published independently when no station changes have occurred.

> [!NOTE]
> `privateCodes/PrivateCode[@type='uicCode']` is an **intermediate form**. The long-term direction is that downstream systems resolve stops via the stable NeTEx `id` (`NSR:StopPlace:59977`) directly, at which point the UIC code becomes a display attribute rather than the interoperability key. See the [Stable Identity Guide](../StableIdentity/StableIdentity_Guide.md) for the full architectural rationale.

In this guide you will learn:
- 🎯 Why `privateCodes/PrivateCode[@type='uicCode']` is mandatory in this profile
- 🧩 The 9-digit UIC format and how to read it
- 🗂️ The delivery contract between TSDUPD and SKDUPD
- 📝 Common mistakes and how to avoid them

---

## 2. 🧠 Core Concepts

### The location identity requirement

A StopPlace without a resolvable UIC code is invisible to MERITS EDIFACT consumers. The TSDUPD converter skips stops with no UIC. The SKDUPD converter emits a POR row with a blank UIC field, which downstream consumers cannot process.

The rule is simple:

> Every `StopPlace` used in a timetable or station delivery **must** carry a `privateCodes/PrivateCode[@type='uicCode']` containing a valid full 9-digit UIC station number.

This is not a NeTEx XSD requirement — it is a **profile requirement** of this data contract. Without it, the conversion pipeline has no basis for UIC assignment and the EDIFACT output is incomplete.

### The 9-digit UIC format

UIC station numbers in the MERITS world use a fixed **9-digit zero-padded** format.

```
007600100
││└──────── Station number (5 digits)
│└────────── Country code (76 = Norway)
└─────────── Leading zero padding (to reach 9 digits)
```

**Oslo S — `007600100`** is the canonical example used throughout this profile:

| Part | Value | Meaning |
|---|---|---|
| `00` | Padding | Leading zeros to reach the 9-digit form |
| `76` | Country | Norway (UIC country code) |
| `00100` | Station | Oslo S |

> [!NOTE]
> The 7-digit short form (`7600100`) is sometimes seen in legacy databases. Always normalise to 9 digits with leading zeros before publishing (`7600100` → `007600100`). The profile requires the full 9-digit value in `privateCodes/PrivateCode[@type='uicCode']` — no normalisation is done by the converter.

### Why the typed container form is required

NeTEx v2.0 introduced `privateCodes` as a typed, multi-code container. The profile mandates this form for three reasons:

1. **Unambiguous type**: `@type='uicCode'` makes the code system explicit, not implied.
2. **Multi-code support**: The same StopPlace can carry `uicCode`, `reservationCode`, `eraCode` in the same container without collision.
3. **Converter reliability**: The converters resolve UIC exclusively via `privateCodes/PrivateCode[@type='uicCode']`. Any StopPlace without this element will produce no UIC output.

```mermaid
flowchart LR
    SP["StopPlace"] --> PC["privateCodes"]
    PC --> U["PrivateCode @type=uicCode\n007600100"]
    PC --> R["PrivateCode @type=reservationCode\n(optional)"]
    PC --> E["PrivateCode @type=eraCode\n(optional)"]

    style SP fill:#0D47A1,stroke:#0D47A1,color:#fff
    style PC fill:#1565C0,stroke:#1565C0,color:#fff
    style U fill:#1976D2,stroke:#1976D2,color:#fff
    style R fill:#42A5F5,stroke:#42A5F5,color:#fff
    style E fill:#42A5F5,stroke:#42A5F5,color:#fff
```

---

## 3. 🧭 How It Works In NeTEx

### Required structure

Every StopPlace in a profile-compliant SiteFrame must include:

```xml
<StopPlace id="NSR:StopPlace:59977" version="1">
  <privateCodes>
    <PrivateCode type="uicCode">007600100</PrivateCode>
  </privateCodes>
  <Name lang="nor">Oslo S</Name>
  <TransportMode>rail</TransportMode>
</StopPlace>
```

The `privateCodes` container is declared `0..1` in XSD but is **1..1 in this profile** for any StopPlace that participates in a TSDUPD or SKDUPD delivery.

> [!NOTE]
> **Quay-level identity is out of scope for `uicCode`.** UIC numbers identify *stations*, not platforms. A `Quay` must therefore not carry `privateCodes/PrivateCode[@type='uicCode']`. Platform-level identity belongs in a dedicated platform code (future profile extension); today, platform information is only carried per departure.

### Resolution chain in SKDUPD conversion

The converter uses `uicCode` as the anchor for the entire stop-time resolution chain:

```mermaid
flowchart LR
    SSP["ScheduledStopPoint"] -->|PassengerStopAssignment| Q["Quay"]
    Q -->|parent| SP["StopPlace"]
    SP -->|privateCodes/PrivateCode\n@type='uicCode'| UIC["007600100"]
    UIC --> POR["POR.uic"]

    style SSP fill:#0D47A1,stroke:#0D47A1,color:#fff
    style Q fill:#1565C0,stroke:#1565C0,color:#fff
    style SP fill:#1976D2,stroke:#1976D2,color:#fff
    style UIC fill:#1E88E5,stroke:#1E88E5,color:#fff
    style POR fill:#42A5F5,stroke:#42A5F5,color:#fff
```

A break anywhere in this chain — missing PassengerStopAssignment, missing Quay, or missing UIC code — produces a POR row with a blank UIC. The converter logs this as "stops without UIC" and continues, but the resulting SKDUPD is incomplete for those stops.

### The TSDUPD / SKDUPD delivery contract

TSDUPD and SKDUPD are published independently. The contract is:

**SKDUPD-only delivery is permitted when:**

- Every ScheduledStopPoint referenced in the timetable resolves to a StopPlace UIC that exists in the currently active TSDUPD baseline.
- No new stops or platform changes have been introduced since the last TSDUPD publication.

**A new TSDUPD delivery is required when:**

- A new station is added or renamed.
- A UIC code changes.
- Platform/Quay identity changes.
- Any stop referenced by an upcoming SKDUPD would resolve to a station not in the current baseline.

This makes the UIC code the synchronisation anchor between the two pipelines. As long as the set of UIC codes referenced by SKDUPD is a subset of the published TSDUPD baseline, the two can evolve on independent cadences.

```mermaid
flowchart TD
    Q1{"New stations or\nUIC changes?"}
    Q1 -->|Yes| BOTH["Publish TSDUPD first,\nthen SKDUPD"]
    Q1 -->|No| Q2{"All SKDUPD stops\nin current baseline?"}
    Q2 -->|Yes| SKD["Publish SKDUPD only"]
    Q2 -->|No| BOTH

    style Q1 fill:#1565C0,stroke:#1565C0,color:#fff
    style Q2 fill:#1565C0,stroke:#1565C0,color:#fff
    style BOTH fill:#0D47A1,stroke:#0D47A1,color:#fff
    style SKD fill:#42A5F5,stroke:#42A5F5,color:#fff
```

---

## 4. 🧪 Practical Examples

📄 **Full example:** [Example_LocationHandling.xml](Example_LocationHandling.xml)

### Correct — full 9-digit UIC in typed container

```xml
<StopPlace id="NSR:StopPlace:59977" version="1">
  <privateCodes>
    <!-- Full 9-digit UIC. Padding (00) + Country (76 = Norway) + Station (00100) -->
    <PrivateCode type="uicCode">007600100</PrivateCode>
  </privateCodes>
  <Name lang="nor">Oslo S</Name>
  <TransportMode>rail</TransportMode>
</StopPlace>
```

### ❌ Wrong — 7-digit without leading zeros

```xml
<!-- Missing leading zeros — will not match downstream EDIFACT lookups -->
<PrivateCode type="uicCode">7600100</PrivateCode>
```

### ✅ Full compliant example with optional codes

```xml
<StopPlace id="NSR:StopPlace:59977" version="1">
  <privateCodes>
    <PrivateCode type="uicCode">007600100</PrivateCode>
    <PrivateCode type="reservationCode">OSL</PrivateCode>
  </privateCodes>
  <Name lang="nor">Oslo S</Name>
  <Centroid>
    <Location>
      <Longitude>10.752245</Longitude>
      <Latitude>59.910890</Latitude>
    </Location>
  </Centroid>
  <TransportMode>rail</TransportMode>
  <StopPlaceType>railStation</StopPlaceType>
</StopPlace>
```

---

## 5. ✅ Best Practices

> [!TIP]
> - Always use `privateCodes/PrivateCode[@type='uicCode']` — it is the only supported form.
> - Always use the full 9-digit zero-padded form. Never publish 7-digit values.
> - Treat `uicCode` as the stable identity anchor — do not change it unless the UIC assignment itself has changed.
> - Validate UIC presence and format before delivery (check that all StopPlaces used in timetables have a matching UIC in the station baseline).
> - Keep `reservationCode` and other codes in separate typed entries in the same `privateCodes` container.

> [!WARNING]
> - **7-digit values**: Downstream EDIFACT consumers always expect 9 digits. Short values will not match.
> - **Missing `privateCodes/PrivateCode[@type='uicCode']`**: The converter produces no UIC output for the stop — the resulting SKDUPD or TSDUPD row will be incomplete.
> - **Mismatched baselines**: Publishing SKDUPD against a stale TSDUPD baseline silently produces incomplete POR rows for new stops. Always validate coverage before SKDUPD-only publication.

---

## 6. 🔗 Related Resources

### Guides
- [PrivateCode Type Conventions](../Validation/PrivateCode_Type_Conventions.md) — canonical type token list
- [Stable Identity Guide](../StableIdentity/StableIdentity_Guide.md) — opaque id vs. human-readable codes; long-term direction for stop and service identity
- [TSDUPD Converter Guide](../TSDUPD/TSDUPD_Converter_Guide.md) — how UIC is extracted and published
- [SKDUPD Converter Guide](../SKDUPD/SKDUPD_Converter_Guide.md) — how UIC feeds stop-time records

### Frames and Objects
- [SiteFrame](../../Frames/SiteFrame/Description_SiteFrame.md)
- [StopPlace](../../Objects/StopPlace/Description_StopPlace.md) — full element table
- [Quay](../../Objects/Quay/Description_Quay.md)

### External
- [UIC Station Codes](https://www.uic.org/support/it/article/uic-codes) — UIC station numbering reference
