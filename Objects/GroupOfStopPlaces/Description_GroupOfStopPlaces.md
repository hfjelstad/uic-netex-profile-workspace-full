# GroupOfStopPlaces

> *→ [Glossary definition](../../Guides/Glossary/Glossary.md#groupofstopplaces)*

## 1. Purpose

A **GroupOfStopPlaces** is a named, purposeful collection of `StopPlace` records that belong together for a specific operational or informational reason — without changing the identity or ownership of the individual `StopPlace` elements. Each member `StopPlace` retains its own `@id`, `@version`, and data ownership; the group is a separate, lightweight overlay.

Two primary use cases apply in the railway context:

| Use case | Example | `PurposeOfGrouping` |
|----------|---------|---------------------|
| **Logical interchange** | Oslo S (rail) + Oslo Bussterminal (bus) form one passenger hub | `interchange` |
| **Regional / country grouping** | All rail stations in Norway grouped for routing, tariff, or ERA reporting | `country` / `region` |

A `GroupOfStopPlaces` may optionally carry an external cross-border identifier via `keyList`, making it a candidate anchor for EU-level station codes without requiring changes to individual national `StopPlace` records.

---

## 2. Structure Overview

```text
GroupOfStopPlaces
 ├─ @id (1..1)
 ├─ @version (1..1)
 ├─ privateCodes (0..1)           ← NeTEx 2.0: replaces deprecated PrivateCode
 │   └─ PrivateCode @type (1..n) ← e.g. type="eraCode", type="uicGroupCode"
 ├─ Name (1..1)
 ├─ ShortName (0..1)
 ├─ Description (0..1)
 ├─ PurposeOfGroupingRef/@ref (0..1)  ← ref to PurposeOfGrouping in ResourceFrame
 ├─ Centroid (0..1)
 │   └─ Location
 │       ├─ Longitude
 │       └─ Latitude
 └─ members (1..1)
     └─ StopPlaceRef (1..n)      ← references to member StopPlace @id
```

---

## 3. Key Elements

- **`@id`**: Unique identifier in the producer's codespace, e.g. `NSR:GroupOfStopPlaces:OsloS` or `ERA:GroupOfStopPlaces:0010002326`.
- **`Name`**: The human-readable name of the group, e.g. `Oslo S interchange` or `Norwegian rail stations`.
- **`PurposeOfGroupingRef/@ref`**: References a `PurposeOfGrouping` object defined in a `ResourceFrame`. `PurposeOfGrouping` is a full NeTEx `TypeOfValue` with its own `@id` and `@version` — not a free-text string. Standardising the available purposes (e.g. `interchange`, `country`, `region`) is a profile decision.
- **`Centroid`**: Optional geographic centre of the group. For interchange groups this is typically the physical hub centre; for regional groups it is informative only.
- **`privateCodes / PrivateCode @type`**: Container for carrying multiple typed external identifiers (NeTEx 2.0, `DataManagedObjectGroup`). Use this when you need more than one code — each `PrivateCode` carries a mandatory `@type` attribute (free text, must be unique within the container). When only one code is needed, the plain `<PrivateCode>` element (without a container) inherited from the base group is still valid in NeTEx 2.0.
- **`members / StopPlaceRef`**: The ordered or unordered list of `StopPlace` records in the group. References must resolve to existing `StopPlace` elements either in the same `SiteFrame` or in a referenced external registry.

---

## 4. Relationship to Other Objects

| Object | Relationship |
|--------|-------------|
| [`StopPlace`](../StopPlace/Description_StopPlace.md) | Member — `StopPlace` records are referenced, not owned, by the group |
| [`PurposeOfGrouping`](../PurposeOfGrouping/Description_PurposeOfGrouping.md) | Classifies the group's intent |
| `TopographicPlace` | A group that corresponds to a city or region may reference the same `TopographicPlace` as its members |

---

## 5. Usage Notes

### 5a. Interchange grouping

An interchange group brings together all `StopPlace` records at a physical hub that serves multiple transport modes or operators. The group does **not** replace the multimodal `StopPlace` parent hierarchy (which models the physical containment of quays); it is an additional logical association for use cases such as journey planning, wayfinding apps, and connection discovery.

```xml
<GroupOfStopPlaces version="1" id="NSR:GroupOfStopPlaces:OsloS">
    <Name>Oslo S — Central Interchange</Name>
    <PurposeOfGroupingRef ref="NSR:PurposeOfGrouping:interchange"/>
    <Centroid>
        <Location>
            <Longitude>10.752245</Longitude>
            <Latitude>59.910924</Latitude>
        </Location>
    </Centroid>
    <members>
        <StopPlaceRef ref="NSR:StopPlace:58366"/>   <!-- Oslo S rail -->
        <StopPlaceRef ref="NSR:StopPlace:59872"/>   <!-- Oslo Bussterminal -->
        <StopPlaceRef ref="NSR:StopPlace:60001"/>   <!-- Oslo S metro -->
    </members>
</GroupOfStopPlaces>
```

### 5b. Cross-border identifier anchor

When a central EU registry assigns an identifier to a logical station that spans multiple national `StopPlace` records (e.g. an ERA code covering the Finnish, Swedish, and Norwegian representations of the same border station), that identifier can be stored on the `GroupOfStopPlaces` via `privateCodes` rather than modifying the national records:

```xml
<GroupOfStopPlaces version="1" id="NSR:GroupOfStopPlaces:Narvik">
    <privateCodes>
        <!-- @type must be unique within this block -->
        <PrivateCode type="eraCode">ERA:station:0076:Narvik</PrivateCode>
    </privateCodes>
    <Name>Narvik</Name>
    <PurposeOfGroupingRef ref="NSR:PurposeOfGrouping:country" version="1"/>
    <members>
        <StopPlaceRef ref="NSR:StopPlace:10042" version="1"/>
    </members>
</GroupOfStopPlaces>
```

> [!NOTE]
> Whether `GroupOfStopPlaces` is the right anchor for a future EU station ID is an **open profile decision** — see Topic 12 in the [European Profile Discussion Agenda](../../Guides/UIC_EDIFACT_Migration/European_Profile_Discussion_Agenda.md).

### 5c. Regional grouping

For country- or region-level aggregation (e.g. for ERA reporting, national routing tables, or tariff attribution), `GroupOfStopPlaces` with a `country` or `region` purpose groups all relevant stations:

```xml
<GroupOfStopPlaces version="1" id="ERA:GroupOfStopPlaces:FI">
    <Name>Finnish rail stations</Name>
    <PurposeOfGroupingRef ref="ERA:PurposeOfGrouping:country"/>
    <members>
        <StopPlaceRef ref="VR:StopPlace:001002326"/>  <!-- Helsinki -->
        <StopPlaceRef ref="VR:StopPlace:001000010"/>  <!-- Pasila -->
        <!-- ... all Finnish rail stations ... -->
    </members>
</GroupOfStopPlaces>
```

### 5d. Consistency rules

- A `StopPlace` may belong to multiple groups with different purposes (e.g. both an interchange group and a country group).
- `StopPlaceRef` elements must resolve to real `StopPlace` objects. References to external registries should omit `@version`.
- The group's `@id` codespace should reflect the organisation responsible for maintaining the group (e.g. `NSR` for national stop registry groups, `ERA` for European-level groups).

---

## 6. Additional Information

See [Table_GroupOfStopPlaces.md](Table_GroupOfStopPlaces.md) for full attribute specifications.  
Example XML: [Example_GroupOfStopPlaces_NP.xml](Example_GroupOfStopPlaces_NP.xml)  
Contained in: [`SiteFrame`](../../Frames/SiteFrame/Description_SiteFrame.md) → `groupsOfStopPlaces`.
