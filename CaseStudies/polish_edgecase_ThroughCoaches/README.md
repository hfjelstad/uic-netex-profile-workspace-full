# Polish Edge Case: Through Coaches

Dette case-studiet samler et krevende NeTEx-eksempel for gjennomgående vogner (through coaches) med kobling/deling i knutepunkter.

## Innhold

### Source Data
- `wagony_bezposrednie_2026-04-23.xml`: originalt eksempelgrunnlag fra MERITS EDIFACT-eksport.

### Improvements & Documentation
- `improvements-identified.md`: konkrete forbedringer vi har implementert (tognummer per JourneyPart, opak lokalisering).

### Locations Profile ✅
- `Locations/locations-profile-example.xml`: første profilutkast med opake StopPlace-id-er.
- `Locations/locations-profile-v2.0.xml`: **NeTEx 2.0 SiteFrame**, validert mot repository-schema, 18/33 stoppesteder med koordinater.
- `Locations/locations-overpass.csv`: auto-innhentede koordinater fra OSM Overpass API.
- `Locations/locations-coordinate-gaps.md`: manglende koordinater (15 stoppesteder) for manuell innhenting.
- `Locations/locations-inventory.md`: inventarliste over alle 33 stoppesteder fra case-filen.

### Timetable Profile ✅
- `timetable-profile-sj406.xml`: **profilert eksempel** som viser hvordan tognummer modelleres eksplisitt per JourneyPart.
  - ServiceJourney 406 CHOPIN (München → Warszawa) med 3 deler:
    - Part 1: München → Breclav (Train 406)
    - Part 2: Breclav → Bohumín (Train 406x)
    - Part 3: Bohumín → Warszawa (Train 406y)
- `timetable-profile-standalone-servicejourneys.xml`: full profilering av **alle 6 enkelstående ServiceJourneys** med:
  - opake og stabile ServiceJourney-id-er (`PE:ServiceJourney:sj001` ... `sj006`)
  - tognummer flyttet til `privateCodes/PrivateCode[@type='trainNumber']` på SJ-nivå
  - eksplisitt tognummer per JourneyPart
  - uten `journeyPartCouples` og `blocks` (standalone-view)
- `timetable-profile-explanation.md`: detaljert dokumentasjon av profileringen.

## Mål

- ✅ Dokumentere edge-case-struktur tydelig (gjennom-tog-modellering).
- ✅ Avklare stabil identitet for reise, tognummer og kjøretøykobling.
- ✅ Etablere tydelig modell for lokasjonsbeskrivelser (UIC-kode som `PrivateCode`, stabil `id`).
- ✅ Vise hvordan tognummer kan endres per JourneyPart uten å bryte passasjer-opplevelsen.

## Status

| Komponent | Status | Noter |
|-----------|--------|-------|
| Locations (StopPlace) | ✅ v2.0 Profiled | 54.5% med koordinater; validert mot schema |
| Timetable (ServiceJourney) | ✅ Profiled | Eksplisitt tognummer per JourneyPart |
| Coordinate Coverage | 🟡 Partial | 18/33 stoppesteder; 15 mangler (liste opprett) |
| Schema Validation | ✅ Locations OK | Timetable: well-formed, kompatibel med v1.12/2.0 |
