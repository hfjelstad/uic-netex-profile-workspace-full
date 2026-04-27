## Structure Overview

```text
ScheduledStopPoint
 ├─ @id (1..1)
 ├─ @version (1..1)
 ├─ ValidBetween (0..1)
 │  └─ FromDate (0..1)
 ├─ Name (0..1)
 ├─ privateCodes (0..1)
 │  └─ PrivateCode @type (1..n)   ← preferred v2.0 (e.g. type="uicCode")
 ├─ PrivateCode (0..1)            ← legacy single-code pattern
 └─ TimingPointStatus (0..1)
```

## Table

| Element | Type | XSD | ERP | NP | Description | Path |
|---------|------|-----|-----|-----|-------------|------|
| @id | ID | 1..1 | 1..1 | 1..1 | Unique identifier for the ScheduledStopPoint | ScheduledStopPoint/@id |
| @version | String | 1..1 | 1..1 | 1..1 | Version label | ScheduledStopPoint/@version |
| Name | String | 0..1 | 0..1 | 0..1 | Human-readable name of the stop point | ScheduledStopPoint/Name |
| privateCodes | Container | 0..1 | 0..1 | 0..1 | Preferred NeTEx v2.0 container for typed external identifiers | ScheduledStopPoint/privateCodes |
| PrivateCode (@type) | String | 1..n | 1..n | 1..n | External code for inter-system matching. In UIC migration: `type="uicCode"` carrying the station's UIC code. Enables deterministic matching to corresponding typed codes on StopPlace without changing `@id`. | ScheduledStopPoint/privateCodes/PrivateCode |
| PrivateCode | String | 0..1 | 0..1 | 0..1 | Legacy single-code form kept for compatibility; prefer `privateCodes/PrivateCode` in v2.0 datasets | ScheduledStopPoint/PrivateCode |
| TimingPointStatus | Enum | 0..1 | 0..1 | | Whether this is a timing point (timingPoint, notTimingPoint) | ScheduledStopPoint/TimingPointStatus |
| ValidBetween | Period | 0..1 | | 0..1 | Validity period for the stop point | ScheduledStopPoint/ValidBetween |
| FromDate | DateTime | 0..1 | | 0..1 | Start date of validity | ScheduledStopPoint/ValidBetween/FromDate |
