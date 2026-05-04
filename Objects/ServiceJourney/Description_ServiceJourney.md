# ServiceJourney

> *? [Glossary definition](../../Guides/Glossary/Glossary.md#servicejourney)*

## 1. Purpose

A **ServiceJourney** represents a planned trip in the timetable operating on a recurring schedule. It defines the stop sequence via reference to a JourneyPattern, includes scheduled passing times, and specifies operational details such as operator and days of operation. Unlike DatedServiceJourney, which represents a concrete instance on a specific date, ServiceJourney is the reusable template used across multiple dates via DayType definitions.

## 2. Structure Overview

```text
ServiceJourney
├── 📄 @id (1..1)
├── 📄 @version (1..1)
├── 📁 privateCodes (0..1)
│   └── 📄 PrivateCode @type (1..n)         ← preferred typed-code container (e.g. trainNumber)
├── 📄 PrivateCode (0..1)                    ← legacy single-code pattern (deprecated)
├── 📄 Name (0..1)
├── 📄 Description (0..1)
├── 📄 TransportMode (0..1)
├── 📁 TransportSubmode (0..1)
│   └── 📄 RailSubmode | BusSubmode | …      (single typed child, e.g. nightRail)
├── 📁 dayTypes (0..1)
│   └── 🔗 DayTypeRef/@ref (0..n)
├── 🔗 JourneyPatternRef/@ref (1..1)
├── 🔗 OperatorRef/@ref (0..1)
├── 🔗 LineRef/@ref (0..1)
├── 🔗 FlexibleLineRef/@ref (0..1)
├── 📁 passingTimes (1..1)
│   └── 📄 TimetabledPassingTime (1..n)
│       ├── 🔗 StopPointInJourneyPatternRef/@ref (1..1)
│       ├── 📄 ArrivalTime (0..1)
│       ├── 📄 DepartureTime (0..1)
│       └── 📄 ArrivalDayOffset / DepartureDayOffset (0..1)
├── 📁 keyList (0..1)
│   └── 📄 KeyValue (0..n)
├── 📁 parts (0..1)
└── 🔗 BlockRef/@ref (0..1)
```

## 3. Key Elements

- **@id, @version** – Unique identifier and version label
- **JourneyPatternRef** – Reference to the stop sequence (mandatory; defines which stops are served)
- **passingTimes** – Collection of TimetabledPassingTime with ArrivalTime and DepartureTime for each stop
- **dayTypes** – DayType references specifying on which days the journey normally operates
- **OperatorRef** – Reference to the Operator responsible for this journey
- **LineRef** – Reference to the served Line
- **BlockRef** – Optional reference to a Block/TrainBlock for vehicle continuity
- **privateCodes / PrivateCode @type** – Preferred NeTEx v2.0 carrier for one or more typed internal/external identifiers.

## 4. References

- [JourneyPattern](../JourneyPattern/Table_JourneyPattern.md) – Provides the authoritative stop sequence
- [DayType](../DayType/Table_DayType.md) – Specifies operational days
- [Operator](../Operator/Table_Operator.md) – Identifies the service provider
- [Line](../Line/Table_Line.md) – The public transport line being served
- [DatedServiceJourney](../DatedServiceJourney/Description_DatedServiceJourney.md) – Per-date instances and alterations of this journey
- [Block](../TrainBlock/Table_TrainBlock.md) – Optional vehicle/roster grouping

## 5. Usage Notes

- **Template vs. Instance:** ServiceJourney is the template; DatedServiceJourney represents concrete daily instances.
- **Consistency:** A ServiceJourney must reference exactly one JourneyPattern. The pattern's stop sequence is authoritative.
- **Stop Times:** Each stop in the referenced JourneyPattern must have exactly one TimetabledPassingTime entry with ArrivalTime and/or DepartureTime.
- **Day Governance:** DayType references control on which days the journey operates; per-date deviations belong to DatedServiceJourney.
- **Validation:** Ensure journeyPatternRef, lineRef, and operatorRef are consistent and reference existing objects.

## 6. Additional Information

For a complete list of all elements, attributes, cardinalities, and data types, see [Table — ServiceJourney](Table_ServiceJourney.md).

Example XML: [Example_ServiceJourney.xml](Example_ServiceJourney_NP.xml) and [Example_ServiceJourney_MIN.xml](Example_ServiceJourney_NP.xml)


---

## 7. Converter usage (NeTEx -> EDIFACT)

> [!NOTE]
> The **NeTEx -> EDIFACT converter** treats `ServiceJourney` as the SKDUPD train entity (one `PRD` segment per SJ):
> - `privateCodes/PrivateCode[@type='trainNumber']` -> `PRD` service number (with fallback to legacy direct `<PrivateCode>` and finally the SJ `@id`).
> - `OperatorRef/@ref` (last segment) -> `PRD` service provider via the RICS lookup table.
> - `TransportMode` -> `PRD` service mode (`rail`=37, `bus`=32 ...).
> - `TransportSubmode/RailSubmode` -> `ODI/PDT` brand code via `Configuration/mapping_brand.txt` (e.g. `nightRail` -> 101 - drives MERITS sleeper rules).
> - `TimetabledPassingTime` children -> ordered `POR` segments.
> - Linked via `DatedServiceJourney` to operating dates (POP bitmask).
>
> Journeys with fewer than 2 UIC-resolvable stops are discarded; non-rail modes are skipped for SKDUPD entirely.
