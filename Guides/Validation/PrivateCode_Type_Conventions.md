# PrivateCode Type Conventions

## Purpose
Define a stable naming convention for `privateCodes/PrivateCode/@type` so values are unique, interoperable, and predictable across NeTEx and UIC EDIFACT migrations.

## What NeTEx v2.0 enforces
- `privateCodes` is a container for one or more `PrivateCode` entries.
- `@type` must be unique within each `privateCodes` container.
- This means one object cannot contain two codes with the same `@type`.

## Recommendation for this profile
Use controlled tokens in lowerCamelCase and keep them stable over time.

Preferred core types:
- `uicCode`: UIC station/location code used for cross-file matching.
- `reservationCode`: Reservation/operational code (e.g., passenger booking reference).
- `lineCode`: Operator/internal line code.
- `serviceCode`: Operator/internal service journey code.
- `quayLocalCode`: Local quay/platform code.

## About names like uic:LocationCode
You can use a prefixed style, but it is not necessary and can be confused with XML namespace prefixes.

For this profile, prefer:
- `uicCode` (recommended)

Avoid introducing multiple aliases for the same meaning, such as both `uicCode` and `uic:LocationCode`.

## EDIFACT TSDUPD alignment
In UIC EDIFACT mappings used here, station/location identifiers are represented as UIC values (for example in stop-oriented tables and POR-oriented mapping references).

For NeTEx migration, map that value to:
- `privateCodes/PrivateCode[@type='uicCode']`

## Legacy Database Field Mapping
If your source database has the columns `Key`, `UIC Code`, and `Reservation Code`, apply the mapping below.

Recommended canonical mapping:
- `Key` -> `privateCodes/PrivateCode[@type='uicCode']` when it is identical to UIC code.
- `UIC Code` -> `privateCodes/PrivateCode[@type='uicCode']`.
- `Reservation Code` -> `privateCodes/PrivateCode[@type='reservationCode']`.

Rules:
- If `Key` and `UIC Code` are equal, store only one `uicCode` entry.
- Do not overload `uicCode` with reservation semantics.
- Keep `reservationCode` separate even when some countries (for example Sweden) rely on it operationally.

## Governance rules
- Keep a small canonical list of allowed `@type` values in profile docs.
- Treat new `@type` values as change-controlled (review before use).
- Do not rename existing `@type` values once datasets are in production.
- Validate that each object has at most one code per `@type`.

## Example
```xml
<StopPlace id="NSR:StopPlace:59977" version="1">
  <privateCodes>
    <PrivateCode type="uicCode">007600100</PrivateCode>
    <PrivateCode type="reservationCode">OSL</PrivateCode>
  </privateCodes>
  <Name lang="nor">Oslo S</Name>
</StopPlace>
```

See the [Location Handling Guide](../LocationHandling/LocationHandling_Guide.md) for the full UIC requirement and the TSDUPD/SKDUPD delivery contract that depends on `uicCode`.
