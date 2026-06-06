#   AUTO-MAS: A Multi-Script, Multi-Config Management and Automation Software
#   Copyright © 2025-2026 AUTO-MAS Team

#   This file is part of AUTO-MAS.

#   AUTO-MAS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   AUTO-MAS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with AUTO-MAS. If not, see <https://www.gnu.org/licenses/>.

#   Contact: DLmaster_361@163.com


from copy import deepcopy
from pathlib import Path
from typing import Any

import json5

from app.utils import get_logger

logger = get_logger("MaaEnd 任务加载器")


class MaaEndTaskLoader:
    """MaaEnd 任务加载器"""

    def __init__(self, maaend_root_path: Path, language: str = "zh_cn") -> None:
        self.root_path = maaend_root_path
        self.interface_path = maaend_root_path / "interface.json"
        self.language = language.replace("-", "_").lower()
        self._locale: dict[str, str] = {}
        self._groups: list[dict[str, Any]] = []
        self._controllers: list[dict[str, Any]] = []
        self._resources: list[dict[str, Any]] = []
        self._task_cache: dict[str, dict[str, Any]] = {}
        self._raw_data_cache: dict[str, dict[str, Any]] = {}
        self._global_option_defs: dict[str, dict[str, Any]] = {}
        self._load_all_tasks()

    def _read_json5(self, path: Path) -> dict[str, Any]:
        return json5.loads(path.read_text(encoding="utf-8"))

    def _load_locale(self, interface_data: dict[str, Any]) -> None:
        languages = interface_data.get("languages", {})
        locale_path = languages.get(self.language) or languages.get("zh_cn")
        if not locale_path:
            logger.warning("MaaEnd interface.json 未声明 zh_cn 语言文件")
            return

        locale_file = self.root_path / locale_path
        if not locale_file.exists():
            logger.warning(f"MaaEnd 语言文件不存在：{locale_file}")
            return

        try:
            self._locale = self._read_json5(locale_file)
        except Exception as e:
            logger.warning(f"读取 MaaEnd 语言文件失败：{e}")

    def _translate_text(self, value: str) -> str:
        if not value.startswith("$"):
            return value
        return self._locale.get(value[1:], value)

    def _translate(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._translate_text(value)
        if isinstance(value, list):
            return [self._translate(item) for item in value]
        if isinstance(value, dict):
            return {key: self._translate(item) for key, item in value.items()}
        return value

    @staticmethod
    def _is_internal_task(task_name: str) -> bool:
        return task_name.startswith("__MXU_")

    def _load_all_tasks(self) -> None:
        """加载 interface.json 引入的 MaaEnd 任务定义"""

        if not self.interface_path.exists():
            logger.error(f"MaaEnd interface.json 不存在：{self.interface_path}")
            return

        try:
            interface_data = self._read_json5(self.interface_path)
        except Exception as e:
            logger.error(f"读取 MaaEnd interface.json 失败：{e}")
            return

        self._load_locale(interface_data)
        self._groups = self._translate(interface_data.get("group", []))
        self._controllers = self._translate(interface_data.get("controller", []))
        self._resources = self._translate(interface_data.get("resource", []))

        import_paths = interface_data.get("import", [])
        for import_path in import_paths:
            task_file = self.root_path / import_path
            if "preset/" in import_path.replace("\\", "/"):
                continue
            if not task_file.exists():
                logger.warning(f"MaaEnd 任务定义不存在：{task_file}")
                continue

            try:
                raw_data = self._read_json5(task_file)
            except Exception as e:
                logger.warning(f"读取 MaaEnd 任务定义失败 {task_file.name}: {e}")
                continue

            for option_name, option_def in raw_data.get("option", {}).items():
                self._global_option_defs[option_name] = self._translate(option_def)

            translated_data = self._translate(raw_data)
            for task in translated_data.get("task", []):
                task_name = task.get("name")
                if not task_name or self._is_internal_task(task_name):
                    continue
                self._task_cache[task_name] = task
                self._raw_data_cache[task_name] = translated_data
                logger.debug(f"加载 MaaEnd 任务：{task_name}")

        logger.success(f"MaaEnd 任务加载完成，共 {len(self._task_cache)} 个任务")

    def get_groups(self) -> list[dict[str, Any]]:
        """获取 MaaEnd 分组定义"""

        return deepcopy(self._groups)

    def get_controllers(self) -> list[dict[str, Any]]:
        """获取 MaaEnd 控制器定义"""

        return deepcopy(self._controllers)

    def get_resources(self) -> list[dict[str, Any]]:
        """获取 MaaEnd 资源定义"""

        return deepcopy(self._resources)

    def get_available_tasks(
        self, controller_name: str | None = None
    ) -> list[dict[str, Any]]:
        """获取可用任务列表"""

        tasks = []
        for task in self._task_cache.values():
            task_controllers = task.get("controller", [])
            if (
                controller_name
                and task_controllers
                and controller_name not in task_controllers
            ):
                continue
            tasks.append(
                {
                    "name": task.get("name"),
                    "entry": task.get("entry"),
                    "label": task.get("label", task.get("name")),
                    "description": task.get("description", ""),
                    "controller": task_controllers,
                    "group": task.get("group", []),
                    "option": task.get("option", []),
                }
            )
        return tasks

    def get_full_definition(self, task_name: str) -> dict[str, Any] | None:
        """获取任务完整定义"""

        task_def = self._task_cache.get(task_name)
        if not task_def:
            return None

        result = deepcopy(task_def)
        option_names = result.get("option", [])
        result["_option_definitions"] = self._collect_option_definitions(option_names)
        return result

    def get_available_tasks_with_options(
        self, controller_name: str | None = None
    ) -> list[dict[str, Any]]:
        """获取可用任务和完整 option 定义"""

        result = []
        for task in self.get_available_tasks(controller_name):
            full_def = self.get_full_definition(str(task["name"]))
            if full_def is not None:
                result.append(full_def)
        return result

    def _collect_option_definitions(self, option_names: list[str]) -> dict[str, Any]:
        """收集任务及子选项需要的 option 定义"""

        collected: dict[str, Any] = {}

        def collect(option_name: str) -> None:
            if option_name in collected:
                return
            option_def = self._global_option_defs.get(option_name)
            if option_def is None:
                logger.warning(f"MaaEnd option 定义缺失：{option_name}")
                return

            collected[option_name] = deepcopy(option_def)
            for case_item in option_def.get("cases", []):
                for sub_option_name in case_item.get("option", []):
                    collect(sub_option_name)

        for option_name in option_names:
            collect(option_name)

        return collected
