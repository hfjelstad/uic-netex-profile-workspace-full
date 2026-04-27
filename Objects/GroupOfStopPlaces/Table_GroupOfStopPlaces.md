```text
GroupOfStopPlaces
 ├─ @id (1..1)
 ├─ @version (1..1)
 ├─ privateCodes (0..1)
 │   └─ PrivateCode @type (1..n)
 ├─ Name (1..1)
 ├─ ShortName (0..1)
 ├─ Description (0..1)
 ├─ PurposeOfGroupingRef (0..1)
 ├─ Centroid (0..1)
 │   └─ Location
 │       ├─ Longitude
 │       └─ Latitude
 └─ members (1..1)
     └─ StopPlaceRef (1..n)
```

## Table

| Element | Type | XSD | NP | Description | Path |
|---------|------|-----|----|-------------|------|
| @id | ID | 1..1 | 1..1 | Unique identifier in producer's codespace (e.g., `NSR:GroupOfStopPlaces:OsloS`) | GroupOfStopPlaces/@id |
| @version | String | 1..1 | 1..1 | Version number | GroupOfStopPlaces/@version |
| privateCodes | Container | 0..1 | 0..1 | Container for multiple typed external codes (NeTEx 2.0). Use when more than one external identifier is needed. For a single code, plain `<PrivateCode>` without a container is still valid. | GroupOfStopPlaces/privateCodes |
| PrivateCode | String | 1..n | 1..n | An external or legacy code for this group. `@type` attribute is required and must be unique within the container (e.g. `type="eraCode"`) | GroupOfStopPlaces/privateCodes/PrivateCode |
| Name | String | 1..1 | 1..1 | Human-readable name of the group | GroupOfStopPlaces/Name |
| ShortName | String | 0..1 | 0..1 | Abbreviated name | GroupOfStopPlaces/ShortName |
| Description | String | 0..1 | | Free-text description of the group's purpose | GroupOfStopPlaces/Description |
| [PurposeOfGroupingRef](../PurposeOfGrouping/Description_PurposeOfGrouping.md)/@ref | Reference | 0..1 | 0..1 | Reference to a `PurposeOfGrouping` object defined in a `ResourceFrame`. Not a free-text string — must resolve to a declared object. | GroupOfStopPlaces/PurposeOfGroupingRef/@ref |
| Centroid | Location | 0..1 | 0..1 | Geographic centre of the group (WGS84) | GroupOfStopPlaces/Centroid/Location |
| Longitude | Decimal | 0..1 | 0..1 | WGS84 longitude | GroupOfStopPlaces/Centroid/Location/Longitude |
| Latitude | Decimal | 0..1 | 0..1 | WGS84 latitude | GroupOfStopPlaces/Centroid/Location/Latitude |
| members | Container | 1..1 | 1..1 | Collection of member StopPlace references | GroupOfStopPlaces/members |
| [StopPlaceRef](../StopPlace/Description_StopPlace.md)/@ref | Reference | 1..n | 1..n | Reference to a member StopPlace. Omit `@version` for external registry references | GroupOfStopPlaces/members/StopPlaceRef/@ref |
