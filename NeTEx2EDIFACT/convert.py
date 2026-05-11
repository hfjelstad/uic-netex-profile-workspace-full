# -*- coding: utf-8 -*-
"""
convert.py — Zero-config converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Put NeTEx files in Source/, run this script, get EDIFACT in Output/.

  1. Place files in Source/:
     - Station data:   any *.zip or *.xml containing a SiteFrame
     - Timetables:     operator NeTEx ZIPs (one per operator)

  2. Run:   python convert.py

  3. Collect output from Output/:
     - SKDUPD.r   — timetable EDIFACT
     - TSDUPD.r   — station EDIFACT

The script auto-detects what to convert based on what's in Source/.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure imports work regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

SOURCE_DIR = Path(__file__).resolve().parent / "Source"
OUTPUT_DIR = Path(__file__).resolve().parent / "Output"
CONFIG_DIR = Path(__file__).resolve().parent / "Configuration"

STATION_PATTERNS = ["RailStations", "stations", "SiteFrame", "tiamat", "TSDUPD"]


def _find_station_file() -> Path | None:
    """Find the station file in Source/ (ZIP or XML)."""
    # Check Source/TSDUPD/ subfolder first
    tsdupd_dir = SOURCE_DIR / "TSDUPD"
    if tsdupd_dir.exists():
        files = sorted(tsdupd_dir.glob("*.zip"), reverse=True) + sorted(tsdupd_dir.glob("*.xml"), reverse=True)
        if files:
            return files[0]

    # Then look in Source/ root for known station patterns
    for pattern in STATION_PATTERNS:
        for ext in ("*.zip", "*.xml"):
            matches = [f for f in SOURCE_DIR.glob(ext) if pattern.lower() in f.name.lower()]
            if matches:
                return sorted(matches, reverse=True)[0]

    # Fallback: any XML that isn't clearly a timetable
    for xml in sorted(SOURCE_DIR.glob("*.xml"), reverse=True):
        if "timetable" not in xml.name.lower():
            return xml

    return None


def _find_timetable_zips(station_file: Path | None) -> list[Path]:
    """Find timetable ZIPs in Source/ (everything that isn't the station file)."""
    exclude_name = station_file.name.lower() if station_file else ""
    zips = []
    for z in sorted(SOURCE_DIR.glob("*.zip")):
        if z.name.lower() == exclude_name:
            continue
        # Skip known station patterns
        if any(p.lower() in z.name.lower() for p in STATION_PATTERNS):
            continue
        zips.append(z)
    return zips


def main() -> None:
    print("=" * 60)
    print("  NeTEx → EDIFACT Converter")
    print("=" * 60)

    if not SOURCE_DIR.exists():
        SOURCE_DIR.mkdir(parents=True)
        print(f"\nCreated {SOURCE_DIR.relative_to(SOURCE_DIR.parent)}/")
        print("Place your NeTEx files there and run again.")
        return

    # Discover files
    station_file = _find_station_file()
    timetable_zips = _find_timetable_zips(station_file)

    if not station_file and not timetable_zips:
        print(f"\nNo NeTEx files found in {SOURCE_DIR.relative_to(SOURCE_DIR.parent)}/")
        print("Place station and/or timetable files there and run again.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nSource:  {SOURCE_DIR.relative_to(SOURCE_DIR.parent)}/")
    print(f"Output:  {OUTPUT_DIR.relative_to(OUTPUT_DIR.parent)}/")
    print()

    # ---- TSDUPD (stations) ----
    if station_file:
        print(f"Station file: {station_file.name}")
        tsdupd_output = OUTPUT_DIR / "TSDUPD.r"
        try:
            from Converter.TSDUPD.netex2tsdupd import convert as tsdupd_convert
            # TSDUPD convert() scans a directory for newest file;
            # pass the directory containing our station file.
            tsdupd_convert(
                input_dir=station_file.parent,
                output_file=tsdupd_output,
                originator=None,
            )
            print(f"  → {tsdupd_output.relative_to(OUTPUT_DIR.parent)}")
        except Exception as e:
            print(f"  ✗ TSDUPD failed: {e}")
    else:
        print("No station file found — skipping TSDUPD.")

    # ---- SKDUPD (timetables) ----
    if timetable_zips and station_file:
        print(f"\nTimetable ZIPs: {len(timetable_zips)}")
        for z in timetable_zips:
            print(f"  - {z.name}")

        skdupd_output = OUTPUT_DIR / "SKDUPD.r"

        if len(timetable_zips) == 1:
            # Single operator — use direct converter
            try:
                from Converter.SKDUPD.netex2skdupd import convert as skdupd_convert
                skdupd_convert(
                    timetable_zip=timetable_zips[0],
                    station_zip=station_file,
                    output_file=skdupd_output,
                    originator=None,
                    config_dir=CONFIG_DIR if CONFIG_DIR.exists() else None,
                )
                print(f"  → {skdupd_output.relative_to(OUTPUT_DIR.parent)}")
            except Exception as e:
                print(f"  ✗ SKDUPD failed: {e}")
        else:
            # Multi-operator — use batch converter
            try:
                from Converter.SKDUPD.run_conversion import convert_batch
                from Converter.Shared.netex_helpers import participant_ref
                from Converter.Shared.edifact_mappings import resolve_originator
                import zipfile, xml.etree.ElementTree as ET

                # Derive originator from first timetable's ParticipantRef
                derived_originator = None
                with zipfile.ZipFile(timetable_zips[0]) as z:
                    xml_names = [n for n in z.namelist() if n.endswith(".xml")]
                    if xml_names:
                        root = ET.fromstring(z.read(xml_names[0]))
                        participant = participant_ref(root)
                        if participant:
                            derived_originator = resolve_originator(participant, None)

                if not derived_originator:
                    raise RuntimeError(
                        "Cannot derive originator — no ParticipantRef found in timetable files. "
                        "Use run.py with --originator <RICS-code> instead."
                    )

                convert_batch(
                    source_dir=SOURCE_DIR,
                    station_zip=station_file,
                    output_file=skdupd_output,
                    originator=derived_originator,
                    config_dir=CONFIG_DIR if CONFIG_DIR.exists() else Path("."),
                )
                print(f"  → {skdupd_output.relative_to(OUTPUT_DIR.parent)}")
            except Exception as e:
                print(f"  ✗ SKDUPD batch failed: {e}")
    elif timetable_zips and not station_file:
        print(f"\n⚠ Found {len(timetable_zips)} timetable ZIPs but no station file.")
        print("  Add a station file to Source/ to generate SKDUPD.")
    else:
        print("\nNo timetable ZIPs found — skipping SKDUPD.")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
