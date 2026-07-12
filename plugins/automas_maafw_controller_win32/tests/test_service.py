from __future__ import annotations

import unittest

from automas_maafw_controller_win32.service import (
    MaaFWWin32ControllerService,
    MaaFWWin32Window,
)


class MaaFWWin32ControllerServiceTest(unittest.TestCase):
    def test_match_windows_accepts_controller_contract(self) -> None:
        controller = {
            "name": "Win32-Front",
            "type": "Win32",
            "win32": {
                "class_regex": "EndfieldClass",
                "window_regex": "Endfield",
            },
        }
        windows = [
            MaaFWWin32Window(
                hWnd=36163,
                className="EndfieldClass",
                windowName="Arknights: Endfield",
            )
        ]

        matches = MaaFWWin32ControllerService().match_controller_windows(
            controller,
            windows,
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].hWnd, 36163)
        self.assertEqual(matches[0].controllerName, "Win32-Front")


if __name__ == "__main__":
    unittest.main()
