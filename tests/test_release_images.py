"""Release pins and the local build option must select the intended images."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("renderer", ROOT / "deploy/scripts/render_domain_manifest.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseImagesTest(unittest.TestCase):
    def test_release_and_local_selection_for_all_pins(self):
        pins = json.loads((ROOT / "deploy/release-images.json").read_text())
        for local, published in pins.items():
            with self.subTest(image=local):
                original = f"    image: {local}\n"
                expected = f"    image: {published}\n"
                self.assertEqual(MODULE.transform_images(original), expected)
                self.assertEqual(MODULE.transform_images(expected, "local"), original)
                self.assertNotIn(":latest", published)

    def test_other_images_and_unrelated_text_are_preserved(self):
        text = "  image: postgres:16\n  value: pipeline-dashboard:latest\n"
        self.assertEqual(MODULE.transform_images(text), text)
        self.assertEqual(MODULE.transform_images(text, "local"), text)

    def test_invalid_source_fails_closed(self):
        with self.assertRaises(ValueError):
            MODULE.transform_images("image: postgres:16\n", "typo")

    def test_pins_are_used_in_manifests_and_remain_domain_independent(self):
        paths = list((ROOT / "deploy/k8s").glob("*.yaml"))
        paths.append(ROOT / "deploy/golang-reverse-proxy/deployment.yaml")
        combined = "\n".join(path.read_text() for path in paths)
        for published in json.loads((ROOT / "deploy/release-images.json").read_text()).values():
            self.assertIn("image: " + published, combined)
        rendered = MODULE.transform_manifest(MODULE.transform_images(combined), "bb.example")
        self.assertIn("ghcr.io/jctanner/jira-emulator-k3s:2026.11.15", rendered)
