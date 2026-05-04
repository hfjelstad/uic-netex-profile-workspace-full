# StopPointInJourneyPattern

> *→ [Glossary definition](../../Guides/Glossary/Glossary.md#stoppointinjourneypattern)*

## 1. Purpose

StopPointInJourneyPattern defines a single stop within a JourneyPattern's sequence. It establishes the logical connection between a journey's route (via ScheduledStopPoint) and the access rules (boarding/alighting restrictions) at that specific position in the trip.

---

## 2. Structure Overview

```text
StopPointInJourneyPattern
 ├─ @id (1..1) ..................... Unique identifier
 ├─ @version (1..1) ................ Version label
 ├─ @order (1..1) .................. Position in sequence (1, 2, 3…)
 ├─ 🔗 ScheduledStopPointRef (1..1) .. Link to logical stop
 ├─ ForAlighting (0..1) ............ Allow passengers to exit
 ├─ ForBoarding (0..1) ............. Allow passengers to enter
 ├─ 🔗 DestinationDisplayRef (0..1) . Headsign from this stop
 ├─ RequestStop (0..1) ............. On-demand only?
 ├─ StopUse (0..1) ................. How the stop is used
 ├─ 📁 noticeAssignments (0..1)
 │  └─ NoticeAssignment (0..n) .... Stop-specific notices
 └─ 📁 BookingArrangements (0..1) . Flexible booking rules
```

---

## 3. Key Elements

- **@order** – Position in the journey pattern sequence; used to determine stop-to-stop distance and segment ordering during timetable conversion.
- **ScheduledStopPointRef** – Reference to the logical stop in the network; required to map to physical platforms via PassengerStopAssignment.
- **ForAlighting / ForBoarding** – Access restrictions; combined to determine traffic restriction codes in EDIFACT conversion (e.g., IM code "4" = no boarding/alighting).
- **RequestStop** – Marks on-demand/flag stops where the journey only calls if requested by a passenger or operator.
- **DestinationDisplayRef** – The headsign or display text shown from this stop to the journey's end; allows display changes along the route.

---

## 4. References

- [JourneyPattern](../JourneyPattern/Table_JourneyPattern.md) – Parent container
- [ScheduledStopPoint](../ScheduledStopPoint/Table_ScheduledStopPoint.md) – Logical stop referenced
- [DestinationDisplay](../DestinationDisplay/Table_DestinationDisplay.md) – Headsign display text
- [Notice](../Notice/Table_Notice.md) – Attached notices (via NoticeAssignment)

---

## 5. Usage Notes

### 5a. Consistency Rules

- **@order must be unique and sequential within a JourneyPattern** – No gaps or duplicates. Enables deterministic stop-to-stop distance calculation.
- **Every StopPointInJourneyPattern must reference an existing ScheduledStopPoint** – No orphaned stops.
- **ForAlighting and ForBoarding defaults to true** – Omission means both are allowed; explicit false blocks access.

### 5b. Validation Requirements

- Each stop in a JourneyPattern must have a **unique @order** value starting from 1.
- The **ScheduledStopPointRef/@ref** must point to a valid ScheduledStopPoint in the TimetableFrame.
- If **DestinationDisplayRef** is present, it must reference a valid DestinationDisplay.
- **RequestStop** should be `true` only for demand-responsive services; static timetables normally omit it.

### 5c. Common Pitfalls

- **Forgetting @order during XML generation** – Timetable converters (e.g., SKDUPD) depend on @order to determine stop position and distance.
- **Using identical stops multiple times without @order distinction** – A route may pass the same physical stop twice; @order disambiguates them.
- **Setting both ForAlighting and ForBoarding to false** – This makes the stop meaningless. Use StopUse=`passthrough` or exclude the stop instead.
- **Leaving DestinationDisplay unchanged across a multi-segment journey** – Update it at major transfer points to keep the headsign accurate.

### 5d. Profile-Specific Notes

- **Nordic Profile (NP):** All StopPointInJourneyPattern elements are required for timetable interchange; on-demand flexibility (RequestStop, FlexibleService) is optional.
- **NP:** More extensive booking and notice assignment support; SLO may require explicit notice chains for regulatory compliance.

---

## 6. Additional Information

### Relationship to TimetabledPassingTime

- StopPointInJourneyPattern defines **where** in a journey's sequence a stop appears (the pattern).
- TimetabledPassingTime defines **when** (arrival/departure times) for a specific ServiceJourney following that pattern.
- A single StopPointInJourneyPattern maps to many TimetabledPassingTime entries (one per ServiceJourney using the pattern).

### Use in Timetable Conversion

When converting NeTEx to EDIFACT (SKDUPD):

1. For each ServiceJourney, retrieve its JourneyPattern.
2. Iterate over JourneyPattern.pointsInSequence (i.e., all StopPointInJourneyPattern elements), ordered by @order.
3. For each TimetabledPassingTime in the ServiceJourney, match it to a StopPointInJourneyPattern via StopPointInJourneyPatternRef.
4. Use the StopPointInJourneyPattern @order to write the POR (Passage-Or-Record) stop position in the EDIFACT output.
5. Apply ForAlighting / ForBoarding rules to determine traffic restriction codes.

### Example XML Fragment

```xml
<JourneyPattern id="FLB:JP:1234">
  <pointsInSequence>
    <StopPointInJourneyPattern id="FLB:SPIJP:0001" order="1" version="1">
      <ScheduledStopPointRef ref="FLB:SSP:001" />
      <ForBoarding>true</ForBoarding>
      <ForAlighting>false</ForAlighting>
    </StopPointInJourneyPattern>
    
    <StopPointInJourneyPattern id="FLB:SPIJP:0002" order="2" version="1">
      <ScheduledStopPointRef ref="FLB:SSP:002" />
      <DestinationDisplayRef ref="FLB:DD:001" />
    </StopPointInJourneyPattern>
  </pointsInSequence>
</JourneyPattern>
```

---

## See Also

- [JourneyPattern Description](../JourneyPattern/Description_JourneyPattern.md)
- [ScheduledStopPoint Description](../ScheduledStopPoint/Description_ScheduledStopPoint.md)
- [SKDUPD Converter Guide](../../Guides/SKDUPD/SKDUPD_Converter_Guide.md)


---

## 7. Converter usage (NeTEx -> EDIFACT)

> [!NOTE]
> The **NeTEx -> EDIFACT converter** uses `StopPointInJourneyPattern` as the *positional* element of a journey:
> - Enumeration order (1-based) -> `POR.stop_number` in the SKDUPD output.
> - `ForBoarding` / `ForAlighting` (default `true`) -> `POR.traffic_restriction_code` (`2` alight-only, `3` board-only, `4` pass-through, blank = normal).
> - `ScheduledStopPointRef/@ref` is the join key out to the SSP/PSA/Quay/StopPlace chain that ultimately resolves the UIC.
