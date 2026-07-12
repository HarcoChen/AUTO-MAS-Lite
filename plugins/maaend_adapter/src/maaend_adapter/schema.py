from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.plugins.fields import PluginField


class PluginConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class Config(PluginConfig):
    """Plugin instance config entrypoint."""


class MaaEndInfoConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Name: str = PluginField(
        default="新 MaaEnd 脚本",
        title="脚本名称",
        json_schema_extra={"size": "large"},
    )
    ProjectLabel: str = PluginField(
        default="MaaEnd",
        title="项目标签",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Path: str = PluginField(
        default="",
        title="MaaEnd 项目目录",
        placeholder="请选择包含 interface.json 的 MaaEnd MaaFW 项目目录",
        ui_type="path",
        path_kind="folder",
        required=True,
        json_schema_extra={"size": "large"},
    )
    Controller: str = PluginField(
        default="",
        title="Controller",
        help="留空时按 interface 与设备配置自动选择。",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Resource: str = PluginField(
        default="",
        title="Resource",
        help="留空时选择匹配 controller 的第一个 resource。",
        hidden=True,
        json_schema_extra={"size": "half"},
    )


class MaaEndEmulatorConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Id: str = PluginField(
        default="-",
        title="模拟器",
        ui_type="select",
        options_provider={"source": "emulator_options"},
        json_schema_extra={
            "size": "half",
            "visible_when": {"field": "Game.ControllerType", "equals": "Adb"},
        },
    )
    Index: str = PluginField(
        default="-",
        title="模拟器实例",
        ui_type="select",
        options_provider={
            "source": "emulator_device_options",
            "selected_field": "Emulator.Id",
        },
        json_schema_extra={
            "size": "half",
            "visible_when": {"field": "Game.ControllerType", "equals": "Adb"},
        },
    )


class MaaEndDeviceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    AdbPath: str = PluginField(
        default="",
        title="ADB 路径",
        ui_type="path",
        path_kind="file",
        hidden=True,
        json_schema_extra={"size": "large"},
    )
    AdbAddress: str = PluginField(
        default="",
        title="ADB 地址",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    AdbScreencapMethods: int = PluginField(
        default=-57,
        title="ADB 截图方法",
        min=-999,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    AdbInputMethods: int = PluginField(
        default=-1,
        title="ADB 输入方法",
        min=-999,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    HWnd: int = PluginField(
        default=0,
        title="Win32 窗口句柄",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Win32ScreencapMethod: int = PluginField(
        default=0,
        title="Win32 截图方法",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Win32MouseMethod: int = PluginField(
        default=0,
        title="Win32 鼠标方法",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Win32KeyboardMethod: int = PluginField(
        default=0,
        title="Win32 键盘方法",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    GamepadType: int = PluginField(
        default=0,
        title="Gamepad 类型",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    PlayCoverAddress: str = PluginField(
        default="",
        title="PlayCover 地址",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    PlayCoverUuid: str = PluginField(
        default="",
        title="PlayCover UUID",
        hidden=True,
        json_schema_extra={"size": "half"},
    )


class MaaEndGameConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    ControllerType: Literal["Win32", "Adb"] = PluginField(
        default="Win32",
        title="控制器",
        option_labels={"Win32": "Win32 抢矿", "Adb": "ADB 模拟器"},
        json_schema_extra={"size": "half"},
    )
    Path: str = PluginField(
        default="",
        title="终末地客户端路径",
        placeholder="请选择 Endfield.exe",
        ui_type="path",
        path_kind="file",
        json_schema_extra={
            "size": "large",
            "visible_when": {"field": "Game.ControllerType", "equals": "Win32"},
        },
    )
    Arguments: str = PluginField(
        default="",
        title="游戏启动参数",
        json_schema_extra={
            "size": "large",
            "visible_when": {"field": "Game.ControllerType", "equals": "Win32"},
        },
    )
    WaitTime: int = PluginField(
        default=60,
        title="游戏启动等待时间",
        min=60,
        max=9999,
        json_schema_extra={
            "size": "half",
            "visible_when": {"field": "Game.ControllerType", "equals": "Win32"},
        },
    )
    CloseOnFinish: bool = PluginField(
        default=True,
        title="任务结束后关闭游戏",
        json_schema_extra={"size": "half"},
    )


class MaaEndUpdateConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    IfAutoUpdate: bool = PluginField(default=True, title="运行前自动更新")
    Source: Literal["MirrorChyan"] = PluginField(
        default="MirrorChyan",
        title="更新源",
    )
    Channel: Literal["", "stable", "beta"] = PluginField(
        default="",
        title="更新渠道",
        option_labels={"": "使用全局设置", "stable": "stable", "beta": "beta"},
    )
    MirrorChyanCDK: str = PluginField(
        default="",
        title="Mirror 酱 CDK",
        sensitive=True,
        json_schema_extra={"size": "large"},
    )


class MaaEndRunConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    ProxyTimesLimit: int = PluginField(
        default=0,
        title="每日代理次数限制",
        min=0,
        max=9999,
        json_schema_extra={"size": "half"},
    )
    RunTimesLimit: int = PluginField(
        default=1,
        title="失败重试次数",
        min=1,
        max=9999,
        json_schema_extra={"size": "half"},
    )
    RunTimeLimit: int = PluginField(
        default=30,
        title="单次运行超时",
        min=1,
        max=9999,
        json_schema_extra={"size": "half"},
    )
    DailyOnceTasks: str = PluginField(
        default="[]",
        title="每日仅完成一次的任务",
        ui_type="json",
        json_type="array",
        hidden=True,
        json_schema_extra={"size": "large"},
    )
    WeeklyOnceTasks: str = PluginField(
        default="[]",
        title="每周仅完成一次的任务",
        ui_type="json",
        json_type="array",
        hidden=True,
        json_schema_extra={"size": "large"},
    )
    MonthlyOnceTasks: str = PluginField(
        default="[]",
        title="每月仅完成一次的任务",
        ui_type="json",
        json_type="array",
        hidden=True,
        json_schema_extra={"size": "large"},
    )


class MaaEndConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Info: MaaEndInfoConfig = PluginField(default_factory=MaaEndInfoConfig, title="基础信息")
    Emulator: MaaEndEmulatorConfig = PluginField(
        default_factory=MaaEndEmulatorConfig,
        title="模拟器配置",
    )
    Device: MaaEndDeviceConfig = PluginField(
        default_factory=MaaEndDeviceConfig,
        title="设备配置",
    )
    Game: MaaEndGameConfig = PluginField(default_factory=MaaEndGameConfig, title="游戏配置")
    Update: MaaEndUpdateConfig = PluginField(
        default_factory=MaaEndUpdateConfig,
        title="项目更新",
    )
    Run: MaaEndRunConfig = PluginField(default_factory=MaaEndRunConfig, title="运行配置")


class MaaEndUserInfoConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Name: str = PluginField(
        default="新用户",
        title="用户名称",
        validator="username",
        json_schema_extra={"size": "large"},
    )
    Status: bool = PluginField(default=True, title="启用用户", json_schema_extra={"size": "half"})
    RemainedDay: int = PluginField(
        default=-1,
        title="剩余天数",
        min=-1,
        max=9999,
        json_schema_extra={"size": "half"},
    )
    IfScriptBeforeTask: bool = PluginField(
        default=False,
        title="启用前置脚本",
        json_schema_extra={"size": "1/4"},
    )
    ScriptBeforeTask: str = PluginField(
        default="",
        title="前置脚本",
        ui_type="path",
        path_kind="file",
        json_schema_extra={"size": "3/4"},
    )
    IfScriptAfterTask: bool = PluginField(
        default=False,
        title="启用后置脚本",
        json_schema_extra={"size": "1/4"},
    )
    ScriptAfterTask: str = PluginField(
        default="",
        title="后置脚本",
        ui_type="path",
        path_kind="file",
        json_schema_extra={"size": "3/4"},
    )
    Notes: str = PluginField(
        default="无",
        title="备注",
        format="textarea",
        rows=3,
        json_schema_extra={"size": "large"},
    )
    Tag: str = PluginField(
        default="[ ]",
        title="标签",
        readonly=True,
        hidden=True,
        configurable=False,
    )
    Account: str = PluginField(default="", title="账号", json_schema_extra={"size": "half"})
    Password: str = PluginField(
        default="",
        title="密码",
        format="password",
        sensitive=True,
        json_schema_extra={"size": "half"},
    )
    Controller: str = PluginField(
        default="",
        title="Controller",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    Resource: str = PluginField(
        default="",
        title="Resource",
        hidden=True,
        json_schema_extra={"size": "half"},
    )


class MaaEndUserTaskConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    SelectedPreset: str = PluginField(
        default="",
        title="任务预设",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    TaskSnapshot: str = PluginField(
        default="{}",
        title="任务快照",
        ui_type="json",
        json_type="object",
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "large"},
    )


class MaaEndUserDeviceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    AdbAddress: str = PluginField(
        default="",
        title="ADB 地址",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    HWnd: int = PluginField(
        default=0,
        title="Win32 窗口句柄",
        min=0,
        max=999999999999,
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    PlayCoverAddress: str = PluginField(
        default="",
        title="PlayCover 地址",
        hidden=True,
        json_schema_extra={"size": "half"},
    )
    PlayCoverUuid: str = PluginField(
        default="",
        title="PlayCover UUID",
        hidden=True,
        json_schema_extra={"size": "half"},
    )


class MaaEndUserDataConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    LastProxyDate: str = PluginField(
        default="2000-01-01",
        title="上次代理日期",
        readonly=True,
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "half"},
    )
    ProxyTimes: int = PluginField(
        default=0,
        title="代理次数",
        min=0,
        max=9999,
        readonly=True,
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "half"},
    )
    IfPassCheck: bool = PluginField(
        default=True,
        title="是否通过检查",
        readonly=True,
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "half"},
    )
    LastProxyStatus: str = PluginField(
        default="未知",
        title="上次运行状态",
        readonly=True,
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "half"},
    )
    PeriodTaskRecords: str = PluginField(
        default="{}",
        title="周期任务完成记录",
        ui_type="json",
        json_type="object",
        readonly=True,
        hidden=True,
        include_in_schema=False,
        json_schema_extra={"size": "large"},
    )


class MaaEndUserNotifyConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Enabled: bool = PluginField(default=False, title="启用单独通知")
    IfSendStatistic: bool = PluginField(default=False, title="发送统计")
    IfSendMail: bool = PluginField(default=False, title="发送邮件")
    ToAddress: str = PluginField(default="", title="收件地址")
    IfServerChan: bool = PluginField(default=False, title="启用 ServerChan")
    ServerChanKey: str = PluginField(default="", title="ServerChan Key", sensitive=True)


class MaaEndUserConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    Info: MaaEndUserInfoConfig = PluginField(
        default_factory=MaaEndUserInfoConfig,
        title="基础信息",
    )
    Task: MaaEndUserTaskConfig = PluginField(
        default_factory=MaaEndUserTaskConfig,
        title="任务配置",
    )
    Device: MaaEndUserDeviceConfig = PluginField(
        default_factory=MaaEndUserDeviceConfig,
        title="设备覆盖",
    )
    Data: MaaEndUserDataConfig = PluginField(
        default_factory=MaaEndUserDataConfig,
        title="用户数据",
    )
    Notify: MaaEndUserNotifyConfig = PluginField(
        default_factory=MaaEndUserNotifyConfig,
        title="单独通知",
    )
