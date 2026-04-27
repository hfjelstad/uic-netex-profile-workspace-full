## Structure Overview

```text
GroupOfLines
 ├─ @id (1..1)
 ├─ @version (1..1)
 ├─ Name (0..1)
 ├─ ShortName (0..1)
 ├─ Description (0..1)
 ├─ privateCodes (0..1)
 │  └─ PrivateCode @type (1..n)
 ├─ PrivateCode (0..1)            ← legacy single-code pattern
 └─ members (1..1)
    └─ LineRef/@ref (1..n)
```

## Table

| Element | Type | XSD | Description | Path |
|---------|------|-----|-------------|------|
| @id | ID | 1..1 | Unique identifier for the GroupOfLines | GroupOfLines/@id |
| @version | String | 1..1 | Version label | GroupOfLines/@version |
| Name | String | 0..1 | Public name of the group | GroupOfLines/Name |
| ShortName | String | 0..1 | Short public name or label | GroupOfLines/ShortName |
| Description | String | 0..1 | Description of purpose and content | GroupOfLines/Description |
| privateCodes | Container | 0..1 | Preferred NeTEx v2.0 container for typed internal/external identifiers | GroupOfLines/privateCodes |
| PrivateCode (@type) | String | 1..n | Typed code within `privateCodes`; `@type` should identify code system and be unique in container | GroupOfLines/privateCodes/PrivateCode |
| PrivateCode | String | 0..1 | Legacy single-code form kept for compatibility; prefer `privateCodes/PrivateCode` in v2.0 datasets | GroupOfLines/PrivateCode |
| [Line](../Line/Table_Line.md)@ref | Reference | 0..n | Reference to a Line that is a member of this group | GroupOfLines/members/LineRef/@ref |
