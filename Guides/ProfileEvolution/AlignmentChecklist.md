# Alignment Checklist — what needs buy-in before we push

Working list of modelling decisions and changes that **require
alignment** (with the Nordic profile group, with CEN/UIC, or with
internal stakeholders) before they are locked into the profile or
proposed upstream.

Anything **not** on this list can be moved forward unilaterally inside
this profile / case-study work.

Updated: 2026-04-30. Owner: hfjelstad.

---

## A. Profile-level changes (Nordic profile group)

These do not touch NeTEx core. Decision needed: adopt into the Nordic
profile, keep as profile extension, or reject.

| ID    | Decision needed                                                                                          | Blocker? | Forum                  |
|-------|----------------------------------------------------------------------------------------------------------|----------|------------------------|
| P-001 | Make `type` attribute on `PrivateCode` mandatory + lock a shared vocabulary (`RICS`, `uicCode`, …)       | No       | Nordic profile review  |
| P-002 | Replace `Operator` + `OperatorRef` with `GeneralOrganisation` + `ResponsibilitySet` as the default       | No       | Nordic profile review  |
| —     | Use `TrainNumber` object (not `PrivateCode`) for commercial/operational service numbers in this profile  | No       | Internal — implement   |

Rationale for "no blocker": these can be applied in our own data and
case studies today; Nordic-profile adoption is an *upstream* outcome,
not a prerequisite.

---

## B. NeTEx core changes (CEN, onboarding window)

These touch the schema. Decision needed: raise as formal proposal in
the current onboarding window — yes/no, and with what scope.

| ID    | Decision needed                                                                              | Blocker? | Forum             |
|-------|----------------------------------------------------------------------------------------------|----------|-------------------|
| ~~P-004~~ | ~~Introduce `ServiceNumber` as co-equal alias to `TrainNumber`~~ | ~~Yes~~ | ~~CEN onboarding WG~~ |

**No blocker-level items remain.** P-004 was withdrawn 2026-05-12 —
the use cases are covered by `PublicCode` + P-001 + P-002 +
Block/BlockPart without a schema change.

---

## C. Edge cases to surface before next meeting

The user's own next-step task list. Each edge case is expected to
either:

- (a) confirm the existing model handles it → no change, document only,
- (b) reveal a profile-level gap → new P-XXX proposal, or
- (c) reveal a NeTEx core gap → candidate for P-004-style upstream
  proposal (folded in *before* the onboarding window closes).

| Case | Status         | Notes                                                                     |
|------|----------------|---------------------------------------------------------------------------|
| Polish through-coaches (DB → ČD → PKP, train 406)        | Done — surfaced P-001, P-002, P-004 | Reference case for multi-operator + per-leg numbering. |
| Multi-modal disruption (train replaced by bus mid-route) | TODO — pull edge case             | Validate `replacedJourneys` with mode change end-to-end.  |
| Cross-border with operator change at border station      | TODO — pull edge case             | Likely confirms P-002 is sufficient.                       |
| Ferry leg embedded in a rail journey                     | TODO — pull edge case             | Stress-tests P-004 motivation (mode-neutral name).         |
| Splitting/joining trains (one SJ becomes two)            | TODO — pull edge case             | May surface a new proposal around `JourneyPartCouple`.     |
| Reservation across overnight/multi-day journeys          | TODO — pull edge case             | Validates DSJ-per-OperatingDay model under long journeys.  |
| Pre-IM-approval sales window                             | TODO — pull edge case             | Already covered by ExtendedSales guide; confirm only.      |

For each new edge case, the workflow is:

1. Build (or borrow) a minimal NeTEx 2.0 example in `CaseStudies/<name>/`.
2. Validate against `XSD/xsd/NeTEx_publication.xsd`.
3. List "improvements identified" against the source (as in the Polish
   case).
4. Tag each improvement against this checklist:
   - if it fits an existing P-XXX → reference only,
   - if it is new and stays inside the profile → propose new P-XXX
     under category A,
   - if it requires a schema change → propose new P-XXX under
     category B (must hit the onboarding window).

---

## D. Things explicitly *not* on this checklist (out of scope)

Documented elsewhere or considered settled — do **not** spend meeting
time on these:

- Identity model (`DatedServiceJourney.id` as sales anchor, versioning).
  → [ExtendedSales_and_DeviationHandling_Guide](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Guides/ExtendedSales_and_DeviationHandling/ExtendedSales_and_DeviationHandling_Guide.md)
- Disruption mechanics (`replacedJourneys`, `ServiceAlteration`).
  → same guide.
- Calendar model (DayType / OperatingPeriod / OperatingDay,
  `isAvailable` exceptions).
  → [Calendar_Guide](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Guides/Calendar/Calendar_Guide.md)
- DatedServiceJourney structure and references.
  → [Description_DatedServiceJourney](https://github.com/hfjelstad/Profile_Documentation_v2/blob/EnStandardBranch/Objects/DatedServiceJourney/Description_DatedServiceJourney.md)

If a new edge case appears to challenge one of these, the default is
to assume the existing guide is right and re-read it before proposing
a change.

---

## E. Decision log

Append-only record of decisions made about items on this checklist.
Date · ID · Decision · Forum.

- 2026-04-30 · P-003 · **Withdrawn**, superseded by P-004 (native
  `TrainNumber` object covers commercial/operational split via
  `ForAdvertisement`/`ForProduction`). · Internal review.
- 2026-04-30 · P-004 · **Promoted from "won't do" to "upstream
  proposal — onboarding window"** on the strength of the
  onboarding-window argument (alias + soft deprecation is a normal CEN
  pattern; cost lower now than later). · Internal review.
- 2026-05-12 · P-004 · **Withdrawn.** Superseded by existing schema
  elements: `PublicCode` on ServiceJourney (commercial identity),
  `PrivateCode[@type='CommercialTrainNumber']` on JourneyPart (per-leg
  override per P-001), Block/BlockPart (operational/path numbers), and
  `responsibilitySetRef` on JourneyPart (per-leg operator per P-002).
  No CEN schema change needed. · Internal review.

---

## How to use this file

- Before any meeting: scan section B for blocker-level items.
- After any case-study session: update section C with what the case
  surfaced; add new P-XXX entries under A or B as needed.
- After any decision (adopt / reject / defer): append to section E.
- Sections A and B should match the Index in
  [ProfileEvolution_Proposals.md](ProfileEvolution_Proposals.md). If
  they drift, the proposals file wins.
