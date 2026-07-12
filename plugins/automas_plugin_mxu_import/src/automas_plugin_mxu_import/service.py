from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import MxuConfig, MxuImportPreview, MxuInstance, MxuInstanceSummary


class MxuImportError(ValueError):
    """MXU 配置无法定位、解析或转换。"""


class MxuImportService:
    """把 MXU 实例配置转换为 MaaFW 标准任务快照。"""

    def __init__(self, interface_service: Any) -> None:
        self.interface_service = interface_service

    def preview(
        self,
        project_path: str | Path,
        *,
        config_path: str | Path | None = None,
        instance_id: str | None = None,
    ) -> MxuImportPreview:
        project_root = Path(project_path).expanduser().resolve()
        source_path = self._resolve_config_path(project_root, config_path)
        config = self._load_config(source_path)
        instance = self._select_instance(config, instance_id)
        interface = self.interface_service.load(project_root)
        warnings = self._build_warnings(instance, interface)

        raw_snapshot = {
            "taskOrder": [task.task_name for task in instance.tasks],
            "taskChecked": {
                task.task_name: task.enabled for task in instance.tasks
            },
            "taskOptions": {
                task.task_name: task.option_values for task in instance.tasks
            },
        }
        snapshot = self.interface_service.normalize_snapshot(interface, raw_snapshot)
        snapshot_data = snapshot.model_dump(mode="json")
        warnings.extend(self._build_option_warnings(instance, snapshot_data))

        return MxuImportPreview(
            config_path=str(source_path),
            selected_instance_id=instance.id,
            instances=[self._summarize(item) for item in config.instances],
            controller=instance.controller_name,
            resource=instance.resource_name,
            snapshot=snapshot_data,
            warnings=warnings,
        )

    @staticmethod
    def _resolve_config_path(project_root: Path, config_path: str | Path | None) -> Path:
        if config_path:
            candidate = Path(config_path).expanduser()
            if not candidate.is_absolute():
                candidate = project_root / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(project_root)
            except ValueError as exc:
                raise MxuImportError("MXU 配置文件必须位于 MaaEnd 项目目录内") from exc
            if not candidate.is_file():
                raise MxuImportError(f"MXU 配置文件不存在: {candidate}")
            return candidate

        candidates = sorted((project_root / "config").glob("mxu-*.json"))
        if not candidates:
            raise MxuImportError("未在项目 config 目录找到 mxu-*.json")
        if len(candidates) > 1:
            names = "、".join(path.name for path in candidates)
            raise MxuImportError(f"找到多个 MXU 配置文件，请明确选择: {names}")
        return candidates[0].resolve()

    @staticmethod
    def _load_config(path: Path) -> MxuConfig:
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            config = MxuConfig.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise MxuImportError(f"无法读取 MXU 配置: {exc}") from exc
        if not config.instances:
            raise MxuImportError("MXU 配置中没有可导入的实例")
        return config

    @staticmethod
    def _select_instance(config: MxuConfig, instance_id: str | None) -> MxuInstance:
        requested = str(instance_id or "").strip()
        if requested:
            selected = next((item for item in config.instances if item.id == requested), None)
            if selected is None:
                raise MxuImportError(f"MXU 实例不存在: {requested}")
            return selected

        for preferred_id in ("automas", config.last_active_instance_id):
            if preferred_id:
                selected = next(
                    (item for item in config.instances if item.id == preferred_id),
                    None,
                )
                if selected is not None:
                    return selected
        if len(config.instances) == 1:
            return config.instances[0]
        return config.instances[0]

    @staticmethod
    def _build_warnings(instance: MxuInstance, interface: Any) -> list[str]:
        warnings: list[str] = []
        task_names = {task.name for task in interface.task}
        unknown_tasks = sorted(
            {task.task_name for task in instance.tasks if task.task_name not in task_names}
        )
        if unknown_tasks:
            warnings.append(f"已忽略 Interface 中不存在的任务: {'、'.join(unknown_tasks)}")

        controller_names = {controller.name for controller in interface.controller}
        if instance.controller_name and instance.controller_name not in controller_names:
            warnings.append(f"Controller 不存在: {instance.controller_name}")

        resources = {resource.name: resource for resource in interface.resource}
        resource = resources.get(instance.resource_name)
        if instance.resource_name and resource is None:
            warnings.append(f"Resource 不存在: {instance.resource_name}")
        elif resource is not None and resource.controller:
            if instance.controller_name not in resource.controller:
                warnings.append(
                    f"Resource {instance.resource_name} 不支持 Controller {instance.controller_name}"
                )
        return warnings

    @staticmethod
    def _summarize(instance: MxuInstance) -> MxuInstanceSummary:
        return MxuInstanceSummary(
            id=instance.id,
            name=instance.name or instance.id,
            controller=instance.controller_name,
            resource=instance.resource_name,
            task_count=len(instance.tasks),
            enabled_task_count=sum(task.enabled for task in instance.tasks),
        )

    @staticmethod
    def _build_option_warnings(
        instance: MxuInstance,
        snapshot: dict[str, Any],
    ) -> list[str]:
        normalized_options = snapshot.get("taskOptions", {})
        warnings: list[str] = []
        for task in instance.tasks:
            accepted = normalized_options.get(task.task_name)
            if not isinstance(accepted, dict):
                continue
            ignored = sorted(set(task.option_values) - set(accepted))
            if ignored:
                warnings.append(
                    f"任务 {task.task_name} 已忽略不存在的选项: {'、'.join(ignored)}"
                )
        return warnings
