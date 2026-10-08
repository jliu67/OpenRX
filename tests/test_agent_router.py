"""Synthetic communication fixtures, not mining measurements or active agents."""
import copy
import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("agent_router", Path(__file__).resolve().parents[1] / "scripts/agent_router.py")
router = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = router
SPEC.loader.exec_module(router)
NOW = router.timestamp("2026-10-08T04:00:00Z")


def issue(**extra):
    item = {"number": 6, "body": router.THREAD + "\n### To\nresearch\n\n### From\nfixture/a",
            "state": "open", "user": {"login": "owner"}, "comments": 0, "labels": [{"name": "bug"}]}
    item.update(extra)
    return item


def comment(cid, body, actor="owner", minute=0, **extra):
    created = router.iso(NOW + dt.timedelta(minutes=minute))
    item = {"id": cid, "body": body, "user": {"login": actor}, "created_at": created, "updated_at": created}
    item.update(extra)
    return item


def reduce(comments, target=None, writers=None, now=None):
    return router.reduce_thread(target or issue(), comments, writers or {"owner", "writer"}, now or NOW + dt.timedelta(hours=1))


class ProtocolTests(unittest.TestCase):
    def test_initial_routing(self):
        state = reduce([])
        self.assertEqual((state["role"], state["status"], state["claim"]), ("research", "ready", None))

    def test_missing_or_duplicate_role_falls_back(self):
        for body in (router.THREAD, router.THREAD + "\n### To\nevil\n", router.THREAD + "\n### To\nrtl\n### To\nresearch"):
            with self.subTest(body=body):
                state = reduce([], issue(body=body))
                self.assertEqual(state["role"], "coordinator")
                self.assertTrue(state["warnings"])

    def test_crlf_metadata(self):
        self.assertEqual(reduce([], issue(body=router.THREAD + "\r\n### To\r\ntooling\r\n"))["role"], "tooling")

    def test_non_protocol_text_not_executed(self):
        for text in ("hello", "```\n/openrx claim x/y\n```", "text\n/openrx claim x/y", "$(touch /tmp/pwn)"):
            self.assertIsNone(router.command(text))

    def test_invalid_commands(self):
        for text in ("/openrx claim $(id)", "/openrx route bad", "/openrx claim a/b more", "/openrx done x/y", "/openrx run echo"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                router.command(text)

    def test_claim_and_conflict_same_account(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx claim agent/b", minute=1)])
        self.assertEqual(state["claim"]["session"], "agent/a")
        self.assertIn("another session", state["audit"][-1]["result"])

    def test_claim_conflict_other_account(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx claim agent/a", actor="writer", minute=1)])
        self.assertEqual(state["claim"]["actor"], "owner")
        self.assertIn("rejected", state["audit"][-1]["result"])

    def test_sorted_history(self):
        state = reduce([comment(20, "/openrx claim second/b", minute=1), comment(10, "/openrx claim first/a")])
        self.assertEqual(state["claim"]["session"], "first/a")

    def test_wrong_session_cannot_release(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx release agent/b", minute=1)])
        self.assertIsNotNone(state["claim"])

    def test_other_actor_cannot_release(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx release agent/a", actor="writer", minute=1)])
        self.assertIsNotNone(state["claim"])

    def test_heartbeat_extends_lease(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx heartbeat agent/a", minute=30)])
        self.assertEqual(state["claim"]["expires_at"], "2026-10-08T08:30:00Z")

    def test_expiry_at_boundary(self):
        self.assertIsNone(reduce([comment(1, "/openrx claim agent/a")], now=NOW + dt.timedelta(hours=4))["claim"])

    def test_expired_claim_can_be_replaced(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx claim next/b", minute=241)], now=NOW + dt.timedelta(hours=5))
        self.assertEqual(state["claim"]["session"], "next/b")

    def test_expired_heartbeat_does_not_resurrect(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx heartbeat agent/a", minute=241)], now=NOW + dt.timedelta(hours=5))
        self.assertIsNone(state["claim"])
        self.assertIn("rejected", state["audit"][-1]["result"])

    def test_release_block_review_relinquish_claim(self):
        for op, expected in (("release", "ready"), ("blocked", "blocked"), ("review", "review")):
            with self.subTest(op=op):
                state = reduce([comment(1, "/openrx claim agent/a"), comment(2, f"/openrx {op} agent/a", minute=1)])
                self.assertEqual(state["status"], expected)
                self.assertIsNone(state["claim"])

    def test_done_requires_review(self):
        state = reduce([comment(1, "/openrx done")])
        self.assertEqual(state["status"], "ready")
        self.assertIn("rejected", state["audit"][0]["result"])

    def test_review_done_reopen(self):
        comments = [comment(1, "/openrx claim agent/a"), comment(2, "/openrx review agent/a", minute=1), comment(3, "/openrx done", minute=2)]
        self.assertEqual(reduce(comments)["status"], "done")
        self.assertEqual(reduce(comments + [comment(4, "/openrx reopen", minute=3)])["status"], "ready")

    def test_cannot_claim_while_waiting_for_review(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx review agent/a", minute=1), comment(3, "/openrx claim next/b", minute=2)])
        self.assertEqual(state["status"], "review")

    def test_cannot_reopen_active_claim(self):
        state = reduce([comment(1, "/openrx claim agent/a"), comment(2, "/openrx reopen", minute=1)])
        self.assertEqual(state["status"], "claimed")

    def test_unauthorized_controls_rejected(self):
        state = reduce([comment(1, "/openrx claim outsider/a", actor="outsider"), comment(2, "/openrx route rtl", actor="outsider")])
        self.assertIsNone(state["claim"])
        self.assertEqual(state["role"], "research")

    def test_untrusted_issue_requires_writer_optin(self):
        target = issue(user={"login": "outsider"})
        self.assertIsNone(reduce([], target))
        self.assertEqual(reduce([comment(1, "/openrx route review")], target)["role"], "review")

    def test_route_enrolls_existing_issue(self):
        target = issue(body="Existing baseline task")
        self.assertIsNone(reduce([], target))
        self.assertEqual(reduce([comment(1, "/openrx route benchmark")], target)["role"], "benchmark")

    def test_claim_does_not_silently_enroll(self):
        self.assertIsNone(reduce([comment(1, "/openrx claim a/b")], issue(body="Not enrolled")))

    def test_edited_commands_ignored(self):
        state = reduce([comment(1, "/openrx claim a/b", updated_at="2026-10-08T04:01:00Z")])
        self.assertIsNone(state["claim"])
        self.assertIn("edited", state["audit"][0]["result"])

    def test_future_command_rejected(self):
        self.assertIsNone(reduce([comment(1, "/openrx claim a/b", minute=100)])["claim"])

    def test_closed_issue_releases_claim(self):
        state = reduce([comment(1, "/openrx claim a/b")], issue(state="closed"))
        self.assertEqual(state["status"], "closed")
        self.assertIsNone(state["claim"])

    def test_replay_is_identical(self):
        comments = [comment(1, "/openrx claim a/b"), comment(2, "/openrx route tooling", minute=1)]
        self.assertEqual(router.render(reduce(comments)), router.render(reduce(list(reversed(comments)))))

    def test_audit_bounded(self):
        self.assertEqual(len(reduce([comment(i, "/openrx route tooling") for i in range(1, 40)])["audit"]), 20)

    def test_labels_are_allowlisted(self):
        self.assertTrue(router.desired_labels(reduce([])) <= set(router.label_catalog()))

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            router.timestamp("2026-10-08T04:00:00")


class FakeAPI:
    def __init__(self, target=None, comments=None):
        self.target = copy.deepcopy(target or issue())
        self.comments = copy.deepcopy(comments or [])
        self.target["comments"] = len(self.comments)
        self.calls = []
        self.writers = {"owner", "writer"}

    def can_write(self, login):
        return login in self.writers

    def pages(self, path):
        if path == "/labels":
            return [{"name": name} for name in router.label_catalog()]
        if path == "/issues?state=all":
            return [copy.deepcopy(self.target)]
        if path.endswith("/comments"):
            return copy.deepcopy(self.comments)
        raise AssertionError(path)

    def request(self, method, path, data=None):
        self.calls.append((method, path, data))
        if method == "GET" and path == "/issues/6":
            return copy.deepcopy(self.target)
        if method == "POST" and path.endswith("/labels"):
            self.target["labels"] += [{"name": x} for x in data["labels"]]
        elif method == "DELETE" and "/labels/" in path:
            name = router.urllib.parse.unquote(path.rsplit("/", 1)[1])
            self.target["labels"] = [x for x in self.target["labels"] if x["name"] != name]
        elif method == "POST" and path.endswith("/comments"):
            cid = max([x["id"] for x in self.comments] + [1000]) + 1
            self.comments.append(comment(cid, data["body"], actor=router.BOT))
            self.target["comments"] = len(self.comments)
        elif method == "PATCH" and "/issues/comments/" in path:
            cid = int(path.rsplit("/", 1)[1])
            next(x for x in self.comments if x["id"] == cid)["body"] = data["body"]
        else:
            raise AssertionError((method, path, data))


class IntegrationTests(unittest.TestCase):
    def test_writer_whitespace_command_identity(self):
        api = FakeAPI(comments=[comment(1, "  /openrx claim agent/writer", actor="writer")])
        router.run(api, {}, NOW)
        self.assertIn('"session": "agent/writer"', api.comments[-1]["body"])

    def test_closed_issue_recovery_without_original_event(self):
        api = FakeAPI(target=issue(state="closed"), comments=[comment(1, "/openrx claim a/b")])
        self.assertEqual(router.run(api, {}, NOW), 1)
        self.assertIn({"name": "agent:status:closed"}, api.target["labels"])

    def test_label_sync_and_receipt(self):
        api = FakeAPI(comments=[comment(1, "/openrx claim a/b")])
        self.assertEqual(router.run(api, {}, NOW + dt.timedelta(minutes=1)), 1)
        self.assertIn({"name": "bug"}, api.target["labels"])
        self.assertIn({"name": "agent:status:claimed"}, api.target["labels"])
        self.assertEqual(sum(x["body"].startswith(router.SUMMARY) for x in api.comments), 1)

    def test_idempotent_run_performs_no_duplicate_writes(self):
        api = FakeAPI()
        router.run(api, {}, NOW)
        api.calls.clear()
        router.run(api, {}, NOW + dt.timedelta(minutes=1))
        self.assertEqual(api.calls, [])

    def test_status_change_updates_one_receipt(self):
        api = FakeAPI(comments=[comment(1, "/openrx claim a/b")])
        router.run(api, {}, NOW)
        api.comments.append(comment(2000, "/openrx release a/b", minute=1))
        api.target["comments"] += 1
        router.run(api, {}, NOW + dt.timedelta(minutes=2))
        self.assertEqual(sum(x["body"].startswith(router.SUMMARY) for x in api.comments), 1)
        self.assertIn({"name": "agent:status:ready"}, api.target["labels"])
        self.assertNotIn({"name": "agent:status:claimed"}, api.target["labels"])

    def test_spoofed_bot_marker_not_overwritten(self):
        spoof = router.SUMMARY + "fake"
        api = FakeAPI(comments=[comment(1, spoof)])
        router.run(api, {}, NOW)
        self.assertEqual(api.comments[0]["body"], spoof)
        self.assertEqual(len(api.comments), 2)

    def test_pull_requests_skipped(self):
        api = FakeAPI(target=issue(pull_request={"url": "not-used"}))
        self.assertEqual(router.run(api, {}, NOW), 0)
        self.assertEqual(api.calls, [])

    def test_unrelated_issue_not_modified(self):
        api = FakeAPI(target=issue(body="Keep existing work unchanged"))
        self.assertEqual(router.run(api, {}, NOW), 0)
        self.assertEqual(api.calls, [])

    def test_explicit_closed_issue_reconciled(self):
        api = FakeAPI(target=issue(state="closed"))
        self.assertEqual(router.run(api, {"inputs": {"issue_number": "6"}}, NOW), 1)
        self.assertIn({"name": "agent:status:closed"}, api.target["labels"])

    def test_input_not_shell_or_api_path(self):
        with self.assertRaises(ValueError):
            router.run(FakeAPI(), {"inputs": {"issue_number": "6; curl evil"}}, NOW)

    def test_invalid_repository_and_missing_token(self):
        for repo, token in (("https://evil/a", "x"), ("owner/repo\n", "x"), ("owner/repo", "")):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                router.GitHubAPI(repo, token)

    def test_owner_and_writer_permissions(self):
        api = router.GitHubAPI("owner/repo", "fixture")
        self.assertTrue(api.can_write("owner"))
        with patch.object(api, "request", return_value={"permission": "write"}):
            self.assertTrue(api.can_write("writer"))
        with patch.object(api, "request", return_value={"permission": "read"}):
            self.assertFalse(api.can_write("reader"))

    def test_permission_lookup_fails_closed(self):
        api = router.GitHubAPI("owner/repo", "fixture")
        with patch.object(api, "request", side_effect=router.APIError(404, "/test")):
            self.assertFalse(api.can_write("unknown"))
        with patch.object(api, "request", side_effect=router.APIError(403, "/test")), self.assertRaises(router.APIError):
            api.can_write("unknown")

    def test_pagination_reads_all_pages(self):
        api = router.GitHubAPI("owner/repo", "fixture")
        with patch.object(api, "request", side_effect=[[{}] * 100, [{"last": True}]]) as call:
            self.assertEqual(len(api.pages("/issues?state=open")), 101)
            self.assertIn("&per_page=100&page=2", call.call_args.args[1])

    def test_pagination_limit_is_not_partial_success(self):
        api = router.GitHubAPI("owner/repo", "fixture")
        with patch.object(api, "request", return_value=[{}] * 100), self.assertRaises(RuntimeError):
            api.pages("/issues")


if __name__ == "__main__":
    unittest.main()
