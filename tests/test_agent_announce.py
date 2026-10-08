"""Offline authorization and duplicate-prevention tests; no GitHub writes."""
import copy
import importlib.util
import pathlib
import sys
import unittest

p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "agent_announce.py"
spec = importlib.util.spec_from_file_location("agent_announce", p)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def event(text="/openrx announce\nQuick future agent update"):
    return {"action": "created", "repository": {"full_name": "jliu67/OpenRandomX", "owner": {"login": "jliu67"}},
            "issue": {"number": 5}, "comment": {"id": 13579, "body": text,
            "user": {"login": "jliu67"}, "html_url": "https://github.com/jliu67/OpenRandomX/issues/5#issuecomment-13579"}}


class AnnouncementTests(unittest.TestCase):
    def test_parses_valid(self):
        self.assertEqual(mod.announcement(event())[2], "Quick future agent update")

    def test_wrong_hub_and_pull_request_ignored(self):
        for issue in ({"number": 3}, {"number": 5, "pull_request": {}}):
            data = event()
            data["issue"] = issue
            self.assertIsNone(mod.announcement(data))

    def test_authorization_denies_other_authors_and_bot(self):
        for actor in ("someone", mod.BOT, ""):
            data = event()
            data["comment"]["user"]["login"] = actor
            self.assertIsNone(mod.announcement(data))

    def test_only_created_first_line_command(self):
        for text in ("Hello\n/openrx announce\nNo", "/openrx claim a/b", "/openrx announced\nNo"):
            self.assertIsNone(mod.announcement(event(text)))
        data = event()
        data["action"] = "edited"
        self.assertIsNone(mod.announcement(data))

    def test_length_and_missing_source(self):
        for text in ("/openrx announce", "/openrx announce\n" + "x" * 1201):
            with self.assertRaises(ValueError):
                mod.announcement(event(text))
        data = event()
        data["comment"]["id"] = "bad"
        with self.assertRaises(ValueError):
            mod.announcement(data)

    def test_posts_once_and_idempotent_on_replay(self):
        saved = []
        def fake(url, token, method="GET", data=None):
            if method == "POST":
                self.assertIn("Original request", data["body"])
                self.assertIn("13579 -->", data["body"])
                saved.append({"id": 222, "user": {"login": mod.BOT}, "body": data["body"]})
                return {"id": 222}
            return saved
        self.assertEqual(mod.publish(event(), "fake", fake), "posted")
        self.assertEqual(mod.publish(event(), "fake", fake), "already-posted")
        self.assertEqual(len(saved), 1)

    def test_spoofed_human_marker_does_not_block(self):
        saved = [{"id": 2, "user": {"login": "other"}, "body": mod.MARKER + "13579 -->"}]
        def fake(url, token, method="GET", data=None):
            if method == "POST":
                saved.append({"id": 3, "user": {"login": mod.BOT}, "body": data["body"]})
                return {"id": 3}
            return saved
        self.assertEqual(mod.publish(event(), "fake", fake), "posted")

    def test_no_actions_without_authorized_message(self):
        def unreachable(*args):
            raise AssertionError("API should not be called")
        data = event()
        data["comment"]["user"]["login"] = "stranger"
        self.assertEqual(mod.publish(data, "fake", unreachable), "ignored")


if __name__ == "__main__":
    unittest.main()
