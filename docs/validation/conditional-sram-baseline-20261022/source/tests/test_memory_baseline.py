"""Prepared, unrun parser/contract tests. Synthetic rows are not CACTI results."""
import copy
import csv
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapter"))
import memory_baseline as model


def contract():
    # These tests are admitted only after the whole prepared candidate is copied.
    return model.strict_json((ROOT / "contract.json").read_bytes())


def synthetic_csv(banks, overrides=None):
    """Format-only fixture: numbers deliberately invented for parser checks."""
    fields = {key: "N/A" for key in model.CSV_HEADERS}
    fields.update({"Tech node (nm)": 45, "Capacity (bytes)": 131072,
                   "Number of banks": banks, "Associativity": 1,
                   "Output width (bits)": 256, "Access time (ns)": 2 * banks,
                   "Random cycle time (ns)": 3 * banks,
                   "Dynamic read energy (nJ)": 0.25, "Dynamic write energy (nJ)": 0.5,
                   "Standby leakage per bank(mW)": 0.01, "Area (mm2)": 1.5,
                   "Data arrary area efficiency %": 50, **model.PARTITION})
    fields.update(overrides or {})
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(list(model.CSV_HEADERS) + [""])
    writer.writerow([fields[key] for key in model.CSV_HEADERS] + [""])
    return stream.getvalue().encode()


def synthetic_stdout(banks):
    """Format-only fixture; never retained or published as model evidence."""
    inputs = model.expected_echo(banks)
    result = {
        "Total cache size (bytes)": 131072, "Number of banks": banks,
        "Associativity": "direct mapped", "Block size (bytes)": 32,
        "Read/write Ports": 1, "Read ports": 0, "Write ports": 0,
        "Technology size (nm)": 45, "Access time (ns)": 2 * banks,
        "Cycle time (ns)": 3 * banks,
        "Total dynamic read energy per access (nJ)": 0.25,
        "Total dynamic write energy per access (nJ)": 0.5,
        "Total leakage power of a bank (mW)": 0.006,
        "Total gate leakage power of a bank (mW)": 0.004,
        "Cache height x width (mm)": "1 x 1.5", "Best Ndwl": 2, "Best Ndbl": 2,
        "Best Nspd": 1, "Best Ndcm": 1, "Best Ndsam L1": 2, "Best Ndsam L2": 1,
        "Data array, H-tree wire type": "Delay optimized global wires",
    }
    return ("\n".join(str(k) + " : " + str(v) for k, v in inputs.items()) +
            "\n" + model.BANNER + "\n" +
            "\n".join(str(k) + " : " + str(v) for k, v in result.items()) + "\n").encode()


def synthetic_case(root, spec):
    path = root / spec["name"]
    path.mkdir()
    data = {"input.cfg": (ROOT / "inputs/configs" / (spec["name"] + ".cfg")).read_bytes(),
            "stdout.txt": synthetic_stdout(spec["banks"]), "stderr.txt": b"",
            "out.csv": synthetic_csv(spec["banks"]),
            "status.json": json.dumps({"returncode": 0, "timed_out": False,
                                       "model_binary_sha256": "a" * 64}).encode()}
    for name, value in data.items():
        (path / name).write_bytes(value)
    return path


class MemoryBaselineTests(unittest.TestCase):
    def test_contract_pinned_organization_and_model(self):
        value = contract()
        self.assertIs(model.validate_contract(value), value)
        self.assertEqual(value["organization"]["rows"] * 32, 131072)
        self.assertEqual(value["organization"]["stored_content_bits"] +
                         value["organization"]["padding_bits"], 256)
        self.assertEqual([case["banks"] for case in value["cases"]], [1, 4])

    def test_contract_rejects_extra_credit_ports_and_unknown_gates(self):
        original = contract()
        mutations = [("organization", "global_credits", 4),
                     ("organization", "exclusive_read_ports", 1),
                     ("organization", "row_bits", 128),
                     ("model", "physical_characterization", True),
                     ("model", "voltage_v", True),
                     ("scientific_limits", "achieved_hashes_per_second", 1_000_000)]
        for section, key, replacement in mutations:
            changed = copy.deepcopy(original)
            changed[section][key] = replacement
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                model.validate_contract(changed)
        changed = copy.deepcopy(original)
        changed["cases"][0]["expected_input_echo"] = {}
        with self.assertRaises(ValueError):
            model.validate_contract(changed)

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.strict_json(value)
        with self.assertRaises(ValueError):
            model.integer(True)

    def test_read_source_rejects_traversal_symlinks_and_size(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "item").write_bytes(b"1234")
            (root / "alias").symlink_to(root / "item")
            for path, bound in [("../item", 10), ("alias", 10), ("item", 3)]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    model.read_file(root, path, bound)

    def test_source_binding_and_accepted_reports(self):
        value = model.validate_contract(contract())
        facts = model.verify_source_files(value, ROOT / "inputs")
        demand_path = value["accepted_inputs"]["hardware_dataset_report"]
        self.assertEqual(facts[demand_path]["sha256"], model.HARDWARE_DEMAND_SHA256)
        self.assertEqual(len(facts), len(value["source_files"]))
        changed = copy.deepcopy(value)
        changed["source_files"][demand_path]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            model.verify_source_files(changed, ROOT / "inputs")

    def test_csv_exact_header_single_row_and_pure_ram(self):
        values = model.parse_csv(synthetic_csv(1), 1)
        self.assertEqual(values["Access time (ns)"], 2)
        self.assertEqual(values["Area (mm2)"], 1.5)
        variants = [synthetic_csv(1) + synthetic_csv(1).splitlines(keepends=True)[1],
                    synthetic_csv(1).replace(b"Data arrary", b"Data array"),
                    synthetic_csv(1, {"Ntwl": 2}),
                    synthetic_csv(1, {"Dynamic search energy (nJ)": 0})]
        for data in variants:
            with self.subTest(data=data[:80]), self.assertRaises(ValueError):
                model.parse_csv(data, 1)

    def test_csv_rejects_nonfinite_sign_and_partition_changes(self):
        for field, value in [("Access time (ns)", "nan"),
                             ("Random cycle time (ns)", 0),
                             ("Dynamic read energy (nJ)", -1),
                             ("Standby leakage per bank(mW)", -0.1),
                             ("Data arrary area efficiency %", 101),
                             ("Ndwl", 4), ("Capacity (bytes)", 65536),
                             ("Output width (bits)", 128)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                model.parse_csv(synthetic_csv(1, {field: value}), 1)

    def test_stdout_crosschecks_config_results_and_leakage(self):
        spec = contract()["cases"][0]
        detail = model.parse_stdout(synthetic_stdout(1), spec, model.parse_csv(synthetic_csv(1), 1))
        self.assertEqual(detail["subthreshold_leakage_per_bank_mw"], 0.006)
        for old, new in [(b"Temperature : 360", b"Temperature : 300"),
                         (b"Best Ndbl : 2", b"Best Ndbl : 4"),
                         (b"Cycle time (ns) : 3", b"Cycle time (ns) : 4"),
                         (b"Total gate leakage power of a bank (mW) : 0.004",
                          b"Total gate leakage power of a bank (mW) : 0.04")]:
            data = synthetic_stdout(1)
            self.assertIn(old, data)
            with self.subTest(old=old), self.assertRaises(ValueError):
                model.parse_stdout(data.replace(old, new), spec,
                                   model.parse_csv(synthetic_csv(1), 1))

    def test_stdout_rejects_duplicate_result_and_exit_zero_error_text(self):
        spec = contract()["cases"][0]
        values = model.parse_csv(synthetic_csv(1), 1)
        for extra in [b"\nAccess time (ns) : 2\n", b"\nERROR: no valid cache organizations found\n",
                      ("\n" + model.BANNER + "\n").encode()]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                model.parse_stdout(synthetic_stdout(1) + extra, spec, values)

    def test_stdout_dimensions_must_match_csv_organization_area(self):
        spec = contract()["cases"][0]
        values = model.parse_csv(synthetic_csv(1), 1)
        original = synthetic_stdout(1)
        changed = original.replace(b"Cache height x width (mm) : 1 x 1.5",
                                   b"Cache height x width (mm) : 10 x 10")
        self.assertNotEqual(original, changed)
        with self.assertRaises(ValueError):
            model.parse_stdout(changed, spec, values)
        # Independent six-significant-digit rounding in dimensions and area
        # must not reject the same source-defined product.
        rounded = original.replace(b"Cache height x width (mm) : 1 x 1.5",
                                   b"Cache height x width (mm) : 1.23457 x 1.215")
        rounded_values = model.parse_csv(synthetic_csv(1, {"Area (mm2)": 1.5}), 1)
        model.parse_stdout(rounded, spec, rounded_values)

    def test_case_status_stderr_input_and_swapped_banks_fail_closed(self):
        value = contract()
        spec = value["cases"][0]
        mutations = {"status.json": b'{"returncode":0,"timed_out":true}',
                     "stderr.txt": b"File out.csv could not be opened successfully\n",
                     "input.cfg": b"substituted configuration\n",
                     "out.csv": synthetic_csv(4)}
        for name, replacement in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = synthetic_case(root, spec)
                (path / name).write_bytes(replacement)
                with self.assertRaises(ValueError):
                    model.validate_case(path, spec, value)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = synthetic_case(root, spec)
            (path / "status.json").write_text('{"returncode":1,"timed_out":false}')
            with self.assertRaises(ValueError):
                model.parse_case(root, spec)

    def test_one_credit_rate_does_not_multiply_by_bank_count(self):
        value = contract()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for spec in value["cases"]:
                synthetic_case(root, spec)
            one, four = [model.validate_case(root / spec["name"], spec, value)
                         for spec in value["cases"]]
        self.assertAlmostEqual(one["optimistic_global_one_credit_transactions_per_second"], 1e9 / 3)
        self.assertAlmostEqual(four["optimistic_global_one_credit_transactions_per_second"], 1e9 / 12)
        self.assertAlmostEqual(four["optimistic_local_sram_row_bytes_per_second"], (1e9 / 12) * 32)
        self.assertEqual(four["modeled_standby_leakage_per_bank_mw"], 0.01)
        self.assertNotIn("whole_machine_wall_power_w", four)
        changed = copy.deepcopy(four)
        changed["model_binary_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            model.assemble_report(value, [one, changed], {})

    def test_report_retains_conditional_labels_unknowns_and_required_demand(self):
        value = contract()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for spec in value["cases"]:
                synthetic_case(root, spec)
            cases = [model.validate_case(root / spec["name"], spec, value)
                     for spec in value["cases"]]
        report = model.assemble_report(value, cases, {})
        self.assertEqual(report["classification"], "conditional_analytic_model_observations_only")
        self.assertFalse(report["physical_characterization"])
        self.assertFalse(report["physical_ppa_accepted"])
        self.assertFalse(report["full_hash_projection_performed"])
        self.assertTrue(all(item is None for item in report["unknown"].values()))
        demand = report["required_demand_only"]
        self.assertEqual(demand["required_aggregate_transactions_per_second_at_target"], 58376192000000)
        self.assertEqual(demand["required_aggregate_local_sram_row_bytes_per_second_at_target"], 1868038144000000)
        self.assertIsNone(demand["aggregate_offchip_bytes_per_hash"])
        self.assertAlmostEqual(report["bank4_divided_by_bank1_model_ratios"]["optimistic_one_credit_service_rate"], 0.25)

    def test_build_report_source_provenance_with_parser_only_fixtures(self):
        value = contract()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for spec in value["cases"]:
                synthetic_case(root, spec)
            report, provenance = model.build_report(ROOT / "contract.json", ROOT / "inputs", root)
        self.assertEqual(provenance["contract_sha256"], model.digest((ROOT / "contract.json").read_bytes()))
        self.assertEqual(set(provenance["case_artifact_bindings"]), {"bank1", "bank4"})
        self.assertEqual(provenance["scientific_acceptance"], "unverified_pending_independent_review")
        self.assertEqual(report["source_bindings"], provenance["source_bindings"])

    def test_exclusive_outputs_and_index(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report"
            model.write_outputs(output, {"conditional": True}, {"physical": False})
            index = model.strict_json((output / "artifacts.sha256.json").read_bytes())
            self.assertEqual(set(index), {"memory-baseline.json", "provenance.json"})
            for name, pin in index.items():
                self.assertEqual(pin, model.digest((output / name).read_bytes()))
            with self.assertRaises(ValueError):
                model.write_outputs(output, {}, {})

    def test_nonfinite_or_private_output_rejected_before_directory_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index, data in enumerate([{"n": math.inf}, {"path": "/home/server/private"}]):
                path = root / str(index)
                with self.assertRaises(ValueError):
                    model.write_outputs(path, data, {})
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
