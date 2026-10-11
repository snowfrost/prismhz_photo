#!/usr/bin/env python3
"""Positive examples and independent invalid mutations; no MJ generation."""
import copy
import json
import unittest
from pathlib import Path

from validate_outputs import parameters, to_markdown, validate

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "references" / "examples.json").read_text(encoding="utf-8"))
        self.case = self.data["cases"][0]

    def rejected(self, substring):
        errors = validate(self.data)
        self.assertTrue(any(substring in error for error in errors), errors)

    def test_all_authored_cases_pass(self):
        self.assertEqual(validate(self.data), [])

    def test_missing_second_version(self):
        del self.case["mj_without_moodboard"]
        self.rejected("missing mj_without")

    def test_deleted_parameter_is_not_rewrite(self):
        self.case["mj_without_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--s 125", "--s 100")
        self.rejected("only differ in parameters")

    def test_no_board_must_disable_ui(self):
        self.case["mj_without_moodboard"]["setup_note"] = "保留 Attach to prompt 和 Style reference。"
        self.rejected("disable automatic personalization")

    def test_no_board_must_not_drop_attach(self):
        self.case["mj_without_moodboard"]["reference_setup"]["attach_to_prompt"] = {"mode": "none", "assets": []}
        self.rejected("silently changes reference roles")

    def test_no_board_p_is_rejected(self):
        self.case["mj_without_moodboard"]["prompt"] = self.case["mj_without_moodboard"]["prompt"].replace("--v 8.2", "--p TESTONLY --v 8.2")
        self.rejected("no-board prompt contains")

    def test_board_sw_and_sv_are_each_rejected(self):
        for flag in ("sw 100", "sv 6"):
            with self.subTest(flag=flag):
                candidate = copy.deepcopy(self.data)
                candidate["cases"][0]["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", f"--{flag} --v 8.2")
                self.assertTrue(any("incompatible" in e for e in validate(candidate)))

    def test_bare_p_is_rejected_when_board_unknown(self):
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--p --v 8.2")
        self.rejected("unknown board")

    def test_iw_cannot_mean_attach(self):
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--iw 2 --v 8.2")
        self.rejected("iw applies to Image Prompt")

    def test_mismatched_ratio(self):
        self.case["mj_without_moodboard"]["prompt"] = self.case["mj_without_moodboard"]["prompt"].replace("--ar 9:16", "--ar 16:9")
        self.rejected("ratio mismatch")

    def test_version_must_be_last(self):
        self.case["mj_with_moodboard"]["prompt"] += " --raw"
        self.rejected("end exactly")

    def test_changed_scene_anchor(self):
        self.case["mj_without_moodboard"]["prompt"] = self.case["mj_without_moodboard"]["prompt"].replace("lower right", "upper left")
        self.rejected("missing shared anchor")

    def test_imagegen_cannot_contain_mj_flags(self):
        self.case["imagegen"]["prompt"] += " --v 8.2"
        self.rejected("ImageGen contains MJ")

    def test_local_path_not_a_mj_url(self):
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--sref C:/private/image.png --v 8.2")
        self.rejected("local Windows path")

    def test_placeholder_not_publishable(self):
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--p YOUR_BOARD --v 8.2")
        self.rejected("placeholder")

    def test_no_visual_validation_claim(self):
        self.case["validation_level"] = "mj_visual_verified"
        self.rejected("cannot claim visual")

    def test_explicit_code_branch_syntax_only(self):
        # Synthetic token solely for parser coverage, not an actual Moodboard.
        self.case["moodboard"] = {"mode": "code", "code": "TESTONLY123", "source": "user_supplied"}
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--p TESTONLY123 --v 8.2")
        self.assertEqual(validate(self.data), [])
        self.case["moodboard"]["code"] = "DIFFERENT"
        self.rejected("not the supplied code")

    def test_reference_free_branch_stays_honest(self):
        empty = {role: {"mode": "none", "assets": []} for role in ("attach_to_prompt", "style_reference", "image_prompt")}
        self.case["reference_setup"] = empty
        for key in ("mj_with_moodboard", "mj_without_moodboard"):
            self.case[key]["reference_setup"] = copy.deepcopy(empty)
        self.case["moodboard"]["source"] = "setup_required"
        self.case["mj_with_moodboard"]["setup_note"] = "需先准备并选择情绪版，使用前开启 Personalization；Attach to prompt 与 Style reference 均不使用。"
        self.case["mj_without_moodboard"]["setup_note"] = "关闭 Personalization；Attach to prompt 与 Style reference 均不使用，本例为纯文本。"
        self.assertEqual(validate(self.data), [])

    def test_absent_board_not_reported_as_existing(self):
        self.case["moodboard"]["source"] = "setup_required"
        self.rejected("honest setup prerequisite")

    def test_parameter_parser_separates_negative_words(self):
        self.assertEqual(parameters("photo --no text, neon --ar 16:9 --v 8.2"), {"no": ["text, neon"], "ar": ["16:9"], "v": ["8.2"]})

    def test_duplicate_version(self):
        self.case["mj_with_moodboard"]["prompt"] = self.case["mj_with_moodboard"]["prompt"].replace("--v 8.2", "--v 7 --v 8.2")
        self.rejected("duplicate or wrong version")

    def test_malformed_input(self):
        for data in (None, [], {"schema_version": 1, "cases": [None]}, {"schema_version": 1, "cases": []}):
            self.assertTrue(validate(data))

    def test_markdown_retains_every_prompt_verbatim(self):
        markdown = to_markdown(self.data)
        for case in self.data["cases"]:
            for key in ("mj_with_moodboard", "mj_without_moodboard", "imagegen"):
                self.assertIn(case[key]["prompt"], markdown)
        self.assertEqual(markdown.count("```text"), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
