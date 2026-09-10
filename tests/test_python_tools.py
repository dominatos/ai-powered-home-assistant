#!/usr/bin/env python3
"""
test_python_tools.py
====================
Unit tests for all Python scripts in tools/.

Run from the repository root:
    python3 -m pytest tests/test_python_tools.py -v
    # or
    python3 tests/test_python_tools.py

Tests use temporary directories with mock data — no real HA installation needed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def write_file(path: Path, content: str) -> None:
    """Write text content to a file, creating its parent directories when needed.
    
    Parameters:
    	path (Path): Destination file path.
    	content (str): Text to write to the file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def run_tool(*args, cwd: Path = None) -> subprocess.CompletedProcess:
    """
    Run a tool command and capture its completed process result.
    
    Parameters:
        *args: Command and arguments to execute.
        cwd (Path, optional): Working directory for the command.
    
    Returns:
        subprocess.CompletedProcess: The completed process, including captured output.
    """
    return subprocess.run(
        args,
        capture_output=True, text=True,
        cwd=str(cwd) if cwd else None,
        timeout=10,
        # The tools print emoji. Without an explicit encoding this decodes
        # with the legacy Windows codepage and raises UnicodeDecodeError in
        # subprocess' reader thread, leaving stdout empty.
        encoding="utf-8", errors="replace",
    )


def make_automations_yaml(*aliases: str) -> str:
    """
    Generate YAML entries for test automations using the provided aliases.
    
    Parameters:
    	aliases (str): Aliases to assign to the generated automations.
    
    Returns:
    	str: A YAML-formatted automation list.
    """
    items = []
    for i, alias in enumerate(aliases, 1):
        items.append(textwrap.dedent(f"""\
            - alias: "{alias}"
              id: "auto_{i}"
              description: "Test automation {i}"
              trigger:
                - platform: state
                  entity_id: sensor.test
              action:
                - service: light.turn_on
                  target:
                    entity_id: light.test
        """))
    return "\n".join(items)


# ===========================================================================
# 1. backup_automations.py
# ===========================================================================
class TestBackupAutomations(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_backup_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_backup_creates_file(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On"))
        r = run_tool(sys.executable, str(TOOLS / "backup_automations.py"), "auto_1", cwd=self.test_dir)
        self.assertIn("Backed up", r.stdout)
        self.assertEqual(r.returncode, 0)

    def test_backup_missing_id(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On"))
        r = run_tool(sys.executable, str(TOOLS / "backup_automations.py"), "nonexistent", cwd=self.test_dir)
        self.assertIn("Not found", r.stdout)
        self.assertNotEqual(r.returncode, 0)

    def test_backup_no_file(self):
        r = run_tool(sys.executable, str(TOOLS / "backup_automations.py"), "auto_1", cwd=self.test_dir)
        self.assertIn("Error", r.stdout)

    def test_backup_multiple_ids(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On", "Bedroom: Fan Off"))
        r = run_tool(sys.executable, str(TOOLS / "backup_automations.py"), "auto_1", "auto_2", cwd=self.test_dir)
        self.assertIn("Backed up", r.stdout)
        backups = list((self.test_dir / "backups").glob("*.yaml"))
        self.assertEqual(len(backups), 2)

    def test_backup_exit_code_no_args(self):
        r = run_tool(sys.executable, str(TOOLS / "backup_automations.py"), cwd=self.test_dir)
        self.assertNotEqual(r.returncode, 0)


# ===========================================================================
# 2. check_docs.py
# ===========================================================================
class TestCheckDocs(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_checkdocs_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_all_documented(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On"))
        write_file(self.test_dir / "HOUSE_CONTEXT.md", "# Kitchen\n\n- `Kitchen: Light On` triggers when door opens\n")
        r = run_tool(sys.executable, str(TOOLS / "check_docs.py"), cwd=self.test_dir)
        self.assertIn("All automations are documented", r.stdout)
        self.assertEqual(r.returncode, 0)

    def test_missing_documentation(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On", "Bedroom: Fan Off"))
        write_file(self.test_dir / "HOUSE_CONTEXT.md", "# Kitchen\n\n- `Kitchen: Light On` triggers when door opens\n")
        r = run_tool(sys.executable, str(TOOLS / "check_docs.py"), cwd=self.test_dir)
        self.assertIn("MISSING", r.stdout)
        self.assertNotEqual(r.returncode, 0)

    def test_stale_aliases(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On"))
        write_file(self.test_dir / "HOUSE_CONTEXT.md", "# Kitchen\n\n- `Kitchen: Light On` is fine\n- `Old Removed: Automation` is gone\n")
        r = run_tool(sys.executable, str(TOOLS / "check_docs.py"), cwd=self.test_dir)
        self.assertIn("STALE", r.stdout)
        self.assertNotEqual(r.returncode, 0)

    def test_no_automations_file(self):
        r = run_tool(sys.executable, str(TOOLS / "check_docs.py"), cwd=self.test_dir)
        self.assertIn("Error", r.stdout)
        self.assertNotEqual(r.returncode, 0)

    def test_nested_include(self):
        write_file(self.test_dir / "my_automation.yaml", make_automations_yaml("Kitchen: Included Light"))
        write_file(self.test_dir / "automations.yaml", "- !include my_automation.yaml\n")
        write_file(self.test_dir / "HOUSE_CONTEXT.md", "# House\n\nNo automations configured yet.\n")
        r = run_tool(sys.executable, str(TOOLS / "check_docs.py"), cwd=self.test_dir)
        self.assertNotIn("Kitchen: Included Light", r.stdout)
        self.assertEqual(r.returncode, 0)


# ===========================================================================
# 3. dashboard_audit.py
# ===========================================================================
class TestDashboardAudit(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_dashaudit_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_runs_with_inventory(self):
        inventory = {
            "entities": [
                {"entity_id": "sensor.kitchen_temperature", "original_name": "Kitchen Temp",
                 "device_class": "temperature", "disabled_by": None, "area": {"area_name": "Kitchen"}},
                {"entity_id": "light.kitchen_main", "original_name": "Kitchen Light",
                 "device_class": None, "disabled_by": None, "area": {"area_name": "Kitchen"}},
            ]
        }
        write_file(self.test_dir / "ha_device_inventory.json", json.dumps(inventory, indent=2))
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertIn("TEMPERATURE & HUMIDITY", r.stdout)
        self.assertIn("sensor.kitchen_temperature", r.stdout)

    def test_dashboard_entity_refs_all_found(self):
        inventory = {"entities": [{"entity_id": "light.kitchen", "disabled_by": None}]}
        dashboard = textwrap.dedent("""\
            views:
              - title: Kitchen
                cards:
                  - type: entity
                    entity: light.kitchen
        """)
        write_file(self.test_dir / "ha_device_inventory.json", json.dumps(inventory))
        write_file(self.test_dir / "dashboard.yaml", dashboard)
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertIn("All dashboard entity references found", r.stdout)

    def test_dashboard_entity_refs_missing(self):
        inventory = {"entities": [{"entity_id": "light.kitchen", "disabled_by": None}]}
        dashboard = "views:\n  - cards:\n      - entity: light.missing\n"
        write_file(self.test_dir / "ha_device_inventory.json", json.dumps(inventory))
        write_file(self.test_dir / "dashboard.yaml", dashboard)
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertIn("NOT IN INVENTORY", r.stdout)

    def test_input_booleans(self):
        inventory = {
            "entities": [
                {"entity_id": "input_boolean.vacation_mode", "original_name": "Vacation Mode",
                 "disabled_by": None, "area": {}},
            ]
        }
        write_file(self.test_dir / "ha_device_inventory.json", json.dumps(inventory))
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertIn("input_boolean.vacation_mode", r.stdout)

    def test_malformed_inventory_json(self):
        write_file(self.test_dir / "ha_device_inventory.json", "not valid json {{{")
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertNotEqual(r.returncode, 0)

    def test_inventory_without_entities(self):
        write_file(self.test_dir / "ha_device_inventory.json", json.dumps({"other_key": []}))
        r = run_tool(sys.executable, str(TOOLS / "dashboard_audit.py"), cwd=self.test_dir)
        self.assertNotEqual(r.returncode, 0)


# ===========================================================================
# 4. export_ha_inventory.py
# ===========================================================================
class TestExportHaInventory(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_exportinv_"))
        self.storage = self.test_dir / ".storage"
        self.storage.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_storage_files(self):
        """
        Create mock Home Assistant storage registry files for entity, device, area, and zone data.
        """
        entities = [
            {"entity_id": "sensor.temp", "original_name": "Temperature", "name": None,
             "platform": "mqtt", "device_class": "temperature", "original_device_class": "temperature",
             "original_icon": None, "unit_of_measurement": "°C", "state_class": "measurement",
             "entity_category": None, "hidden_by": None, "disabled_by": None,
             "has_entity_name": False, "aliases": [], "labels": [],
             "device_id": "dev_1", "area_id": "area_1"},
        ]
        devices = [
            {"id": "dev_1", "name_by_user": "Temp Sensor", "name": "Temp Sensor",
             "manufacturer": "Aqara", "model": "WSDCGQ11LM", "hw_version": "1.0",
             "sw_version": "1.0", "area_id": "area_1", "labels": [],
             "config_entries": [], "via_device_id": None, "disabled_by": None},
        ]
        areas = [{"id": "area_1", "name": "Living Room", "floor_id": None, "labels": []}]
        zones = [{"id": "zone.home", "name": "Home", "latitude": 50.0, "longitude": 30.0,
                  "radius": 100, "passive": False, "icon": "mdi:home"}]

        write_file(self.storage / "core.entity_registry", json.dumps({"data": {"entities": entities}}))
        write_file(self.storage / "core.device_registry", json.dumps({"data": {"devices": devices}}))
        write_file(self.storage / "core.area_registry", json.dumps({"data": {"areas": areas}}))
        # load_storage_json looks for "items" key if "zones" key not present
        write_file(self.storage / "core.zone_registry", json.dumps({"data": {"items": zones}}))

    def _export(self, **extra_args):
        """
        Run the inventory export tool with test storage and output paths.
        
        Parameters:
            **extra_args: Additional command-line options passed to the export tool.
        
        Returns:
            subprocess.CompletedProcess: The completed process with captured standard output and error.
        """
        cmd = [
            sys.executable, str(TOOLS / "export_ha_inventory.py"),
            "--storage-dir", str(self.storage),
            "--output", str(self.test_dir / "inventory.json"),
            "--text-output", str(self.test_dir / "inventory.txt"),
            "--number-map", str(self.test_dir / "numbers.json"),
            "--virtual-inventory", str(self.test_dir / "virtual.json"),
        ]
        for k, v in extra_args.items():
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.test_dir), timeout=10)

    def test_export_creates_files(self):
        self._write_storage_files()
        r = self._export()
        self.assertIn("Wrote inventory", r.stdout)
        self.assertTrue((self.test_dir / "inventory.json").exists())
        self.assertTrue((self.test_dir / "inventory.txt").exists())
        self.assertTrue((self.test_dir / "numbers.json").exists())
        self.assertTrue((self.test_dir / "virtual.json").exists())

    def test_inventory_counts(self):
        self._write_storage_files()
        self._export()
        inv = json.loads((self.test_dir / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(inv["counts"]["entities"], 1)
        self.assertEqual(inv["counts"]["areas"], 1)
        self.assertEqual(inv["counts"]["devices"], 1)

    def test_text_inventory(self):
        self._write_storage_files()
        self._export()
        txt = (self.test_dir / "inventory.txt").read_text(encoding="utf-8")
        self.assertIn("Temp Sensor", txt)

    def test_number_map_persists(self):
        self._write_storage_files()
        self._export()
        nums = json.loads((self.test_dir / "numbers.json").read_text(encoding="utf-8"))
        self.assertEqual(nums["version"], 1)
        self.assertIn("dev_1", nums["devices"])

    def test_virtual_inventory_zones(self):
        self._write_storage_files()
        self._export()
        virt = json.loads((self.test_dir / "virtual.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(virt["counts"]["virtual_entities"], 1)

    def test_missing_storage_exits(self):
        r = self.run_tool_direct(
            sys.executable, str(TOOLS / "export_ha_inventory.py"),
            "--storage-dir", str(self.test_dir / "nonexistent"),
            "--output", str(self.test_dir / "inv.json"),
        )
        self.assertIn("Missing", r.stderr + r.stdout)

    def run_tool_direct(self, *args, **kwargs):
        """
        Run a tool command directly and capture its output.
        
        Parameters:
        	args: Command and arguments to execute.
        	kwargs: Additional options passed to `subprocess.run`.
        
        Returns:
        	subprocess.CompletedProcess: The completed subprocess result.
        """
        return subprocess.run(list(args), capture_output=True, text=True, timeout=10, **kwargs)


# ===========================================================================
# 5. generate_automations_kb.py
# ===========================================================================
class TestGenerateAutomationsKB(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_genkb_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generates_kb(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Light On", "Bedroom: Fan Off"))
        r = run_tool(sys.executable, str(TOOLS / "generate_automations_kb.py"), cwd=self.test_dir)
        self.assertEqual(r.returncode, 0)
        kb = (self.test_dir / "automations_kb.md").read_text(encoding="utf-8")
        self.assertIn("Kitchen: Light On", kb)
        self.assertIn("Bedroom: Fan Off", kb)

    def test_empty_automations(self):
        write_file(self.test_dir / "automations.yaml", "[]")
        r = run_tool(sys.executable, str(TOOLS / "generate_automations_kb.py"), cwd=self.test_dir)
        self.assertEqual(r.returncode, 0)
        kb = (self.test_dir / "automations_kb.md").read_text(encoding="utf-8")
        self.assertIn("Home Assistant Automations Knowledge Base", kb)

    def test_triggers_and_actions(self):
        write_file(self.test_dir / "automations.yaml", make_automations_yaml("Kitchen: Test"))
        r = run_tool(sys.executable, str(TOOLS / "generate_automations_kb.py"), cwd=self.test_dir)
        kb = (self.test_dir / "automations_kb.md").read_text(encoding="utf-8")
        self.assertIn("### Triggers", kb)
        self.assertIn("### Actions", kb)

    def test_missing_automations_yaml(self):
        r = run_tool(sys.executable, str(TOOLS / "generate_automations_kb.py"), cwd=self.test_dir)
        self.assertNotEqual(r.returncode, 0)

    def test_malformed_yaml(self):
        write_file(self.test_dir / "automations.yaml", "invalid: [yaml: {broken")
        r = run_tool(sys.executable, str(TOOLS / "generate_automations_kb.py"), cwd=self.test_dir)
        self.assertNotEqual(r.returncode, 0)


# ===========================================================================
# 6. generate_yaml_template.py
# ===========================================================================
class TestGenerateYamlTemplate(unittest.TestCase):

    def test_generates_basic(self):
        r = run_tool(sys.executable, str(TOOLS / "generate_yaml_template.py"), "basic")
        self.assertIn("Kitchen: Main Light on Door Open", r.stdout)

    def test_generates_advanced(self):
        r = run_tool(sys.executable, str(TOOLS / "generate_yaml_template.py"), "advanced")
        self.assertEqual(r.returncode, 0)

    def test_unknown_target(self):
        r = run_tool(sys.executable, str(TOOLS / "generate_yaml_template.py"), "nonexistent")
        self.assertIn("Unknown target", r.stdout)

    def test_no_args(self):
        r = run_tool(sys.executable, str(TOOLS / "generate_yaml_template.py"))
        self.assertIn("Usage", r.stdout)


# ===========================================================================
# 7. write_yaml_template.py
# ===========================================================================
class TestWriteYamlTemplate(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ha_writeyaml_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_copies_file(self):
        src = self.test_dir / "source.yaml"
        dst = self.test_dir / "output.yaml"
        write_file(src, "test: value\n")
        r = run_tool(sys.executable, str(TOOLS / "write_yaml_template.py"), str(dst), str(src))
        self.assertIn("Written", r.stdout)
        self.assertEqual(dst.read_text(encoding="utf-8"), "test: value\n")

    def test_missing_source(self):
        dst = self.test_dir / "output.yaml"
        r = run_tool(sys.executable, str(TOOLS / "write_yaml_template.py"), str(dst), str(self.test_dir / "nope.yaml"))
        self.assertIn("Error", r.stdout)

    def test_no_args(self):
        r = run_tool(sys.executable, str(TOOLS / "write_yaml_template.py"))
        self.assertIn("Usage", r.stdout)

    def test_preserves_content(self):
        src = self.test_dir / "source.yaml"
        dst = self.test_dir / "output.yaml"
        content = "key:\n  - item1\n  - item2\n"
        write_file(src, content)
        run_tool(sys.executable, str(TOOLS / "write_yaml_template.py"), str(dst), str(src))
        self.assertEqual(dst.read_text(encoding="utf-8"), content)

    def test_overwrites_existing(self):
        src = self.test_dir / "source.yaml"
        dst = self.test_dir / "output.yaml"
        write_file(dst, "old content\n")
        write_file(src, "new content\n")
        r = run_tool(sys.executable, str(TOOLS / "write_yaml_template.py"), str(dst), str(src))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(dst.read_text(encoding="utf-8"), "new content\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
