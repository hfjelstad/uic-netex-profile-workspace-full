## 1. Structure Overview (placed at the top of `Table_<FrameName>.md`)

The Structure Overview must:
- start with the frame name as the root node (e.g., `ServiceFrame`),
- follow the exact element order from the XML examples,
- show nesting using a monospace tree diagram,
- use box-drawing symbols for clarity and consistency,
- list attributes inline using `ElementName/@attribute`,
- show cardinality on every element using standard notation: `(1..1)`, `(1..n)`, `(0..1)`, `(0..n)`,
- match the Structure Overview in the corresponding `Description_<FrameName>.md` if one exists,
- contain no descriptions or comments—structure only.

### Structure Overview Template
```text
<FrameName>
 ├─ @id (1..1)
 ├─ @version (1..1)
 ├─ <CollectionA> (0..1)
 │   └─ <ChildObject> (0..n)
 ├─ <CollectionB> (0..1)
 │   └─ <ChildObject> (0..n)
 └─ <CollectionC> (0..1)
     └─ <ChildObject> (0..n)
```

## 2. `Table_<FrameName>.md` (mandatory)

The flat table provides a normalized representation of the frame's structure.
It must always be placed below the Structure Overview.

### Required Columns

The table must always contain the following columns, in this order:

Element | Type | Description | Path

### Rules
- **Element** must contain only the element name or attribute (e.g., `organisations`, `Authority`).
  No nesting or path notation is allowed here.

- **Cross-references** to Objects must be written using relative links.
  The link wraps the Object name and points to its Table file.
  Example:
  `[Authority](../../Objects/Authority/Table_Authority.md)`

- **Type** must reflect the datatype or structural role:
  - Use `Container` for collection elements (e.g., `organisations`, `vehicleJourneys`)
  - Use `Element` for child objects within a collection
  - Use `ID` and `String` for attributes
  - Use `Reference` for `@ref` elements

- **Description** must briefly describe the element's purpose within the frame.

- **Path** must contain the full hierarchical structure using slash notation
  (e.g., `ServiceFrame/lines/Line`).

### Additional Requirements
- All columns must be present for every row.
- Attributes must appear with an `@` prefix.
- The structure, order, and presence of elements must match the XML examples.
- The table and Structure Overview must always remain synchronized.
- All documentation must be written in English.
- Frame tables do not use profile columns (unlike Object tables). Frames serve as
  containers and their structure is consistent across profiles.
