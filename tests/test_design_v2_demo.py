import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import design_v2_demo


class DesignV2DemoSafetyTest(unittest.TestCase):
    @staticmethod
    def _private_lookup(_host, _port):
        return [(None, None, None, None, ("172.18.0.3", 5432))]

    def test_accepts_only_exact_local_database_target(self):
        local = "postgresql://gitpod:local-only@db:5432/metalwolft_design_v2_demo"
        target = design_v2_demo.validate_test_database_url(local, lookup=self._private_lookup)
        self.assertEqual((target.host, target.port, target.database, target.username),
                         ("db", 5432, "metalwolft_design_v2_demo", "gitpod"))
        for unsafe in (
            local.replace("@db:", "@prod.neon.tech:"),
            local.replace("/metalwolft_design_v2_demo", "/example"),
            local.replace("gitpod:", "neondb_owner:"),
            local.replace(":5432/", ":5433/"),
        ):
            with self.assertRaises(RuntimeError):
                design_v2_demo.validate_test_database_url(unsafe, lookup=self._private_lookup)

    def test_rejects_public_resolution_even_for_db_alias(self):
        local = "postgresql://gitpod:local-only@db:5432/metalwolft_design_v2_demo"
        with self.assertRaises(RuntimeError):
            design_v2_demo.validate_test_database_url(
                local, lookup=lambda *_args: [(None, None, None, None, ("8.8.8.8", 5432))]
            )

    def test_refuses_execution_outside_codespaces(self):
        with patch.dict(os.environ, {"CODESPACES": "false"}):
            with self.assertRaisesRegex(RuntimeError, "Codespaces"):
                design_v2_demo.safe_target()

    def test_local_storage_keeps_objects_private_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(design_v2_demo, "STATE_DIR", Path(directory)):
                storage = design_v2_demo.LocalDemoStorage()
                storage.put_object(storage_key="design-results/demo/file.glb", content=b"glTF", mime_type="model/gltf-binary")
                self.assertEqual(storage.get_object(storage_key="design-results/demo/file.glb"), b"glTF")
                self.assertEqual(storage.head_object(storage_key="design-results/demo/file.glb")["ContentLength"], 4)
                with self.assertRaises(Exception):
                    storage.get_object(storage_key="../outside")
                with self.assertRaises(Exception):
                    storage.put_object(storage_key="/absolute", content=b"bad", mime_type="text/plain")
                storage.delete_object(storage_key="design-results/demo/file.glb")
                self.assertFalse((Path(directory) / "objects/design-results/demo/file.glb").exists())


if __name__ == "__main__":
    unittest.main()
