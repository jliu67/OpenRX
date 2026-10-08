#!/usr/bin/env python3
"""Replay the dated source audit; no daemon, mining, or accounts are involved."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen


STABLE = "22578c3f7d7b4b6dd85ff7daa42a827d97cc53d0"
RANDOMX = "12f2c2ffe2108d6cf54c391fee33c8bc3646cdab"
BETA = "d816367cb1aa405bfa68a20ac3e034d0759d968e"


def table(text, name):
    body = text.split("const hardfork_t " + name + "[] = {", 1)[1].split("};", 1)[0]
    return [tuple(map(int, match)) for match in re.findall(
        r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}", body)]


def audit(payloads):
    def source(key):
        return payloads[key].decode("utf-8")

    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError("source assertion failed: " + name)
        checks.append(name)

    stable_forks = table(source("stable_src/hardforks/hardforks.cpp"), "mainnet_hard_forks")
    master_forks = table(source("master_src/hardforks/hardforks.cpp"), "mainnet_hard_forks")
    check("stable_mainnet_ends_at_hf16", stable_forks[-1][:2] == (16, 2689608)
          and all(x[0] <= 16 for x in stable_forks))
    check("master_mainnet_table_matches_stable", master_forks == stable_forks)
    check("randomx_started_at_hf12_height1978433", (12, 1978433, 0, 1571419280) in stable_forks)
    check("randomx_block_version12", re.search(r"#define\s+RX_BLOCK_VERSION\s+12\b",
          source("stable_src/crypto/hash-ops.h")) is not None)
    tx = source("stable_src/cryptonote_core/cryptonote_tx_utils.cpp")
    check("stable_longhash_calls_legacy_randomx", "if (major_version >= RX_BLOCK_VERSION)" in tx
          and "rx_slow_hash(hash.data, bd.data(), bd.size(), res.data);" in tx)
    master = source("master_src/cryptonote_basic/cryptonote_format_utils.cpp")
    check("master_longhash_calls_legacy_randomx", "if (major_version >= RX_BLOCK_VERSION)" in master
          and "crypto::rx_slow_hash(seed_hash.data, block_hashing_blob.data(), block_hashing_blob.size(), res.data);" in master)
    rx = source("stable_src/crypto/rx-slow-hash.c")
    check("stable_vm_uses_legacy_flags", "const randomx_flags flags = enabled_flags() & ~disabled_flags();" in rx
          and "randomx_calculate_hash" in rx and "RANDOMX_FLAG_V2" not in rx)
    check("bundled_randomx_has_no_v2_flag", "RANDOMX_FLAG_V2" not in source("rx123_src/randomx.h"))
    chain = source("stable_src/cryptonote_core/blockchain.cpp")
    check("mainnet_table_installed_and_block_versions_checked", "mainnet_hard_forks[n].version" in chain
          and "if (!m_hardfork->check(bl))" in chain)
    beta_forks = source("beta30_src/hardforks/hardforks.cpp")
    check("beta_mainnet_values_explicitly_mock", "// Mock values for tests\n  { 17, 2689609" in beta_forks)
    testnet = table(beta_forks, "testnet_hard_forks")
    check("beta_testnet_hf17_at3102800_hf18_at3103520", testnet[-2][:2] == (17, 3102800)
          and testnet[-1][:2] == (18, 3103520))
    config = source("beta30_src/cryptonote_config.h")
    check("beta_randomx_v2_hf17", re.search(r"#define\s+HF_VERSION_RANDOMX_V2\s+17\b", config) is not None)
    check("beta_pow_commitment_hf17", re.search(r"#define\s+HF_VERSION_POW_COMMITMENT\s+17\b", config) is not None)
    fmt = source("beta30_src/cryptonote_basic/cryptonote_format_utils.cpp")
    check("beta_selects_v2_at_hf17", "return (hf_version >= HF_VERSION_RANDOMX_V2) ? RX_VARIANT_2 : RX_VARIANT_1;" in fmt)
    check("beta_block_pow_adds_commitment", "if (major_version >= HF_VERSION_POW_COMMITMENT)" in fmt
          and "crypto::rx_commitment" in fmt)
    if "latest" in payloads:
        latest = json.loads(payloads["latest"])
        check("observed_stable_release_v01853", latest["tag_name"] == "v0.18.5.3"
              and latest["prerelease"] is False and latest["published_at"] == "2026-10-06T09:31:49Z")
        check("annotated_stable_tag_resolves_to_commit", json.loads(payloads["stable_tag"])["object"]["sha"] == STABLE)
        check("stable_randomx_gitlink_and_tag_match", json.loads(payloads["stable_submodule"])["sha"] == RANDOMX
              and json.loads(payloads["randomx_tag"])["object"]["sha"] == RANDOMX)
        check("master_randomx_gitlink_matches_stable", json.loads(payloads["master_submodule"])["sha"] == RANDOMX)
        beta_release = json.loads(payloads["beta_release"])
        check("beta_release_is_prerelease_stressnet", beta_release["prerelease"] is True
              and "October 5, 2026, at block 3102800" in beta_release["body"]
              and "hard fork from the current testnet" in beta_release["body"])
        check("beta_tag_resolves_to_audited_commit", json.loads(payloads["beta30_tag_object"])["object"]["sha"] == BETA)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture-dir", type=Path, help="Offline raw captures from this audit session")
    mode.add_argument("--fetch-sources", action="store_true", help="GET pinned raw Git files; dynamic API/web captures excluded")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("source-manifest-20261008.json"))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    payloads = {}
    verified = []
    for record in manifest["records"]:
        if args.fetch_sources:
            if record["kind"] != "git_source":
                continue
            with urlopen(Request(record["url"], headers={"User-Agent": "OpenRX source audit/1.0"}), timeout=30) as response:
                payload = response.read()
        else:
            payload = (args.capture_dir / record["capture_file"]).read_bytes()
        if len(payload) != record["bytes"] or hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError("capture digest mismatch: " + record["key"])
        if record["kind"] == "git_source":
            git_hash = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            if git_hash != record["sha"]:
                raise ValueError("Git blob mismatch: " + record["key"])
        payloads[record["key"]] = payload
        verified.append(record["key"])
    checks = audit(payloads)
    print(json.dumps({"schema_version": 1, "result": "pass", "mode": "pinned-source-fetch" if args.fetch_sources else "offline-capture-replay",
                      "verified_capture_count": len(verified), "source_assertion_count": len(checks), "checks": checks,
                      "live_tip_observed": False, "mainnet_activation_inference": "RandomX v1 under the audited released consensus rules",
                      "mainnet_v2_schedule": "No activation height/date in the audited mainnet release/master schedule"}, indent=2))


if __name__ == "__main__":
    main()
