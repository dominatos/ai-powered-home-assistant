#!/usr/bin/env python3
"""
ha_toolkit.py
=============
Unified Home Assistant Toolkit for static analysis, debugging, and validation.
Replaces ha_debug_cli.py, dashboard_audit.py, check_docs.py, and generate_automations_kb.py.
"""

import argparse
import json
import re
import sys
import yaml
from pathlib import Path
from typing import Any

# ==============================================================================
# YAML Helpers
# ==============================================================================
class HASafeLoader(yaml.SafeLoader):
    """SafeLoader subclass that handles Home Assistant tags."""
    pass

def _ha_constructor(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node) -> Any:
    return f"__{tag_suffix}__"

HASafeLoader.add_multi_constructor("!", _ha_constructor)


def load_automations(repo: Path) -> list:
    auto_file = repo / "automations.yaml"
    try:
        content = auto_file.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        raise FileNotFoundError(f"Error reading {auto_file}: {e}")

    try:
        automations = yaml.load(content, Loader=HASafeLoader)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing automations.yaml: {e}")

    if not isinstance(automations, list):
        raise ValueError("Error: automations.yaml is not a list.")
    return automations


# ==============================================================================
# 1. TRACE ANALYZER (from ha_debug_cli.py)
# ==============================================================================
def _extract_trace_meta(trace: dict) -> dict:
    """Extract start_time, state, script_execution, trigger from HA saved_traces format."""
    sd = trace.get('short_dict') if isinstance(trace.get('short_dict'), dict) else {}
    ed = trace.get('extended_dict') if isinstance(trace.get('extended_dict'), dict) else {}
    
    start_time = (
        trace.get('timestamp', {}).get('start')
        or sd.get('timestamp', {}).get('start')
        or ed.get('timestamp', {}).get('start')
        or 'Unknown'
    )
    finish_time = (
        trace.get('timestamp', {}).get('finish')
        or sd.get('timestamp', {}).get('finish')
        or ed.get('timestamp', {}).get('finish')
        or 'Unknown'
    )
    state = trace.get('state') or sd.get('state') or ed.get('state') or 'Unknown'
    error = trace.get('error') or sd.get('error') or ed.get('error') or ''
    script_execution = trace.get('script_execution') or sd.get('script_execution') or ed.get('script_execution') or ''
    trigger = trace.get('trigger') or sd.get('trigger') or ed.get('trigger') or ''
    
    return {
        'start': start_time,
        'finish': finish_time,
        'state': state,
        'error': error,
        'script_execution': script_execution,
        'trigger': trigger,
    }


def analyze_traces(args, repo: Path):
    try:
        with open(repo / 'temp/trace.saved_traces', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: temp/trace.saved_traces not found. Pull it first using tools/pull_debug_files.sh.")
        sys.exit(1)
    
    traces_dict = data.get('data', {})

    # Map automation IDs to aliases if available
    id_to_alias = {}
    try:
        automations = load_automations(repo)
        for a in automations:
            if isinstance(a, dict) and 'id' in a:
                id_to_alias[str(a['id'])] = a.get('alias', '')
    except Exception:
        pass
    
    if args.list:
        print("Available automation IDs in traces:")
        for k in sorted(traces_dict.keys()):
            raw_id = k.replace('automation.', '')
            alias = id_to_alias.get(raw_id, '')
            alias_str = f" [{alias}]" if alias else ""
            if args.query:
                q = args.query.lower()
                if q not in k.lower() and q not in alias.lower():
                    continue
            traces = traces_dict[k]
            print(f" - {k}{alias_str} ({len(traces)} traces)")
        return

    if not args.automation:
        print("Error: must specify --list or --automation <id>")
        sys.exit(1)

    target_key = None
    q = args.automation.lower()
    for k in traces_dict.keys():
        raw_id = k.replace('automation.', '')
        alias = id_to_alias.get(raw_id, '')
        if q in k.lower() or (alias and q in alias.lower()):
            target_key = k
            break
            
    if not target_key:
        print(f"Error: No traces found matching '{args.automation}'")
        sys.exit(1)
        
    traces = traces_dict[target_key]
    
    if args.valid_only:
        filtered_traces = []
        for t in traces:
            meta = _extract_trace_meta(t)
            if meta['state'] == 'failed_single' or meta['error'] == 'Already running':
                continue
            filtered_traces.append(t)
        traces = filtered_traces

    if not traces:
        print(f"No traces remaining for {target_key} after filtering.")
        return
        
    try:
        traces.sort(key=lambda x: _extract_trace_meta(x)['start'], reverse=True)
    except Exception:
        pass 
        
    limit = args.limit
    selected_traces = traces[:limit]
    
    raw_id = target_key.replace('automation.', '')
    alias = id_to_alias.get(raw_id, '')
    alias_str = f" [{alias}]" if alias else ""
    print(f"Found {len(traces_dict[target_key])} total traces for {target_key}{alias_str}.")
    if args.valid_only:
        print(f"({len(traces)} valid traces after filtering 'failed_single')")
    
    for i, trace in enumerate(selected_traces):
        meta = _extract_trace_meta(trace)
        print(f"\n--- Trace {i+1} ---")
        print(f"Time:      {meta['start']}")
        print(f"State:     {meta['state']}")
        if meta['trigger']:
            print(f"Trigger:   {meta['trigger']}")
        if meta['script_execution']:
            print(f"Execution: {meta['script_execution']}")
        
        if args.full:
            print("Full JSON payload:")
            print(json.dumps(trace, indent=2))
        else:
            print("Run with --full to see the full JSON dump.")
            
        if args.output:
            filename = f"{args.output}_{i+1}.json"
            with open(filename, 'w') as out:
                json.dump(trace, out, indent=2)
            print(f"Saved full trace to {filename}")


# ==============================================================================
# 2. INVENTORY ANALYZER (from ha_debug_cli.py)
# ==============================================================================
def analyze_inventory(args, repo: Path):
    try:
        with open(repo / 'ha_device_inventory.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: ha_device_inventory.json not found.")
        sys.exit(1)

    print(f"Searching inventory for '{args.query}'...")
    found = set()
    query = args.query.lower()
    
    entities = data.get('entities', [])
    for e in entities:
        device = e.get('device') or {}
        
        e_id = e.get('entity_id') or ''
        e_name = e.get('name') or ''
        d_id = device.get('device_id') or ''
        d_name = device.get('device_name') or ''
        d_model = device.get('model') or ''
        d_mfg = device.get('manufacturer') or ''
        
        matches = any(query in str(x).lower() for x in [e_id, e_name, d_id, d_name, d_model, d_mfg])
        
        if matches:
            if d_id:
                if d_id not in found:
                    found.add(d_id)
                    print(f"\n--- Device ID: {d_id} ---")
                    print(f"Name:         {d_name}")
                    print(f"Model:        {d_model}")
                    print(f"Manufacturer: {d_mfg}")
                    
                    device_entities = [ent for ent in entities if ent.get('device') and ent['device'].get('device_id') == d_id]
                    if args.show_all_entities:
                        print("Entities:")
                        for ent in device_entities:
                            print(f"  - {ent.get('entity_id')}")
                    else:
                        print(f"Entities: ({len(device_entities)} total, run with --show-all-entities to list them)")
            else:
                if e_id not in found:
                    found.add(e_id)
                    print(f"\n--- Entity (No Device): {e_id} ---")
                    print(f"Name: {e_name}")

    print(f"\nFound {len(found)} matching items.")


# ==============================================================================
# 3. DASHBOARD AUDIT (from dashboard_audit.py)
# ==============================================================================
def load_inventory(repo: Path) -> dict:
    inv_file = repo / "ha_device_inventory.json"
    try:
        content = inv_file.read_text(encoding='utf-8')
        data = json.loads(content)
    except Exception as e:
        print(f"Error reading {inv_file}: {e}")
        sys.exit(1)
    if not isinstance(data, dict) or "entities" not in data:
        print("Error: ha_device_inventory.json must contain an 'entities' key.")
        sys.exit(1)
    return data


def audit_dashboard(args, repo: Path):
    print("=" * 70)
    print("DASHBOARD AUDIT")
    print("=" * 70)

    inv_file = repo / "ha_device_inventory.json"
    dash_file = repo / "dashboard.yaml"

    if not inv_file.exists():
        print("  SKIPPED — ha_device_inventory.json not found.")
        return

    data = load_inventory(repo)
    entities = data.get("entities", [])
    inv_ids = {e.get("entity_id") for e in entities if "entity_id" in e}

    if not dash_file.exists():
        print("  dashboard.yaml not found — reporting inventory summary only.")
        input_booleans = [e for e in entities if e.get("entity_id", "").startswith("input_boolean.") and not e.get("disabled_by")]
        if input_booleans:
            print(f"\n  ALL INPUT_BOOLEAN HELPERS ({len(input_booleans)}):")
            for ib in sorted(input_booleans, key=lambda x: x.get("entity_id", "")):
                print(f"    - {ib['entity_id']} ({ib.get('original_name', '\u2014')})")

        print("\n" + "=" * 70)
        print("TEMPERATURE & HUMIDITY SENSORS")
        print("=" * 70)
        for ent in entities:
            eid = ent.get("entity_id", "")
            if ("temperature" in eid or "humidity" in eid) and "sensor." in eid and not ent.get("disabled_by"):
                area = ent.get("area") or {}
                aname = area.get("area_name", "\u2014") if isinstance(area, dict) else "\u2014"
                print(f"  {eid:65s} | {aname}")
        print()
        return

    dash = dash_file.read_text(encoding='utf-8')
    ent_refs = set(re.findall(r"entity:\s+[\"']?([\w.]+)[\"']?", dash))
    print(f"  Entities referenced in dashboard.yaml: {len(ent_refs)}")

    missing = []
    for ref in sorted(ent_refs):
        if ref not in inv_ids:
            print(f"    NOT IN INVENTORY: {ref}")
            missing.append(ref)

    if not missing:
        print("  All dashboard entity references found in inventory ✓")
    else:
        print(f"\n  {len(missing)} reference(s) not in inventory (may be template sensors in configuration.yaml)")
    print()
    
    if args.details:
        print("=" * 70)
        print("TEMPERATURE & HUMIDITY SENSORS")
        print("=" * 70)
        for ent in entities:
            eid = ent.get("entity_id", "")
            if ("temperature" in eid or "humidity" in eid) and "sensor." in eid and not ent.get("disabled_by"):
                area = ent.get("area") or {}
                aname = area.get("area_name", "—") if isinstance(area, dict) else "—"
                print(f"  {eid:65s} | {aname}")
        print()
        
        print("=" * 70)
        print("LIGHT ENTITIES")
        print("=" * 70)
        for ent in entities:
            eid = ent.get("entity_id", "")
            if eid.startswith("light.") and not ent.get("disabled_by"):
                area = ent.get("area") or {}
                aname = area.get("area_name", "—") if isinstance(area, dict) else "—"
                print(f"  {eid:55s} | {aname}")
        print()


# ==============================================================================
# 4. DOCS AUDIT (from check_docs.py)
# ==============================================================================
IGNORE_ALIASES: set[str] = set()

def audit_docs(args, repo: Path):
    try:
        automations = load_automations(repo)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        sys.exit(1)
    aliases = {
        a.get("alias", "").strip()
        for a in automations
        if isinstance(a, dict) and a.get("alias")
    }

    try:
        doc = (repo / "HOUSE_CONTEXT.md").read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading HOUSE_CONTEXT.md: {e}")
        sys.exit(1)

    missing = [alias for alias in aliases if alias not in doc]

    potential_aliases = set(re.findall(r"`([A-Z][a-zA-Z0-9\s]+:\s[^`\n]+)`", doc))
    stale = [
        p.strip() for p in potential_aliases
        if p.strip() not in IGNORE_ALIASES
        and " " in p.strip()
        and not p.strip().startswith("sensor.")
        and not p.strip().startswith("binary_sensor.")
        and p.strip() not in aliases
    ]

    has_errors = False
    if missing:
        has_errors = True
        print("\n❌ MISSING in HOUSE_CONTEXT.md (automations with no documentation):")
        for m in sorted(missing):
            print(f"  - {m}")

    if stale:
        has_errors = True
        print("\n⚠️  STALE in HOUSE_CONTEXT.md (aliases not found in automations.yaml):")
        for s in sorted(stale):
            print(f"  - {s}")

    if not has_errors:
        print("✅ All automations are documented and no stale aliases found.")
        sys.exit(0)
    else:
        sys.exit(1)


# ==============================================================================
# 5. GENERATE KB (from generate_automations_kb.py)
# ==============================================================================
def generate_kb(args, repo: Path):
    try:
        automations = load_automations(repo)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        sys.exit(1)
    
    kb = "# Home Assistant Automations Knowledge Base\n\n"
    kb += "This document provides a human-readable summary of all automations currently configured in `automations.yaml`.\n"
    kb += "It is the quick-reference index for finding what automations exist, what IDs they have, what triggers/conditions/actions they use, and a brief description of each.\n"
    kb += "**Keep this file up to date whenever automations are added, changed, or removed.**\n\n"
    
    # Check if there is a header or table we should preserve
    try:
        existing_kb = (repo / "automations_kb.md").read_text(encoding='utf-8')
        if "### Phone → Person Quick Reference" in existing_kb:
            import re
            table_match = re.search(r"(### Phone → Person Quick Reference.*?)\n---", existing_kb, re.DOTALL)
            if table_match:
                kb += table_match.group(1) + "\n---\n\n"
    except Exception:
        pass
    
    for auto in automations:
        if not isinstance(auto, dict):
            continue
            
        alias = auto.get('alias', 'Unnamed Automation')
        desc = auto.get('description', 'No description provided.')
        auto_id = auto.get('id', 'No ID')
        
        kb += f"## {alias}\n"
        kb += f"- **ID**: `{auto_id}`\n"
        kb += f"- **Description**: {desc}\n\n"
        
        triggers = auto.get('trigger', auto.get('triggers', []))
        if triggers:
            kb += "### Triggers\n"
            if isinstance(triggers, list):
                for t in triggers:
                    if isinstance(t, dict):
                        platform = t.get('platform', t.get('trigger', 'unknown'))
                        kb += f"- **{platform}**: `{json.dumps({k:v for k,v in t.items() if k not in ('platform', 'trigger')})}`\n"
                    else:
                        kb += f"- `{t}`\n"
            else:
                kb += f"- `{json.dumps(triggers)}`\n"
        
        conditions = auto.get('condition', auto.get('conditions', []))
        if conditions:
            kb += "\n### Conditions\n"
            if isinstance(conditions, list):
                for c in conditions:
                    if isinstance(c, dict):
                        c_type = c.get('condition', 'unknown')
                        kb += f"- **{c_type}**: `{json.dumps({k:v for k,v in c.items() if k != 'condition'})}`\n"
                    else:
                        kb += f"- `{c}`\n"
            else:
                kb += f"- `{json.dumps(conditions)}`\n"
                
        actions = auto.get('action', auto.get('actions', []))
        if actions:
            kb += "\n### Actions\n"
            if isinstance(actions, list):
                for a in actions:
                    if isinstance(a, dict):
                        action_type = "service/action" if ('service' in a or 'action' in a) else next(iter(a.keys()), "unknown")
                        target = a.get('service', a.get('action', 'unknown'))
                        kb += f"- **{action_type}**: `{target}` "
                        if 'entity_id' in a or ('target' in a and isinstance(a.get('target'), dict) and 'entity_id' in a['target']):
                            ent = a.get('entity_id', a.get('target', {}).get('entity_id', ''))
                            kb += f"on `{ent}` "
                        kb += "\n"
                    else:
                        kb += f"- `{a}`\n"
            else:
                kb += f"- `{json.dumps(actions)}`\n"
                
        kb += "\n---\n\n"
    
    out_file = Path(args.output) if args.output else repo / "automations_kb.md"
    try:
        out_file.write_text(kb, encoding='utf-8')
        print(f"✅ Generated {out_file}")
    except Exception as e:
        print(f"Error writing to {out_file}: {e}")
        sys.exit(1)


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Home Assistant Toolkit")
    parser.add_argument("--repo", default=".", help="Path to HA repository (default: .)")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands", required=True)

    # Trace Parser
    trace_parser = subparsers.add_parser("trace", help="Analyze HA automation traces")
    trace_parser.add_argument("--list", action="store_true", help="List all available automations in traces")
    trace_parser.add_argument("--query", "-q", help="Filter the list output by this substring")
    trace_parser.add_argument("--automation", "-a", help="Automation ID to extract traces for")
    trace_parser.add_argument("--limit", "-n", type=int, default=1, help="Max traces to extract (default 1)")
    trace_parser.add_argument("--valid-only", action="store_true", default=True, help="Filter out failed_single runs")
    trace_parser.add_argument("--all-runs", action="store_false", dest="valid_only", help="Include failed_single runs")
    trace_parser.add_argument("--full", action="store_true", help="Print full JSON output")
    trace_parser.add_argument("--output", "-o", help="Base filename to write JSON traces to")

    # Inventory Parser
    inv_parser = subparsers.add_parser("inventory", help="Analyze HA device inventory")
    inv_parser.add_argument("query", help="Substring to search for in device names, models, or entity IDs")
    inv_parser.add_argument("--show-all-entities", action="store_true", help="Show all entities for matched devices")

    # Dashboard Audit
    dash_parser = subparsers.add_parser("audit-dashboard", help="Audit dashboard.yaml against inventory")
    dash_parser.add_argument("--details", action="store_true", help="Print detailed entity lists (sensors/lights)")

    # Docs Audit
    docs_parser = subparsers.add_parser("audit-docs", help="Audit HOUSE_CONTEXT.md against automations.yaml")

    # Generate KB
    kb_parser = subparsers.add_parser("generate-kb", help="Regenerate automations_kb.md")
    kb_parser.add_argument("--output", help="Output file (default: automations_kb.md)")

    args = parser.parse_args()
    repo = Path(args.repo)

    if args.command == "trace":
        analyze_traces(args, repo)
    elif args.command == "inventory":
        analyze_inventory(args, repo)
    elif args.command == "audit-dashboard":
        audit_dashboard(args, repo)
    elif args.command == "audit-docs":
        audit_docs(args, repo)
    elif args.command == "generate-kb":
        generate_kb(args, repo)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
