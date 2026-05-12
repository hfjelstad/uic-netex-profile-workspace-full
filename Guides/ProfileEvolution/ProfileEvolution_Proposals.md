# Profile Evolution — Proposals for the Nordic Profile

This guide collects **deliberate departures from current Nordic-profile
practice** that have emerged from concrete case-study work. They are
documented here, separately from object reference and identity guides,
so that they can be evaluated, discussed and (hopefully) adopted
upstream without bloating other documents.

Each proposal states:

- **Current Nordic practice** — what is done today
- **Proposed change** — the recommended pattern
- **Why it matters** — concrete benefits
- **Cost** — what producers and consumers pay
- **Migration** — how to adopt without breaking existing data
- **Origin** — case study or context that surfaced the need

---

## P-001 · Mandatory `type` attribute on `PrivateCode`

**Current Nordic practice.** `PrivateCode` is often used without a
`type` attribute, leaving readers to infer the meaning from context
(e.g. "the PrivateCode on a Line is the public line number").

**Proposed change.** **Always** set `type` on `PrivateCode`, and use a
shared, documented vocabulary of type values:

| `type` value   | Carried on                  | Meaning                                                |
|----------------|-----------------------------|--------------------------------------------------------|
| `RICS`         | GeneralOrganisation         | UIC Railway Interchange Coding System code (4 digits)  |
| `uicCode`      | StopPlace                   | UIC station code (typically 9 digits)                  |

The vocabulary is **open**: profiles may add domain-specific values
(e.g. `marketingCode`, `legacySystemId`).

> **Note.** Train/service numbers are intentionally **not** modelled as
> `PrivateCode` in this profile. NeTEx already has a dedicated
> `TrainNumber` object with `ForAdvertisement` (commercial) and
> `ForProduction` (operational) fields, referenced via `TrainNumberRef`
> from `ServiceJourney`, `JourneyPart` and `JourneyPartCouple`. See
> **P-004** for the mode-neutral alias proposed upstream.

**Why it matters.**

- **Disambiguation**: a `ServiceJourney` may carry several private codes
  (train number, internal product code, marketing code). Without
  `type`, only the first is interpretable; with `type`, all are.
- **Machine-readable profiles**: converters and validators can target
  `PrivateCode[@type='trainNumber']` directly without heuristics about
  parent context.
- **Forward-compatible**: new external coding systems can be added
  without breaking existing consumers — they simply ignore unknown
  `type` values.
- **Single source of truth**: combined with P-002, RICS is defined
  exactly once (on the `GeneralOrganisation`) instead of being
  duplicated on every ServiceJourney.

**Cost.** A few extra characters per element. No schema change.

**Migration.** Treat untyped `PrivateCode` as deprecated; profile
validators warn on missing `type`. Producers add `type` opportunistically.

**Origin.** Polish through-coaches case study
(`CaseStudies/polish_edgecase_ThroughCoaches/`).

---

## P-002 · Use `GeneralOrganisation` + `ResponsibilitySet` instead of `Operator` + `OperatorRef`

**Current Nordic practice.** Each transport organisation is modelled as
an `Operator` (or `Authority`). `ServiceJourney` references it via
`OperatorRef`. JourneyParts have **no** `OperatorRef`, so per-leg
operator changes cannot be expressed natively.

**Proposed change.** Use the more general NeTEx pattern:

1. Declare each organisation **once** as a role-neutral
   `GeneralOrganisation` in `ResourceFrame/organisations`.
2. Define one `ResponsibilitySet` per (organisation, role) combination
   in `ResourceFrame/responsibilitySets`, with
   `ResponsibilityRoleAssignment` carrying `StakeholderRoleType`
   (`operation`, `customerService`, `dataRegistrar`, ...) and
   `ResponsibleOrganisationRef` pointing to the GeneralOrganisation.
3. On `ServiceJourney`, `JourneyPart`, `Line`, `StopPlace`, etc., set
   the inherited `responsibilitySetRef` attribute from
   `DataManagedObjectGroup`.

```xml
<organisations>
  <GeneralOrganisation id="PE:GeneralOrganisation:1155" version="1">
    <privateCodes><PrivateCode type="RICS">1155</PrivateCode></privateCodes>
    <Name>DB Fernverkehr AG</Name>
    <ShortName>DB</ShortName>
  </GeneralOrganisation>
</organisations>
<responsibilitySets>
  <ResponsibilitySet id="PE:ResponsibilitySet:1155" version="1">
    <Name>DB as operator</Name>
    <roles>
      <ResponsibilityRoleAssignment id="PE:RRA:1155_op" version="1">
        <StakeholderRoleType>operation</StakeholderRoleType>
        <ResponsibleOrganisationRef ref="PE:GeneralOrganisation:1155" version="1"/>
      </ResponsibilityRoleAssignment>
    </roles>
  </ResponsibilitySet>
</responsibilitySets>
...
<ServiceJourney id="PE:ServiceJourney:sj003" version="1"
                responsibilitySetRef="PE:ResponsibilitySet:1251">
  ...
  <parts>
    <JourneyPart id="PE:JourneyPart:sj003_p01" version="1"
                 responsibilitySetRef="PE:ResponsibilitySet:1155"> ... </JourneyPart>
    <JourneyPart id="PE:JourneyPart:sj003_p02" version="1"
                 responsibilitySetRef="PE:ResponsibilitySet:1181"> ... </JourneyPart>
    <JourneyPart id="PE:JourneyPart:sj003_p03" version="1"
                 responsibilitySetRef="PE:ResponsibilitySet:1251"> ... </JourneyPart>
  </parts>
</ServiceJourney>
```

**Why it matters.**

- **Per-leg operator** is modelled natively. `JourneyPart` cannot carry
  `OperatorRef` in the schema, but `responsibilitySetRef` is inherited
  from `DataManagedObjectGroup` and works on every managed object.
  Through-coach services (DB → ČD → PKP on the same wagon) become
  expressible without workarounds.
- **Identity vs role separation.** A railway company can be operator on
  some trains, customer-service contact on others, data registrar on a
  third. With `Operator` you must either pick one role or duplicate the
  organisation. `GeneralOrganisation` + `ResponsibilitySet` lets the
  identity be defined once and reused in many roles.
- **Multiple stakeholders per object.** A `ResponsibilitySet` can
  contain several `ResponsibilityRoleAssignment` elements — useful when
  an object has, say, an operator *and* an infrastructure manager *and*
  a retail consortium.
- **Default + override semantics.** When `responsibilitySetRef` is
  absent on a `JourneyPart`, the parent `ServiceJourney`'s value
  applies. This matches the natural "lead operator owns the journey,
  individual legs may differ" pattern.
- **No information loss vs OperatorRef.** A `ResponsibilitySet` with a
  single `operation` role is informationally equivalent to an
  `OperatorRef`; the indirection costs one lookup and buys all of the
  above.

**Cost.** One extra object kind (`ResponsibilitySet`) per role/operator
combination. Converters need a 2-step lookup
(`responsibilitySetRef` → `ResponsibilityRoleAssignment` →
`ResponsibleOrganisationRef`) instead of a 1-step `OperatorRef`.

**Migration.** A profile can support both during transition: producers
emit `responsibilitySetRef` going forward; consumers fall back to
`OperatorRef` if absent. Strict profiles emit `responsibilitySetRef`
only.

**Origin.** Polish through-coaches case study
(`CaseStudies/polish_edgecase_ThroughCoaches/`), where train 406 CHOPIN
changes operator three times (DB → ČD → PKP) within one ServiceJourney.

---

## Index

| ID    | Title                                                                | Status                              |
|-------|----------------------------------------------------------------------|-------------------------------------|
| P-001 | Mandatory `type` attribute on `PrivateCode`                          | proposed                            |
| P-002 | `GeneralOrganisation` + `ResponsibilitySet` instead of `OperatorRef` | proposed                            |
| P-004 | Mode-neutral `ServiceNumber` as co-equal alias to `TrainNumber`      | withdrawn — superseded by P-001 + P-002 + `PublicCode` |

**Status vocabulary:**

- `proposed` — recommended for adoption inside this profile.
- `applied` — already implemented in this profile's reference data.
- `open for discussion` — surfaced as a question, no recommendation yet.
- `upstream proposal — onboarding window` — proposed change to NeTEx
  core (CEN), to be raised while the current onboarding window is open
  and reviewers are looking at the whole picture rather than at
  isolated deltas.

---

## P-004 · Mode-neutral `ServiceNumber` as a co-equal alias to `TrainNumber` (NeTEx core)

**Status.** ~~Upstream proposal — onboarding window.~~ **Withdrawn** (2026-05-12).

**Reason for withdrawal.** The problem P-004 addressed — mode-specific
naming and conflation of commercial/operational numbers — is fully
covered by existing NeTEx elements without a schema change:

- **Commercial identity** → `PublicCode` on `ServiceJourney` (already
  mode-neutral, already in schema).
- **Per-leg commercial number** (if it differs) →
  `PrivateCode[@type='CommercialTrainNumber']` on `JourneyPart` (P-001).
- **Operational/path number** → `Block`/`BlockPart` in
  `VehicleScheduleFrame` (existing schema, lays foundation for future
  PathAllocationFrame).
- **Per-leg operator** → `responsibilitySetRef` on `JourneyPart` (P-002).

No CEN proposal needed. The onboarding window can be used for other
items if desired.

<details>
<summary>Original proposal (archived)</summary>

**Scope.** This is the *only* proposal in this document that targets
NeTEx core rather than profile practice. P-001 and P-002 require no
schema change; P-004 does.

### Background — what already works

The identity model and disruption mechanics for services are already
documented and considered settled in the wider profile work — see the
[Extended Sales & Deviation Handling guide](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Guides/ExtendedSales_and_DeviationHandling/ExtendedSales_and_DeviationHandling_Guide.md),
the [Calendar guide](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Guides/Calendar/Calendar_Guide.md)
and the [DatedServiceJourney description](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Objects/DatedServiceJourney/Description_DatedServiceJourney.md).
In short:

- `DatedServiceJourney.id` is the stable, versionable sales anchor — it
  replaces the legacy `TrainNumber + Date (+ Operator)` composite key.
- Replacement, reinforcement and supplementary services are modelled as
  *independent* DSJs with `replacedJourneys/DatedVehicleJourneyRef`
  pointing back to the original — natively, in NeTEx 2.0.
- This already works **across modes**: a bus DSJ can replace a train
  DSJ; a taxi DSJ can supplement a ferry DSJ. The data model is
  mode-neutral.

P-004 does **not** change any of this. It addresses a residual
*terminological* problem on top of an already-working data model.

### The residual problem

NeTEx has a dedicated `TrainNumber` object
(`ForAdvertisement` / `ForProduction`) referenced via `TrainNumberRef`
from `ServiceJourney`, `JourneyPart` and `JourneyPartCouple`. Two
frictions follow from the name:

1. **Mode-specific element name in a mode-neutral standard.** When a
   bus, ferry or taxi participates in a multimodal disruption flow
   (replacement / reinforcement / supplement), it carries a
   `TrainNumber` element. The data is correct; the label is wrong.
   Sister communities use `tripNumber`, `runNumber`, `journeyNumber`,
   `turNummer` etc. for the same concept.
2. **Conflation pressure on a single name.** `TrainNumber` is asked to
   serve commercial branding (`ForAdvertisement`, e.g. `406` end to
   end) and operational reporting (`ForProduction`, e.g. `406 / 406x /
   406y` per leg). The native object already separates these two
   fields; a mode-neutral container reinforces that the distinction is
   semantic, not rail-specific.

### Proposed change (NeTEx core)

Introduce `ServiceNumber` as a **co-equal alias** to `TrainNumber` in
the NeTEx schema:

- Same XSD structure: `ForAdvertisement`, `ForProduction`, same
  cardinalities, same parent collection (`<trainNumbers>` becomes
  optionally `<serviceNumbers>` or both names accepted).
- Same reference type: `ServiceNumberRef` resolves to either
  `TrainNumber` or `ServiceNumber`.
- Both names valid simultaneously; `TrainNumber` carries a soft
  deprecation marker (`-vX.X`) recommending migration to
  `ServiceNumber` for new data.
- No information change, no breaking change, no migration required of
  existing rail systems.

This is a normal CEN alias-with-deprecation pattern.

### Profile-level policy (this profile)

Once the alias exists in NeTEx core:

- **Emit** `ServiceNumber` / `serviceNumbers` / `ServiceNumberRef`.
- **Accept** `TrainNumber` / `trainNumbers` / `TrainNumberRef` on input
  for backward compatibility.
- **Never emit** `TrainNumber` from this profile.

This is what makes the alias a real deprecation track rather than a
parallel option: a profile that always picks the new name turns the
old one into legacy by attrition.

### Why now (the onboarding-window argument)

The strongest reason to raise this proposal *now* is timing:

- The current NeTEx onboarding work (in which this profile
  participates) reviews the standard *as a whole*. Reviewers expect to
  discuss structural and terminological choices and accept
  alias-with-deprecation patterns as a normal outcome.
- After the onboarding window closes, the same change requires a
  formal revision cycle — measured in years rather than months, and
  needing consensus that does not exist today.
- Two flies, one swat: harmonisation now (multimodal disruption flows
  no longer carry a rail-specific element name) **and** a deprecation
  path that no later revision can quietly reverse.

Waiting is the expensive option.

### What this proposal does *not* claim

- It does **not** claim that the data model is broken without it.
  `DatedServiceJourney` + `replacedJourneys` already handle multimodal
  disruption end to end.
- It does **not** claim that `TrainNumber` will or should disappear
  from operational rail systems. Those systems have decades of tooling
  and regulatory anchoring around the term and will not migrate
  because of a NeTEx label.
- It does **not** require any change to existing rail data feeds.
  Producers may continue to emit `TrainNumber` indefinitely.

The proposal is about giving multimodal use cases a clean home and
leaving a documented preference behind, while it is still cheap to do.

### Risks and mitigations

| Risk                                                    | Mitigation                                                                                                   |
|---------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Bikeshedding on the chosen name                         | Propose `ServiceNumber` and hold it. Mirrors `ServiceJourney`; mode-neutral; readable.                       |
| Two parallel hierarchies instead of one alias           | Specify in the proposal: same XSD type, shared reference target, single substitution group.                  |
| Rail community perceives terminology loss               | Frame as alias + soft deprecation, not removal. `TrainNumber` stays valid forever in core.                   |
| Profile policy is read as a removal mandate             | State the policy as *this profile* emits one name; other profiles may choose differently.                    |
| Confusion between `ServiceNumber` and `ServiceJourney`  | Acceptable — the parallel naming is the point. Document that `ServiceNumber` is the *number on* the service. |

### Origin

Polish through-coaches case study
(`CaseStudies/polish_edgecase_ThroughCoaches/`), where train 406 CHOPIN
crosses three operators and the per-leg numbering exposes both the
mode-specific naming friction and the commercial/operational split.
Generalised against the existing DSJ / `replacedJourneys` model in the
[Profile_Documentation_v2 guides](https://github.com/hfjelstad/Profile_Documentation_v2/tree/EnStandardBranch/Guides),
which already handle the data side.

<!-- P-003 (split trainNumber into commercial/operational PrivateCode types) was
     superseded by P-004 once the native TrainNumber object with
     ForAdvertisement/ForProduction was confirmed to cover the same
     distinction without a profile extension. -->

</details>

---

## P-005 · Through coaches modelled as passenger opportunity, not coach attachment

**Current Nordic practice.** The profile does not currently commit to a
through-coach model. The obvious route — mirroring UIC EDIFACT 916-1
mode 31 with a "host train" back-reference from the coach's
ServiceJourney to the train's, as MERITS does with the `_KW_` brand —
has been avoided because it imports vehicle-centric semantics that
downstream consumers then have to undo.

**Proposed change.** Model through coaches as **one passenger journey,
not as a coach attached to host trains**:

1. **One `ServiceJourney` per traveller opportunity** — origin to
   destination, unified `passingTimes`, single primary identity
   (`DatedServiceJourney` for the dated instance, P-004 `ServiceNumber`
   for the customer-facing number).
2. **`JourneyPart` for operational segmentation** — boundaries placed
   only where operational identity genuinely changes (loco/crew swap,
   operator change, IM-assigned path number change). Per-leg train
   numbers go on `JourneyPart/privateCodes/PrivateCode[@type='trainNumber']`
   (per P-001), per-leg responsibility on
   `JourneyPart/responsibilitySetRef` (per P-002).
3. **`JourneyPartCouple` for shared-consist sections** — when two
   distinct ServiceJourneys (e.g. coach 406 and coach 416) run coupled
   for a stretch, both keep their own identity, schedule and tickets;
   the couple records the shared track relationship.
4. **`Block` / `BlockPart` for wagon lifecycle** (in a
   `VehicleScheduleFrame`) — only when a producer needs to expose the
   physical coach's path across multiple ServiceJourneys. Optional, not
   the primary identity.
5. **No "host train" relationship as a first-class profile concept.**
   The host train is a fact about the wagon, not about the journey;
   exposing it in the journey model leaks vehicle-centric semantics
   into a passenger-centric profile.

**Why it matters.**

- **Answers the traveller's question.** "Can I stay seated München →
  Warszawa?" is one query against one `ServiceJourney`, not a graph
  walk over join/split events between coach groups and host trains.
- **Survives reality.** A through coach can have **zero, one, or many**
  host trains along its route, and the host can change at every
  border. Anchoring on a single host introduces a primary key that
  does not exist; anchoring on per-event relationships (which is what
  EDIFACT actually does, with Group 8 repeatable up to 99 per stop)
  is data-faithful but not what most consumers want to read.
- **Multi-operator clean.** Combined with P-002, per-leg operator and
  RICS live on the JourneyPart's `responsibilitySetRef`. No special
  "wagon owner" or "host RU" concept is needed.
- **Lossy projection is honest.** EDIFACT export becomes a
  *projection* with a documented policy choice, not a reverse-mapping
  of a vehicle-centric source.

**Cost.** Exporters must implement an explicit projection policy
(below) rather than a 1:1 mapping. Importers from EDIFACT mode 31 must
infer the passenger-opportunity grouping rather than read it
directly — non-trivial when a feed contains coach groups without
explicit operational grouping.

**Migration.**

- New feeds: model directly as one `ServiceJourney` per opportunity
  with `JourneyPart`s and (optional) `JourneyPartCouple` /
  `Block`/`BlockPart`.
- Existing EDIFACT-derived feeds: at import, group `PRD+...:31`
  records that share host-train references and timing into a single
  `ServiceJourney`. Where grouping is ambiguous, fall back to one SJ
  per coach group with a `Note` describing the ambiguity.
- Document the chosen export projection (see below) per consumer.

### EDIFACT projection policy (export-time choice)

Projecting a passenger-centric NeTEx model to EDIFACT 916-1 is
inherently lossy. Three projections are valid:

| Option | EDIFACT encoding | Trade-off |
|---|---|---|
| **A · Per-leg mode 37** | One `PRD+...:37+...` per `JourneyPart`, with `RFR+AUE` + `RLS+13+8`/`+11` join/split between consecutive PRDs | Preserves per-leg train numbers and operator change; passenger "single journey" view requires the consumer to follow the join/split chain. |
| **B · Mode 31 (UIC default)** | `PRD+...:31+...` per coach group, with `RFR+AUE` per join/split event in Group 8 | Round-trips cleanly with MERITS and `_KW_` consumers. Vehicle-centric semantics travel along; the passenger-opportunity grouping is implicit. |
| **C · Single mode 37** | One `PRD+...:37+...` for the whole journey, using the customer-facing service number; per-leg numbers dropped | Cleanest passenger view; loses per-leg train number / operator change information. Suitable for journey-planner consumers, not for operational consumers. |

The profile does not mandate a single projection. Producers MUST
declare which projection a given feed uses. Most timetable consumers
will want B for compatibility with the MERITS ecosystem; multimodal
journey planners may prefer C; operational consumers needing per-leg
train numbers will want A.

**Origin.** Polish through-coaches case study
(`CaseStudies/polish_edgecase_ThroughCoaches/`) and analysis of UIC
documentation provided April 2026
(`CaseStudies/UIC - Documentation/`). The 916-1 spec confirms Group 8
(`RFR+AUE` + `RLS`) is **Conditional, repeatable up to 99 per stop**
for mode-31 services — there is no single "main host train" requirement
in EDIFACT either; the vehicle-centric framing comes from how the
mode is named and from MERITS UI conventions, not from a hard schema
constraint.

