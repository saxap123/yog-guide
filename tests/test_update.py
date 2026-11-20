"""Step 5: `python -m yog update` — diff and changelog logic (no network, no subprocesses)."""
import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from yog import update  # noqa: E402


class TestUpdateDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = update.snapshot()

    def test_no_change(self):
        d = update.diff(self.before, copy.deepcopy(self.before))
        for k in ("added", "removed", "changed", "revised", "tiers", "pages", "new_unpaired", "todo_new"):
            self.assertEqual(d[k], [], k)
        self.assertIn("No data change.", update.changelog_entry(d, self.before, {}))

    def test_changes_are_reported(self):
        after = copy.deepcopy(self.before)
        keys = sorted(after["records"])
        gone = keys[0]
        del after["records"][gone]
        edited = keys[1]
        after["records"][edited]["fields"]["builds"] = "x"
        after["records"][edited]["revid"] = 999999
        bumped = keys[2]
        after["records"][bumped]["revid"] = 999998
        after["records"]["char-new"] = {"kind": "character", "label": "New Hero (新黑卫)", "revid": 1, "fields": {}}
        after["names"]["characters"]["新黑卫"] = None
        after["names"]["gear"]["新装备"] = "New Gear"
        tier = next(iter(after["tiers"]))
        after["tiers"][tier] = "T9"
        d = update.diff(self.before, after)
        self.assertEqual([r["label"] for r in d["added"]], ["New Hero (新黑卫)"])
        self.assertEqual([r["label"] for r in d["removed"]], [self.before["records"][gone]["label"]])
        self.assertEqual([(r["label"], r["changed"]) for r in d["changed"]],
                         [(self.before["records"][edited]["label"], ["builds"])])
        self.assertEqual([r["label"] for r in d["revised"]], [self.before["records"][bumped]["label"]])
        self.assertEqual(d["new_unpaired"], [("characters", "新黑卫")])
        self.assertEqual(d["new_names"], [("gear", "新装备", "New Gear")])
        self.assertEqual(d["tiers"], [(tier, self.before["tiers"][tier], "T9")])
        text = update.changelog_entry(d, self.before, {"某名": 2})
        for s in ("### Added", "New Hero (新黑卫)", "### Changed", "builds (revid", "### Removed",
                  "### PvE tier list", "→ T9", "新黑卫 (characters)", "某名"):
            self.assertIn(s, text)

    def test_volatile_fields_ignored(self):
        self.assertTrue({"fetched_at", "revid", "permalink", "i18n"} <= update.VOLATILE)
        for r in self.before["records"].values():
            self.assertFalse(set(r["fields"]) & update.VOLATILE)


if __name__ == "__main__":
    unittest.main()
