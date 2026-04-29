# Build converter input zips from canonical XML files and run
# NeTEx -> SKDUPD (timetable) and NeTEx -> TSDUPD (stations).
# Usage: pwsh -File .\run_conversion.ps1
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# Timetable zip needs both a "shared" file and a journey file.
New-Item -ItemType Directory -Path "ConverterInput\tmp_tt" -Force | Out-Null
Copy-Item "timetable-profile-standalone-servicejourneys.xml" "ConverterInput\tmp_tt\_PE_shared_data.xml" -Force
Copy-Item "timetable-profile-standalone-servicejourneys.xml" "ConverterInput\tmp_tt\PE_journeys.xml" -Force
Compress-Archive -Path "ConverterInput\tmp_tt\*.xml" -DestinationPath "ConverterInput\Timetable_profile.zip" -Force
Remove-Item -Recurse -Force "ConverterInput\tmp_tt"

# RailStations zip
New-Item -ItemType Directory -Path "ConverterInput\tmp_rs" -Force | Out-Null
Copy-Item "Locations\locations-profile-v2.0.xml" "ConverterInput\tmp_rs\locations-profile-v2.0.xml" -Force
Compress-Archive -Path "ConverterInput\tmp_rs\locations-profile-v2.0.xml" -DestinationPath "ConverterInput\RailStations_profile.zip" -Force
Remove-Item -Recurse -Force "ConverterInput\tmp_rs"

# Run conversion
python "..\..\NeTEx2EDIFACT\run_conversion.py" `
    --source-dir ConverterInput `
    --stations ConverterInput\RailStations_profile.zip `
    --output ConverterOutput\new_SKDUPD.r `
    --originator PE

# TSDUPD: stations -> EDIFACT (uses the SiteFrame XML directly)
python "..\..\NeTEx2EDIFACT\netex2tsdupd.py" `
    --input "Locations\locations-profile-v2.0.xml" `
    --output "ConverterOutput\new_TSDUPD.r" `
    --originator PE
