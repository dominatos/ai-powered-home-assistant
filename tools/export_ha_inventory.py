#!/usr/bin/env python3
"""Export a sanitized Home Assistant inventory snapshot for automation work."""

from __future__ import annotations

import argparse
import json
import re
import sys
import yaml
from pathlib import Path


DEFAULT_STORAGE = Path("/homeassistant/.storage")
DEFAULT_OUTPUT = Path("ha_device_inventory.json")
DEFAULT_TEXT_OUTPUT = Path("inventory.txt")
DEFAULT_NUMBER_MAP_OUTPUT = Path("inventory_numbers.json")
DEFAULT_VIRTUAL_OUTPUT = Path("virtual-inventory.json")


def load_storage_json(path: Path, optional: bool = False) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        if optional:
            return []
        raise SystemExit(f"Missing required storage file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")

    if not isinstance(data, dict) or "data" not in data or not isinstance(data["data"], dict):
        raise SystemExit(f"Unexpected structure in {path}")

    entries = (
        data["data"].get("entities")
        or data["data"].get("devices")
        or data["data"].get("areas")
        or data["data"].get("items")
    )
    if not isinstance(entries, list):
        if optional and not entries:
            return []
        raise SystemExit(f"Unexpected entries list in {path}")

    return entries


def index_areas(areas: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for area in areas:
        area_id = area.get("id")
        if area_id:
            indexed[area_id] = {
                "area_id": area_id,
                "area_name": area.get("name"),
                "floor_id": area.get("floor_id"),
                "labels": sorted(area.get("labels", [])),
            }
    return indexed


def index_devices(devices: list[dict], areas_by_id: dict[str, dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for device in devices:
        device_id = device.get("id")
        if not device_id:
            continue
        area = areas_by_id.get(device.get("area_id"), {})
        indexed[device_id] = {
            "device_id": device_id,
            "device_name": device.get("name_by_user") or device.get("name"),
            "manufacturer": device.get("manufacturer"),
            "model": device.get("model"),
            "hw_version": device.get("hw_version"),
            "sw_version": device.get("sw_version"),
            "area_id": device.get("area_id"),
            "area_name": area.get("area_name"),
            "labels": sorted(device.get("labels", [])),
            "config_entries": sorted(device.get("config_entries", [])),
            "via_device_id": device.get("via_device_id"),
            "disabled": bool(device.get("disabled_by")),
        }
    return indexed


def map_entity(entity: dict, devices_by_id: dict[str, dict], areas_by_id: dict[str, dict]) -> dict:
    device = devices_by_id.get(entity.get("device_id"), {})
    area = areas_by_id.get(entity.get("area_id"), {})
    return {
        "entity_id": entity.get("entity_id"),
        "original_name": entity.get("original_name"),
        "name": entity.get("name"),
        "platform": entity.get("platform"),
        "device_class": entity.get("device_class"),
        "original_device_class": entity.get("original_device_class"),
        "original_icon": entity.get("original_icon"),
        "unit_of_measurement": entity.get("unit_of_measurement"),
        "state_class": entity.get("state_class"),
        "entity_category": entity.get("entity_category"),
        "hidden": bool(entity.get("hidden_by")),
        "disabled": bool(entity.get("disabled_by")),
        "has_entity_name": entity.get("has_entity_name"),
        "aliases": sorted(entity.get("aliases", [])),
        "labels": sorted(entity.get("labels", [])),
        "device": device,
        "area": {
            "area_id": entity.get("area_id") or device.get("area_id"),
            "area_name": area.get("area_name") or device.get("area_name"),
        },
    }


def build_inventory(storage_dir: Path) -> dict:
    entities = load_storage_json(storage_dir / "core.entity_registry")
    devices = load_storage_json(storage_dir / "core.device_registry")
    areas = load_storage_json(storage_dir / "core.area_registry")
    zones = load_storage_json(storage_dir / "core.zone_registry", optional=True)

    areas_by_id = index_areas(areas)
    devices_by_id = index_devices(devices, areas_by_id)

    mapped_entities = [map_entity(entity, devices_by_id, areas_by_id) for entity in entities]
    mapped_entities.sort(key=lambda item: item["entity_id"] or "")

    return {
        "source": str(storage_dir),
        "counts": {
            "areas": len(areas_by_id),
            "devices": len(devices_by_id),
            "entities": len(mapped_entities),
            "zones": len(zones),
        },
        "entities": mapped_entities,
        "zones": zones,
    }


def current_devices_by_id(inventory: dict) -> dict[str, dict]:
    devices_by_id: dict[str, dict] = {}
    for entity in inventory["entities"]:
        device = entity.get("device") or {}
        device_id = device.get("device_id")
        device_name = device.get("device_name")
        if not device_id or not device_name or device.get("disabled"):
            continue
        devices_by_id[device_id] = device
    return devices_by_id


def sorted_devices(devices_by_id: dict[str, dict]) -> list[dict]:
    return sorted(
        devices_by_id.values(),
        key=lambda item: (
            (item.get("area_name") or "Unassigned").casefold(),
            (item.get("device_name") or "").casefold(),
            item.get("device_id") or "",
        ),
    )


def validate_number_map(number_map: dict, source: Path) -> None:
    if (
        not isinstance(number_map, dict)
        or number_map.get("version") != 1
        or not isinstance(number_map.get("devices"), dict)
    ):
        raise SystemExit(f"Unexpected number map structure in {source}")

    used_numbers: dict[int, str] = {}
    for device_id, item in number_map["devices"].items():
        if not isinstance(item, dict) or not isinstance(item.get("number"), int):
            raise SystemExit(f"Invalid number map entry for {device_id} in {source}")
        number = item["number"]
        if number < 1:
            raise SystemExit(f"Invalid inventory number {number} for {device_id} in {source}")
        if number in used_numbers:
            raise SystemExit(
                f"Duplicate inventory number {number} for "
                f"{used_numbers[number]} and {device_id} in {source}"
            )
        used_numbers[number] = device_id


def load_number_map(path: Path) -> dict:
    if not path.exists():
        return {
            "version": 1,
            "devices": {},
        }

    try:
        number_map = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")

    validate_number_map(number_map, path)
    return number_map


def load_legacy_text_numbers(path: Path, devices_by_id: dict[str, dict]) -> dict:
    number_map = {
        "version": 1,
        "devices": {},
    }
    if not path.exists():
        return number_map

    devices_by_name_area: dict[tuple[str, str], list[dict]] = {}
    for device in devices_by_id.values():
        key = (device["device_name"], device.get("area_name") or "Unassigned")
        devices_by_name_area.setdefault(key, []).append(device)

    line_pattern = re.compile(r"^(?P<number>\d+)\.\s+(?P<name>.+)\s+\((?P<area>.*)\)$")
    for line in path.read_text().splitlines():
        match = line_pattern.match(line)
        if not match:
            continue

        number = int(match.group("number"))
        name = match.group("name")
        area_name = match.group("area")
        matches = devices_by_name_area.get((name, area_name), [])
        if len(matches) > 1:
            raise SystemExit(
                f"Cannot migrate number {number} from {path}: "
                f"multiple devices match {name!r} in {area_name!r}"
            )
        if matches:
            device = matches[0]
            device_id = device["device_id"]
        else:
            device_id = f"legacy:{number}:{name}"

        number_map["devices"][device_id] = {
            "number": number,
            "device_name": name,
            "area_name": area_name,
            "present": bool(matches),
        }

    validate_number_map(number_map, path)
    return number_map


def update_number_map(number_map: dict, devices_by_id: dict[str, dict]) -> dict:
    mapped_devices = number_map["devices"]
    used_numbers = {
        item["number"]
        for item in mapped_devices.values()
        if isinstance(item, dict) and isinstance(item.get("number"), int)
    }
    next_number = max(used_numbers, default=0) + 1

    for device in sorted_devices(devices_by_id):
        device_id = device["device_id"]
        if device_id not in mapped_devices:
            while next_number in used_numbers:
                next_number += 1
            mapped_devices[device_id] = {
                "number": next_number,
            }
            used_numbers.add(next_number)
            next_number += 1

        mapped_devices[device_id]["device_name"] = device.get("device_name")
        mapped_devices[device_id]["area_name"] = device.get("area_name") or "Unassigned"
        mapped_devices[device_id]["present"] = True

    for device_id, item in mapped_devices.items():
        if device_id not in devices_by_id:
            item["present"] = False

    return number_map


def build_text_inventory(devices_by_id: dict[str, dict], number_map: dict) -> str:
    lines = [
        "# Home Assistant Device Map Inventory",
        "",
        "Use these stable numbers to label device locations on an apartment map.",
        "Numbers are kept in inventory_numbers.json and are not reused automatically.",
        "",
    ]
    numbered_devices = sorted(
        devices_by_id.values(),
        key=lambda device: number_map["devices"][device["device_id"]]["number"],
    )
    for device in numbered_devices:
        number = number_map["devices"][device["device_id"]]["number"]
        area_name = device.get("area_name") or "Unassigned"
        lines.append(f"{number:03d}. {device['device_name']} ({area_name})")

    return "\n".join(lines) + "\n"


def build_virtual_inventory(inventory: dict) -> dict:
    virtual_entities = []
    for entity in inventory["entities"]:
        device_id = entity.get("device", {}).get("device_id")
        if not device_id:
            virtual_entities.append(entity)

    for zone in inventory.get("zones", []):
        zone_name = zone.get("name", "unknown")
        entity_id = zone.get("id")
        if not entity_id:
            entity_id = f"zone.{zone_name.lower().replace(' ', '_')}"
        elif not entity_id.startswith("zone."):
            entity_id = f"zone.{entity_id}"

        virtual_entities.append({
            "entity_id": entity_id,
            "original_name": zone_name,
            "name": zone_name,
            "platform": "zone",
            "device_class": None,
            "original_device_class": None,
            "original_icon": zone.get("icon"),
            "unit_of_measurement": None,
            "state_class": None,
            "entity_category": None,
            "hidden": False,
            "disabled": False,
            "has_entity_name": False,
            "aliases": [],
            "labels": [],
            "device": {},
            "area": {},
            "zone_data": {
                "latitude": zone.get("latitude"),
                "longitude": zone.get("longitude"),
                "radius": zone.get("radius"),
                "passive": zone.get("passive"),
            }
        })

    return {
        "counts": {
            "virtual_entities": len(virtual_entities),
        },
        "virtual_entities": virtual_entities,
    }


def export_yaml_entities(config_dir: Path, output_dir: Path) -> None:
    for yaml_file, key_id, key_name, output_file in [
        ("automations.yaml", "id", "alias", "automations_inventory.json"),
        ("scripts.yaml", "alias", "alias", "scripts_inventory.json"),
        ("scenes.yaml", "id", "name", "scenes_inventory.json"),
    ]:
        in_path = config_dir / yaml_file
        out_path = output_dir / output_file
        if not in_path.exists():
            continue
            
        try:
            with open(in_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as exc:
            print(f"Failed to load {yaml_file}: {exc}")
            continue
            
        if not data:
            continue
            
        results = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": str(item.get(key_id, "unknown")),
                    "name": item.get(key_name, ""),
                    "description": item.get("description", ""),
                    "mode": item.get("mode", "single")
                })
        elif isinstance(data, dict):
            for k, v in data.items():
                if not isinstance(v, dict):
                    continue
                results.append({
                    "id": str(k),
                    "name": v.get(key_name, ""),
                    "description": v.get("description", ""),
                    "mode": v.get("mode", "single")
                })
                
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n")
        print(f"Wrote {len(results)} items from {yaml_file} to {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a sanitized Home Assistant entity/device inventory from .storage."
    )
    parser.add_argument(
        "--config-dir",
        default=".",
        help="Home Assistant config directory containing YAML files (default: .)",
    )
    parser.add_argument(
        "--storage-dir",
        default=str(DEFAULT_STORAGE),
        help=f"Home Assistant .storage directory (default: {DEFAULT_STORAGE})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--text-output",
        default=None,
        help=(
            "Output path for a simple numbered device inventory "
            f"(default: {DEFAULT_TEXT_OUTPUT} next to the JSON output)"
        ),
    )
    parser.add_argument(
        "--number-map",
        default=None,
        help=(
            "Path for the persistent device number map "
            f"(default: {DEFAULT_NUMBER_MAP_OUTPUT} next to the JSON output)"
        ),
    )
    parser.add_argument(
        "--virtual-inventory",
        default=None,
        help=(
            "Output JSON path for virtual entities (no device) "
            f"(default: {DEFAULT_VIRTUAL_OUTPUT} next to the JSON output)"
        ),
    )
    args = parser.parse_args()

    storage_dir = Path(args.storage_dir)
    output_path = Path(args.output)
    if args.text_output:
        text_output_path = Path(args.text_output)
    else:
        text_output_path = output_path.with_name(DEFAULT_TEXT_OUTPUT.name)
    if args.number_map:
        number_map_path = Path(args.number_map)
    else:
        number_map_path = output_path.with_name(DEFAULT_NUMBER_MAP_OUTPUT.name)
    if args.virtual_inventory:
        virtual_output_path = Path(args.virtual_inventory)
    else:
        virtual_output_path = output_path.with_name(DEFAULT_VIRTUAL_OUTPUT.name)

    inventory = build_inventory(storage_dir)
    devices_by_id = current_devices_by_id(inventory)
    if number_map_path.exists():
        number_map = load_number_map(number_map_path)
    else:
        number_map = load_legacy_text_numbers(text_output_path, devices_by_id)
    number_map = update_number_map(number_map, devices_by_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=True) + "\n")
    number_map_path.parent.mkdir(parents=True, exist_ok=True)
    number_map_path.write_text(json.dumps(number_map, indent=2, ensure_ascii=True) + "\n")
    text_output_path.parent.mkdir(parents=True, exist_ok=True)
    text_output_path.write_text(build_text_inventory(devices_by_id, number_map))
    
    virtual_inventory = build_virtual_inventory(inventory)
    virtual_output_path.parent.mkdir(parents=True, exist_ok=True)
    virtual_output_path.write_text(json.dumps(virtual_inventory, indent=2, ensure_ascii=True) + "\n")

    print(f"Wrote inventory to {output_path}")
    print(f"Wrote inventory number map to {number_map_path}")
    print(f"Wrote map inventory to {text_output_path}")
    print(f"Wrote virtual inventory to {virtual_output_path}")
    print(
        "Counts: "
        f"{inventory['counts']['areas']} areas, "
        f"{inventory['counts']['devices']} devices, "
        f"{inventory['counts']['entities']} entities, "
        f"{virtual_inventory['counts']['virtual_entities']} virtual entities"
    )

    config_dir = Path(args.config_dir)
    export_yaml_entities(config_dir, output_path.parent)

    return 0


if __name__ == "__main__":
    sys.exit(main())
