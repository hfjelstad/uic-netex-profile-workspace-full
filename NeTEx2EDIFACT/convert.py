# -*- coding: utf-8 -*-
"""
convert.py — Zero-config converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Put NeTEx files in Source/, run this script, get EDIFACT in Output/.

  1. Place files in Source/:
     - One or more NeTEx files (.zip or .xml)
     - Can be separate station + timetable files, or one combined delivery

  2. Run:   python convert.py

  3. Collect output from Output/:
     - SKDUPD.r   — timetable EDIFACT (if timetable data found)
     - TSDUPD.r   — station EDIFACT (if station data found)

The script peeks inside each file to detect what it contains (SiteFrame,
TimetableFrame, or both). No naming conventions required.
"""

from __future__ import annotations

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

# Ensure imports work regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

SOURCE_DIR = Path(__file__).resolve().parent / "Source"
OUTPUT_DIR = Path(__file__).resolve().parent / "Output"
CONFIG_DIR = Path(__file__).resolve().parent / "Configuration"

NS = "http://www.netex.org.uk/netex"


# ---------------------------------------------------------------------------
# Content detection
# ---------------------------------------------------------------------------

class FileContent(NamedTuple):
    path: Path
    has_stops: bool       # Contains StopPlace elements (→ TSDUPD)
    has_timetable: bool   # Contains ServiceJourney elements (→ SKDUPD)


def _peek_xml_root(root: ET.Element) -> tuple[bool, bool]:
    """Check whether an XML tree contains station and/or timetable data."""
    has_stops = root.find(f".//{{{NS}}}StopPlace") is not None
    has_timetable = root.find(f".//{{{NS}}}ServiceJourney") is not None
    return has_stops, has_timetable


def _peek_file(path: Path) -> FileContent:
    """Peek inside a NeTEx file (ZIP or XML) to detect content type."""
    has_stops = False
    has_timetable = False

    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path) as z:
                xml_names = [n for n in z.namelist() if n.lower().endswith(".xml")]
                for name in xml_names:
                    root = ET.fromstring(z.read(name))
                    s, t = _peek_xml_root(root)
                    has_stops = has_stops or s
                    has_timetable = has_timetable or t
                    if has_stops and has_timetable:
                        break
        except (zipfile.BadZipFile, ET.ParseError):
            pass
    elif path.suffix.lower() == ".xml":
        try:
            root = ET.parse(str(path)).getroot()
            has_stops, has_timetable = _peek_xml_root(root)
        except ET.ParseError:
            pass

    return FileContent(path=path, has_stops=has_stops, has_timetable=has_timetable)


def _discover_files() -> list[FileContent]:
    """Scan Source/ (and Source/TSDUPD/) for NeTEx files and classify them."""
    paths: list[Path] = []
    for ext in ("*.zip", "*.xml"):
        paths.extend(SOURCE_DIR.glob(ext))
    # Also check Source/TSDUPD/ subfolder
    tsdupd_dir = SOURCE_DIR / "TSDUPD"
    if tsdupd_dir.exists():
        for ext in ("*.zip", "*.xml"):
            paths.extend(tsdupd_dir.glob(ext))

    print(f"Scanning {len(paths)} file(s) in Source/ ...")
    results = []
    for p in sorted(paths):
        fc = _peek_file(p)
        label = []
        if fc.has_stops:
            label.append("stations")
        if fc.has_timetable:
            label.append("timetable")
        if not label:
            label.append("unknown")
        print(f"  {p.name:40s}  [{', '.join(label)}]")
        results.append(fc)
    return results


def main() -> None:
    print("=" * 60)
    print("  NeTEx → EDIFACT Converter")
    print("=" * 60)

    if not SOURCE_DIR.exists():
        SOURCE_DIR.mkdir(parents=True)
        print(f"\nCreated {SOURCE_DIR.relative_to(SOURCE_DIR.parent)}/")
        print("Place your NeTEx files there and run again.")
        return

    # Discover and classify files by content
    files = _discover_files()

    if not files:
        print(f"\nNo NeTEx files (.zip/.xml) found in {SOURCE_DIR.relative_to(SOURCE_DIR.parent)}/")
        print("Place your NeTEx files there and run again.")
        return

    # Classify: which files have station data, which have timetables?
    station_files = [f for f in files if f.has_stops]
    timetable_files = [f for f in files if f.has_timetable]
    # Files with both (combined deliveries) contribute to both
    combined_files = [f for f in files if f.has_stops and f.has_timetable]

    if not station_files and not timetable_files:
        print("\nNo recognizable NeTEx content found (no StopPlace or ServiceJourney elements).")
        print("Check that your files contain valid NeTEx data.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput:  {OUTPUT_DIR.relative_to(OUTPUT_DIR.parent)}/")

    # ---- TSDUPD (stations) ----
    if station_files:
        # Use the first station file (prefer a dedicated one over a combined file)
        dedicated_station = [f for f in station_files if not f.has_timetable]
        sf = dedicated_station[0] if dedicated_station else station_files[0]
        print(f"\n{'─'*60}")
        print(f"TSDUPD — stations from: {sf.path.name}")
        tsdupd_output = OUTPUT_DIR / "TSDUPD.r"
        try:
            from Converter.TSDUPD.netex2tsdupd import convert as tsdupd_convert
            tsdupd_convert(
                input_dir=sf.path.parent,
                output_file=tsdupd_output,
                originator=None,
            )
            print(f"  ✓ {tsdupd_output.name}")
        except Exception as e:
            print(f"  ✗ TSDUPD failed: {e}")
    else:
        print("\nNo station data found — skipping TSDUPD.")

    # ---- SKDUPD (timetables) ----
    if timetable_files:
        # Station file is needed for UIC code resolution
        station_for_skdupd = None
        if station_files:
            dedicated = [f for f in station_files if not f.has_timetable]
            station_for_skdupd = (dedicated[0] if dedicated else station_files[0]).path

        # For combined files (one file with both), the station data is in the same file
        if not station_for_skdupd and combined_files:
            station_for_skdupd = combined_files[0].path

        if not station_for_skdupd:
            print(f"\n⚠ Found timetable data but no station data for UIC code resolution.")
            print("  Add a file containing StopPlace elements to Source/.")
        else:
            # Timetable ZIPs (exclude the station-only file)
            tt_zips = [f.path for f in timetable_files if f.path.suffix.lower() == ".zip"]
            # If the station file is also a timetable ZIP, include it
            # If no ZIPs but we have combined XML files, handle that
            if not tt_zips:
                # Combined XML with both — use it as timetable source too
                tt_zips = [f.path for f in combined_files if f.path.suffix.lower() == ".zip"]

            if not tt_zips:
                print(f"\n⚠ Timetable data found in XML but SKDUPD converter requires ZIP input.")
                print("  Package timetable XML into a ZIP file.")
            else:
                print(f"\n{'─'*60}")
                print(f"SKDUPD — {len(tt_zips)} timetable file(s), stations from: {station_for_skdupd.name}")
                for z in tt_zips:
                    print(f"  - {z.name}")

                skdupd_output = OUTPUT_DIR / "SKDUPD.r"

                if len(tt_zips) == 1:
                    try:
                        from Converter.SKDUPD.netex2skdupd import convert as skdupd_convert
                        skdupd_convert(
                            timetable_zip=tt_zips[0],
                            station_zip=station_for_skdupd,
                            output_file=skdupd_output,
                            originator=None,
                            config_dir=CONFIG_DIR if CONFIG_DIR.exists() else None,
                        )
                        print(f"  ✓ {skdupd_output.name}")
                    except Exception as e:
                        print(f"  ✗ SKDUPD failed: {e}")
                else:
                    try:
                        from Converter.SKDUPD.run_conversion import convert_batch
                        from Converter.Shared.netex_helpers import participant_ref
                        from Converter.Shared.edifact_mappings import resolve_originator

                        # Derive originator from first timetable
                        derived_originator = None
                        with zipfile.ZipFile(tt_zips[0]) as z:
                            xml_names = [n for n in z.namelist() if n.endswith(".xml")]
                            if xml_names:
                                root = ET.fromstring(z.read(xml_names[0]))
                                participant = participant_ref(root)
                                if participant:
                                    derived_originator = resolve_originator(participant, None)

                        if not derived_originator:
                            raise RuntimeError(
                                "Cannot derive originator — no ParticipantRef in timetable files. "
                                "Use run.py with --originator <RICS-code> instead."
                            )

                        convert_batch(
                            source_dir=SOURCE_DIR,
                            station_zip=station_for_skdupd,
                            output_file=skdupd_output,
                            originator=derived_originator,
                            config_dir=CONFIG_DIR if CONFIG_DIR.exists() else Path("."),
                        )
                        print(f"  ✓ {skdupd_output.name}")
                    except Exception as e:
                        print(f"  ✗ SKDUPD batch failed: {e}")
    else:
        print("\nNo timetable data found — skipping SKDUPD.")

    print(f"\n{'═'*60}")
    print("  Done. Output in Output/")
    print("═" * 60)


if __name__ == "__main__":
    main()
