from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MxuTask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    task_name: str = Field(alias="taskName")
    enabled: bool = True
    option_values: dict[str, Any] = Field(default_factory=dict, alias="optionValues")


class MxuInstance(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str = ""
    controller_name: str = Field(default="", alias="controllerName")
    resource_name: str = Field(default="", alias="resourceName")
    tasks: list[MxuTask] = Field(default_factory=list)


class MxuConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    instances: list[MxuInstance] = Field(default_factory=list)
    last_active_instance_id: str = Field(default="", alias="lastActiveInstanceId")


class MxuInstanceSummary(BaseModel):
    id: str
    name: str
    controller: str
    resource: str
    task_count: int
    enabled_task_count: int


class MxuImportPreview(BaseModel):
    config_path: str
    selected_instance_id: str
    instances: list[MxuInstanceSummary]
    controller: str
    resource: str
    snapshot: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
