from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .service import MxuImportError, MxuImportService

if TYPE_CHECKING:
    from auto_mas_core import PluginContext


DEFAULT_INSTANCE = {
    "name": "MXU 配置导入",
    "enabled": True,
    "config": {},
}

schema = {
    "__no_plugin_config__": {
        "type": "boolean",
        "default": True,
        "hidden": True,
        "configurable": False,
        "title": "No plugin-level configuration",
    },
}


class Plugin:
    provides = ["mxu.import.v1"]
    needs = ["maafw.interface.v1"]

    def __init__(self, ctx: "PluginContext") -> None:
        self.ctx = ctx
        self.service: MxuImportService | None = None

    async def on_start(self) -> None:
        interface_service = self.ctx.get("maafw.interface.v1")
        self.service = MxuImportService(interface_service)
        self.ctx.set("mxu.import.v1", self.service)
        self.ctx.server.http("/mxu/import/status", self._status, methods=["GET"])
        self.ctx.server.http("/mxu/import/preview", self._preview, methods=["POST"])
        self.ctx.logger.info("mxu.import.v1 ready")

    async def on_stop(self, reason: str) -> None:
        self.ctx.logger.info(f"mxu.import.v1 stopped, reason={reason}")

    def _status(self) -> dict[str, Any]:
        return {
            "code": 200,
            "status": "success",
            "data": {"available": self.service is not None},
        }

    def _preview(self, request: Any) -> dict[str, Any]:
        if self.service is None:
            raise RuntimeError("MXU 导入服务尚未就绪")
        payload = request.json if isinstance(request.json, dict) else {}
        project_path = str(payload.get("projectPath") or "").strip()
        if not project_path:
            return {"code": 400, "status": "error", "message": "MaaEnd 项目目录不能为空"}
        try:
            result = self.service.preview(
                project_path,
                config_path=payload.get("configPath"),
                instance_id=payload.get("instanceId"),
            )
        except MxuImportError as exc:
            return {"code": 400, "status": "error", "message": str(exc)}
        return {
            "code": 200,
            "status": "success",
            "message": "MXU 配置解析成功",
            "data": result.model_dump(mode="json", by_alias=True),
        }
