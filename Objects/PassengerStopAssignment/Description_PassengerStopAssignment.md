# PassengerStopAssignment

> *→ [Glossary definition](../../Guides/Glossary/Glossary.md#passengerstopassignment)*

## 1. Purpose

A **PassengerStopAssignment** links a logical `ScheduledStopPoint` to a physical `Quay` within a `StopPlace`, bridging the gap between timetable planning and physical infrastructure. It determines which platform passengers should use for a given stop, and can be overridden for specific dated journeys to handle operational changes such as platform reassignments.

In a two-file delivery structure, `PassengerStopAssignment` is the **cross-file bridge**: it lives in the timetable file's `ServiceFrame` and carries a `QuayRef` that points into the separate location file's `SiteFrame`. The `QuayRef` (and `StopPlaceRef`) are external references and must omit `@version`.

### Cross-file linkage pattern (UIC migration)

During UIC migration, the matching key between the two files is the UIC station code, carried as `privateCodes/PrivateCode type="uicCode"` on both sides:

```
Location file (SiteFrame)
  StopPlace  id="NSR:StopPlace:337"  privateCodes/PrivateCode type="uicCode" = "007600100"
    └─ Quay  id="NSR:Quay:107401"

Timetable file (ServiceFrame)
  ScheduledStopPoint  id="VR:ScheduledStopPoint:007600100"  privateCodes/PrivateCode type="uicCode" = "007600100"
  PassengerStopAssignment
    ├─ ScheduledStopPointRef  ref="VR:ScheduledStopPoint:007600100"
    ├─ StopPlaceRef           ref="NSR:StopPlace:337"      (no @version — external)
    └─ QuayRef                ref="NSR:Quay:107401"        (no @version — external)
```

This means neither file needs to change its `@id` structure to harmonize — the UIC code is the durable matching key. The legacy singleton `PrivateCode` can still appear in older datasets, but v2.0 guidance is to use the `privateCodes` container.

## 2. Structure Overview

```text
📄 PassengerStopAssignment
  ├─ 📄 @id (1..1)
  ├─ 📄 @version (1..1)
  ├─ 📄 @order (1..1)
  ├─ 📄 ValidBetween (0..1)
  ├─ 🔗 ScheduledStopPointRef/@ref (1..1)
  ├─ 🔗 StopPlaceRef/@ref (0..1)
  └─ 🔗 QuayRef/@ref (1..1)
```

## 3. Key Elements

- **ScheduledStopPointRef**: Mandatory reference to the logical timetable stop being assigned to a physical platform.
- **StopPlaceRef**: Optional explicit reference to the parent StopPlace; can be inferred from the Quay's containment.
- **QuayRef**: Mandatory reference to the physical boarding/alighting position (Quay) within a StopPlace.
- **@order**: Technical sequence number; mandatory but carries no business meaning.

## 4. References

- [ScheduledStopPoint](../ScheduledStopPoint/Table_ScheduledStopPoint.md) – The logical timetable stop being assigned
- [Quay](../Quay/Table_Quay.md) – The physical platform assigned to the stop
- [StopPlace](../StopPlace/Table_StopPlace.md) – The stop location containing the assigned Quay

## 5. Usage Notes

### 5a. Consistency Rules

- The referenced QuayRef must belong to the referenced StopPlaceRef (if provided), or to a StopPlace that logically contains it.
- All references must resolve to objects within the same dataset or an externally referenced frame.

### 5b. Validation Requirements

- **ScheduledStopPointRef and QuayRef are both mandatory** — every assignment must link a logical stop to a physical platform.
- **@id and @version are mandatory** — follow codespace conventions (e.g., `ERP:PassengerStopAssignment:1001`).

### 5c. Common Pitfalls

> [!WARNING]
> - **Missing assignments**: A ScheduledStopPoint without a PassengerStopAssignment cannot be resolved to a physical platform, breaking journey planning and passenger information.
> - **QuayRef not belonging to StopPlaceRef**: If both are specified, the Quay must be contained within the referenced StopPlace; mismatches create data integrity errors.

## 6. Additional Information

See [Table_PassengerStopAssignment.md](Table_PassengerStopAssignment.md) for detailed attribute specifications.

Example XML: [Example_PassengerStopAssignment.xml](Example_PassengerStopAssignment_ERP.xml)
