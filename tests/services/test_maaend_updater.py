import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from app.services.maaend_updater import run_maaend_update
from app.utils import ProcessResult


class MaaEndUpdaterServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_writes_normalized_spec_and_builds_runtime_command(self):
        with TemporaryDirectory() as directory:
            root_path = Path(directory) / "MaaEnd"
            root_path.mkdir()
            updater_path = Path(directory) / "maafw-updater"
            updater_path.write_text("", encoding="utf-8")
            updater_path.chmod(0o755)

            async def run_process(*args, **kwargs):
                spec_path = Path(args[3])
                self.assertEqual(args[0], updater_path)
                self.assertEqual(args[1], "update")
                self.assertEqual(args[2], "--spec")
                self.assertEqual(args[4], "--root")
                self.assertEqual(Path(args[5]), root_path)
                self.assertNotIn("--platform", args)
                self.assertEqual(args[args.index("--source") + 1], "auto")
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                self.assertEqual(spec["mas_update"]["scope"], "application")
                return ProcessResult(
                    stdout=json.dumps(
                        {
                            "event": "result",
                            "success": True,
                            "old_version": "v4.5.2",
                            "new_version": "v4.5.3",
                        }
                    ),
                    stderr="",
                    returncode=0,
                )

            with patch(
                "app.services.maaend_updater.ProcessRunner.run_process",
                new=AsyncMock(side_effect=run_process),
            ):
                result = await run_maaend_update(
                    updater_path=updater_path,
                    root_path=root_path,
                    spec={
                        "version": "4.5.3",
                        "github": "https://github.com/MaaEnd/MaaEnd",
                        "mirrorchyan_rid": "MaaEnd",
                        "mas_update": {"scope": "application"},
                    },
                    current_version="v4.5.2",
                )

        self.assertTrue(result.success)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.events[0]["event"], "result")


if __name__ == "__main__":
    unittest.main()
