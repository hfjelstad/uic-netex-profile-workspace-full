#!/usr/bin/env python3
"""
Trim NSR rail station NeTEx exports for UIC profile work.

Primary goal:
- Keep StopPlaces, Quays, and GroupOfStopPlaces context.
- Remove ScheduledStopPoint / PassengerStopAssignment-heavy parts.

This script is namespace-safe and works directly on PublicationDelivery XML.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


NETEX_NS = "http://www.netex.org.uk/netex"
GML_NS = "http://www.opengis.net/gml/3.2"
SIRI_NS = "http://www.siri.org.uk/siri"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


@dataclass
class TrimStats:
    removed_service_frames: int = 0
    removed_scheduled_stop_points: int = 0
    removed_passenger_stop_assignments: int = 0
    removed_passenger_stop_points: int = 0
    removed_scheduled_stop_point_refs: int = 0
    removed_passenger_stop_assignment_refs: int = 0
    removed_stop_assignment_containers: int = 0
    removed_scheduled_stop_point_containers: int = 0
    converted_uic_keyvalues: int = 0
    padded_uic_codes_to_9: int = 0
    removed_keylist_containers: int = 0
    removed_keyvalue_entries: int = 0
    removed_empty_keylists: int = 0
    flattened_privatecodes_wrappers: int = 0
    removed_stopplace_valid_between: int = 0


def iter_with_parent(root: ET.Element) -> Iterable[tuple[ET.Element, ET.Element]]:
    for parent in root.iter():
        for child in list(parent):
            yield parent, child


def namespaced_tag(reference: ET.Element, name: str) -> str:
    if reference.tag.startswith("{"):
        ns_uri = reference.tag[1:].split("}", 1)[0]
        return f"{{{ns_uri}}}{name}"
    return name


def first_child_by_localname(parent: ET.Element, name: str) -> Optional[ET.Element]:
    for child in list(parent):
        if local_name(child.tag) == name:
            return child
    return None


def insert_before_first(parent: ET.Element, child: ET.Element, before_names: set[str]) -> None:
    """Insert child before the first matching local-name sibling, else append."""
    children = list(parent)
    for idx, sibling in enumerate(children):
        if local_name(sibling.tag) in before_names:
            parent.insert(idx, child)
            return
    parent.append(child)


def has_private_code_value(owner: ET.Element, value: str) -> bool:
    for child in list(owner):
        if local_name(child.tag) != "PrivateCode":
            continue
        if (child.text or "") == value:
            return True
    return False


def has_typed_private_code_in_wrapper(owner: ET.Element, code_type: str, value: str) -> bool:
    private_codes = first_child_by_localname(owner, "privateCodes")
    if private_codes is None:
        return False
    for child in list(private_codes):
        if local_name(child.tag) != "PrivateCode":
            continue
        if child.attrib.get("type") == code_type and (child.text or "") == value:
            return True
    return False


def upsert_stopplace_private_code(owner: ET.Element, value: str) -> None:
    """Set a single StopPlace PrivateCode value in a schema-friendly way."""
    for child in list(owner):
        if local_name(child.tag) != "PrivateCode":
            continue
        child.attrib.clear()
        child.text = value
        return

    private_code = ET.Element(namespaced_tag(owner, "PrivateCode"))
    private_code.text = value
    insert_before_first(
        parent=owner,
        child=private_code,
        before_names={
            "infoLinks",
            "members",
            "types",
            "Centroid",
            "projections",
            "ParentZoneRef",
            "placeTypes",
            "Url",
            "Image",
            "PostalAddress",
            "RoadAddress",
            "AccessibilityAssessment",
            "AccessModes",
            "NameSuffix",
            "alternativeNames",
            "CrossRoad",
            "Landmark",
            "PublicUse",
            "Covered",
            "Gated",
            "Lighting",
            "AllAreasWheelchairAccessible",
            "PersonCapacity",
            "Presentation",
            "facilities",
            "TopographicPlaceRef",
            "TopographicPlaceView",
            "additionalTopographicPlaces",
            "SiteType",
            "AtCentre",
            "Locale",
            "OrganisationRef_Dummy",
            "OrganisationRef",
            "TransportOrganisationRef",
            "OtherOrganisationRef",
            "OnlineServiceOperatorRef",
            "RetailConsortiumRef",
            "OperatorRef",
            "AuthorityRef",
            "TravelAgentRef",
            "ServicedOrganisationRef",
            "ManagementAgentRef",
            "GeneralOrganisationRef",
            "OperatingOrganisationView",
            "ParentSiteRef",
            "adjacentSites",
            "ContainedInPlaceRef",
            "levels",
            "entrances",
            "siteStructures",
            "equipmentPlace",
            "accessSpaces",
            "pathLinks",
            "pathJunctions",
            "accesses",
            "navigationPaths",
            "vehicleStoppingPlaces",
            "quays",
        },
    )


def upsert_stopplace_private_code_typed(owner: ET.Element, code_type: str, value: str) -> None:
    """Set a typed PrivateCode in a privateCodes wrapper (Nordic-style payload)."""
    private_codes = first_child_by_localname(owner, "privateCodes")
    if private_codes is None:
        private_codes = ET.Element(namespaced_tag(owner, "privateCodes"))
        insert_before_first(
            parent=owner,
            child=private_codes,
            before_names={
                "infoLinks",
                "members",
                "types",
                "Centroid",
                "projections",
                "ParentZoneRef",
                "placeTypes",
                "Url",
                "Image",
                "PostalAddress",
                "RoadAddress",
                "AccessibilityAssessment",
                "AccessModes",
                "NameSuffix",
                "alternativeNames",
                "CrossRoad",
                "Landmark",
                "PublicUse",
                "Covered",
                "Gated",
                "Lighting",
                "AllAreasWheelchairAccessible",
                "PersonCapacity",
                "Presentation",
                "facilities",
                "TopographicPlaceRef",
                "TopographicPlaceView",
                "additionalTopographicPlaces",
                "SiteType",
                "AtCentre",
                "Locale",
                "OrganisationRef_Dummy",
                "OrganisationRef",
                "TransportOrganisationRef",
                "OtherOrganisationRef",
                "OnlineServiceOperatorRef",
                "RetailConsortiumRef",
                "OperatorRef",
                "AuthorityRef",
                "TravelAgentRef",
                "ServicedOrganisationRef",
                "ManagementAgentRef",
                "GeneralOrganisationRef",
                "OperatingOrganisationView",
                "ParentSiteRef",
                "adjacentSites",
                "ContainedInPlaceRef",
                "levels",
                "entrances",
                "siteStructures",
                "equipmentPlace",
                "accessSpaces",
                "pathLinks",
                "pathJunctions",
                "accesses",
                "navigationPaths",
                "vehicleStoppingPlaces",
                "quays",
            },
        )

    for child in list(private_codes):
        if local_name(child.tag) != "PrivateCode":
            continue
        if child.attrib.get("type") == code_type:
            child.text = value
            return

    private_code = ET.Element(namespaced_tag(owner, "PrivateCode"), attrib={"type": code_type})
    private_code.text = value
    private_codes.append(private_code)


def normalize_uic_code(value: str, pad_uic_to_9: bool) -> tuple[str, bool]:
    """Normalize uicCode values for output interoperability.

    Current rule:
    - If enabled and value is a 7-digit numeric code, prefix with "00".
    """
    if pad_uic_to_9 and value.isdigit() and len(value) == 7:
        return f"00{value}", True
    return value, False


def convert_uic_keyvalues(
    root: ET.Element,
    stats: TrimStats,
    pad_uic_to_9: bool,
    use_typed_privatecodes_wrapper: bool,
) -> None:
    """Convert keyList/KeyValue with Key='uicCode' (or 'iffCode') into privateCodes/PrivateCode.

    Tiamat exports for Nordic neighbour stations (SE, DK) carry the UIC station
    number under Key='iffCode' (typically a 7-digit value such as '7400044' for
    Helsingborg C — country code 74 + station 00044, without the check digit).
    We treat iffCode as a fallback UIC source and let the standard pad-to-9
    rule prefix it with leading zeros so it lines up with the existing 9-digit
    Norwegian uicCode values already present in the dataset.

    When a StopPlace exposes BOTH uicCode and iffCode, uicCode wins (e.g.
    Göteborg C: uicCode=7401318, iffCode=7400002 -> keep 007401318).
    """
    parent_map = {child: parent for parent in root.iter() for child in list(parent)}

    # First pass: record which StopPlaces already have a uicCode KeyValue so
    # iffCode can be skipped for those owners.
    stopplaces_with_uic: set = set()
    for element in root.iter():
        if local_name(element.tag) != "KeyValue":
            continue
        key_elem = first_child_by_localname(element, "Key")
        if key_elem is None or (key_elem.text or "").strip() != "uicCode":
            continue
        key_list = parent_map.get(element)
        owner = parent_map.get(key_list) if key_list is not None else None
        if owner is not None and local_name(owner.tag) == "StopPlace":
            stopplaces_with_uic.add(id(owner))

    for element in list(root.iter()):
        if local_name(element.tag) != "KeyValue":
            continue

        key_elem = first_child_by_localname(element, "Key")
        value_elem = first_child_by_localname(element, "Value")
        key_text = (key_elem.text or "").strip() if key_elem is not None else ""
        value_text = (value_elem.text or "").strip() if value_elem is not None else ""

        if key_text not in {"uicCode", "iffCode"}:
            continue

        key_list = parent_map.get(element)
        if key_list is None:
            continue

        owner = parent_map.get(key_list)
        if owner is None:
            continue

        # Keep uicCode only on StopPlace for schema-safe output.
        if local_name(owner.tag) != "StopPlace":
            key_list.remove(element)
            stats.removed_keyvalue_entries += 1
            if local_name(key_list.tag) == "keyList" and len(list(key_list)) == 0:
                owner.remove(key_list)
                stats.removed_empty_keylists += 1
            continue

        # Skip iffCode if this StopPlace already has a (typically Norwegian) uicCode.
        if key_text == "iffCode" and id(owner) in stopplaces_with_uic:
            key_list.remove(element)
            stats.removed_keyvalue_entries += 1
            if local_name(key_list.tag) == "keyList" and len(list(key_list)) == 0:
                owner.remove(key_list)
                stats.removed_empty_keylists += 1
            continue

        normalized_value, padded = normalize_uic_code(value=value_text, pad_uic_to_9=pad_uic_to_9)
        if padded:
            stats.padded_uic_codes_to_9 += 1

        if normalized_value:
            if use_typed_privatecodes_wrapper:
                if not has_typed_private_code_in_wrapper(owner, code_type="uicCode", value=normalized_value):
                    upsert_stopplace_private_code_typed(owner, code_type="uicCode", value=normalized_value)
            else:
                if not has_private_code_value(owner, value=normalized_value):
                    upsert_stopplace_private_code(owner, value=normalized_value)
        stats.converted_uic_keyvalues += 1

        key_list.remove(element)
        stats.removed_keyvalue_entries += 1
        if local_name(key_list.tag) == "keyList" and len(list(key_list)) == 0:
            owner.remove(key_list)
            stats.removed_empty_keylists += 1


def remove_all_keylist_content(root: ET.Element, stats: TrimStats) -> None:
    """Remove all remaining keyList/KeyValue metadata for profile-clean output."""
    parent_map = {child: parent for parent in root.iter() for child in list(parent)}

    for element in list(root.iter()):
        if local_name(element.tag) != "KeyValue":
            continue

        key_list = parent_map.get(element)
        if key_list is None:
            continue

        owner = parent_map.get(key_list)
        key_list.remove(element)
        stats.removed_keyvalue_entries += 1

        if owner is not None and local_name(key_list.tag) == "keyList" and len(list(key_list)) == 0:
            owner.remove(key_list)
            stats.removed_empty_keylists += 1

    for parent, _ in list(iter_with_parent(root)):
        stats.removed_keylist_containers += remove_children_by_localname(parent, {"keyList"})


def flatten_privatecodes_wrappers(root: ET.Element, stats: TrimStats) -> None:
    """Replace non-standard <privateCodes> wrapper with direct <PrivateCode> children."""
    for parent, child in list(iter_with_parent(root)):
        if local_name(child.tag) != "privateCodes":
            continue
        insert_at = list(parent).index(child)
        for nested in list(child):
            if local_name(nested.tag) == "PrivateCode":
                child.remove(nested)
                parent.insert(insert_at, nested)
                insert_at += 1
        parent.remove(child)
        stats.flattened_privatecodes_wrappers += 1


def remove_invalid_stopplace_children(root: ET.Element, stats: TrimStats) -> None:
    """Drop known StopPlace children that break v2.0 validation in this source."""
    for stop_place in list(root.iter()):
        if local_name(stop_place.tag) != "StopPlace":
            continue
        stats.removed_stopplace_valid_between += remove_children_by_localname(stop_place, {"ValidBetween"})


def prune_stopplace_quay_to_core(root: ET.Element, keep_typed_privatecodes_wrapper: bool) -> None:
    """Keep a compact, schema-oriented subset for StopPlace and Quay."""
    stop_place_keep = {
        "Name",
        "ShortName",
        "Description",
        "PrivateCode",
        "PublicCode",
        "Centroid",
        "TransportMode",
        "StopPlaceType",
        "Weighting",
        "TopographicPlaceRef",
        "ParentSiteRef",
        "quays",
    }
    if keep_typed_privatecodes_wrapper:
        stop_place_keep.add("privateCodes")
    quay_keep = {
        "Name",
        "ShortName",
        "Description",
        "PublicCode",
        "Centroid",
        "CompassBearing",
    }

    for elem in list(root.iter()):
        ln = local_name(elem.tag)
        if ln == "StopPlace":
            for child in list(elem):
                if local_name(child.tag) not in stop_place_keep:
                    elem.remove(child)
        elif ln == "Quay":
            for child in list(elem):
                if local_name(child.tag) not in quay_keep:
                    elem.remove(child)


def remove_children_by_localname(
    parent: ET.Element,
    names: set[str],
) -> int:
    removed = 0
    for child in list(parent):
        if local_name(child.tag) in names:
            parent.remove(child)
            removed += 1
    return removed


def prune_site_frame(site_frame: ET.Element) -> None:
    """Keep only SiteFrame containers relevant for stop place context."""
    keep = {
        "FrameDefaults",
        "ValidBetween",
        "TypeOfFrameRef",
        "stopPlaces",
        "groupsOfStopPlaces",
    }
    for child in list(site_frame):
        if local_name(child.tag) not in keep:
            site_frame.remove(child)


def prune_resource_frame(resource_frame: ET.Element) -> None:
    """Keep only value-type context useful for grouping references."""
    keep = {
        "FrameDefaults",
        "ValidBetween",
        "TypeOfFrameRef",
        "typesOfValue",
    }
    for child in list(resource_frame):
        if local_name(child.tag) not in keep:
            resource_frame.remove(child)


def trim_in_place(root: ET.Element, keep_service_frames: bool) -> TrimStats:
    stats = TrimStats()

    # Remove noisy containers and leafs everywhere first.
    for parent, _ in list(iter_with_parent(root)):
        stats.removed_scheduled_stop_point_containers += remove_children_by_localname(
            parent,
            {"scheduledStopPoints"},
        )
        stats.removed_stop_assignment_containers += remove_children_by_localname(
            parent,
            {"stopAssignments", "passengerStopPoints", "passengerPoints"},
        )

    for parent, child in list(iter_with_parent(root)):
        ln = local_name(child.tag)
        if ln == "ScheduledStopPoint":
            parent.remove(child)
            stats.removed_scheduled_stop_points += 1
        elif ln == "PassengerStopAssignment":
            parent.remove(child)
            stats.removed_passenger_stop_assignments += 1
        elif ln == "PassengerStopPoint":
            parent.remove(child)
            stats.removed_passenger_stop_points += 1
        elif ln == "ScheduledStopPointRef":
            parent.remove(child)
            stats.removed_scheduled_stop_point_refs += 1
        elif ln == "PassengerStopAssignmentRef":
            parent.remove(child)
            stats.removed_passenger_stop_assignment_refs += 1

    data_objects: Optional[ET.Element] = None
    for elem in root.iter():
        if local_name(elem.tag) == "dataObjects":
            data_objects = elem
            break

    if data_objects is None:
        return stats

    # Keep frame-level structure focused on stop place context.
    for frame in list(data_objects):
        ln = local_name(frame.tag)
        if ln == "ServiceFrame" and not keep_service_frames:
            data_objects.remove(frame)
            stats.removed_service_frames += 1
            continue
        if ln == "SiteFrame":
            prune_site_frame(frame)
        elif ln == "ResourceFrame":
            prune_resource_frame(frame)
        elif ln != "CompositeFrame":
            data_objects.remove(frame)

    # Handle CompositeFrame case by retaining only SiteFrame/ResourceFrame in frames.
    for composite in list(data_objects):
        if local_name(composite.tag) != "CompositeFrame":
            continue
        for child in list(composite):
            if local_name(child.tag) != "frames":
                continue
            for nested_frame in list(child):
                ln = local_name(nested_frame.tag)
                if ln == "ServiceFrame" and not keep_service_frames:
                    child.remove(nested_frame)
                    stats.removed_service_frames += 1
                elif ln == "SiteFrame":
                    prune_site_frame(nested_frame)
                elif ln == "ResourceFrame":
                    prune_resource_frame(nested_frame)
                elif ln not in {"SiteFrame", "ResourceFrame"}:
                    child.remove(nested_frame)

    return stats


def write_xml(tree: ET.ElementTree, output_path: Path, pretty: bool) -> None:
    ET.register_namespace("", NETEX_NS)
    ET.register_namespace("gml", GML_NS)
    ET.register_namespace("siri", SIRI_NS)
    ET.register_namespace("xsi", XSI_NS)

    if pretty:
        try:
            ET.indent(tree, space="  ")
        except AttributeError:
            # ET.indent is Python 3.9+ only; continue without pretty-print.
            pass
    tree.write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trim NSR rail station NeTEx to StopPlaces/Quays/groupings-focused content.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input NSR NeTEx XML file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output XML file path. Default: <input>.trimmed.xml",
    )
    parser.add_argument(
        "--keep-service-frames",
        action="store_true",
        help="Keep ServiceFrame containers (still prunes SSP and stopAssignments).",
    )
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        help="Disable XML pretty indentation.",
    )
    parser.add_argument(
        "--pad-uic-to-9",
        action="store_true",
        help="If set, pad 7-digit numeric uicCode values to 9 digits by prefixing 00.",
    )
    parser.add_argument(
        "--typed-privatecodes-wrapper",
        action="store_true",
        help="Emit uicCode as privateCodes/PrivateCode[@type='uicCode'] (may not validate against base v2.0 XSD).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path.with_suffix(".trimmed.xml")

    tree = ET.parse(input_path)
    root = tree.getroot()

    stats = trim_in_place(root=root, keep_service_frames=args.keep_service_frames)
    convert_uic_keyvalues(
        root=root,
        stats=stats,
        pad_uic_to_9=args.pad_uic_to_9,
        use_typed_privatecodes_wrapper=args.typed_privatecodes_wrapper,
    )
    remove_all_keylist_content(root=root, stats=stats)
    if not args.typed_privatecodes_wrapper:
        flatten_privatecodes_wrappers(root=root, stats=stats)
    remove_invalid_stopplace_children(root=root, stats=stats)
    prune_stopplace_quay_to_core(
        root=root,
        keep_typed_privatecodes_wrapper=args.typed_privatecodes_wrapper,
    )
    write_xml(tree=tree, output_path=output_path, pretty=not args.no_pretty)

    print("Trim completed")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Removed ServiceFrame containers: {stats.removed_service_frames}")
    print(f"Removed <scheduledStopPoints> containers: {stats.removed_scheduled_stop_point_containers}")
    print(f"Removed <stopAssignments>/<passengerPoints> containers: {stats.removed_stop_assignment_containers}")
    print(f"Removed ScheduledStopPoint elements: {stats.removed_scheduled_stop_points}")
    print(f"Removed PassengerStopAssignment elements: {stats.removed_passenger_stop_assignments}")
    print(f"Removed PassengerStopPoint elements: {stats.removed_passenger_stop_points}")
    print(f"Removed ScheduledStopPointRef elements: {stats.removed_scheduled_stop_point_refs}")
    print(f"Removed PassengerStopAssignmentRef elements: {stats.removed_passenger_stop_assignment_refs}")
    print(f"Converted uicCode KeyValue entries to PrivateCode: {stats.converted_uic_keyvalues}")
    print(f"Typed privateCodes wrapper mode: {args.typed_privatecodes_wrapper}")
    print(f"Padded uicCode values to 9 digits: {stats.padded_uic_codes_to_9}")
    print(f"Removed KeyValue entries: {stats.removed_keyvalue_entries}")
    print(f"Removed keyList containers: {stats.removed_keylist_containers}")
    print(f"Removed empty keyList containers: {stats.removed_empty_keylists}")
    print(f"Flattened privateCodes wrappers: {stats.flattened_privatecodes_wrappers}")
    print(f"Removed StopPlace ValidBetween elements: {stats.removed_stopplace_valid_between}")


if __name__ == "__main__":
    main()
