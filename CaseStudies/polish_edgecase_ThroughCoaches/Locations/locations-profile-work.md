# Locations Profile Work

Dette dokumentet brukes til å beskrive alle lokasjoner i case-studiet i tråd med Stable Identity-prinsippet.

Status:

- Leveranse v1: `locations-profile-example.xml` (profilert struktur med opake id-er)
- Leveranse v2.0: `locations-profile-v2.0.xml` (NeTEx 2.0 SiteFrame)
- UIC-kode bæres i `privateCodes/PrivateCode[@type='uicCode']`
- Koordinater hentet automatisk til `locations-overpass.csv`
- Dekning koordinater: 18 av 33 stoppesteder
- Validering: `valid=True` mot `XSD/xsd/NeTEx_publication.xsd`

Plan og progresjon:

1. Liste ut alle berørte lokasjoner fra eksempelet. (Ferdig)
2. Foreslå stabil og opak `id` for hvert stoppested. (Ferdig)
3. Legge UIC-kode i `privateCodes/PrivateCode[@type='uicCode']`. (Ferdig)
4. Legge inn koordinater (`Centroid/Location`) der kvaliteten er god nok. (Delvis)
5. Verifisere resterende koordinater manuelt før fullføring. (Gjenstår)
