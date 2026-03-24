# CLI 分发级别计划

## L0 开发态 CLI
- 入口：`python -m app.cli`
- 目标：开发者在仓库内直接调用
- 前提：手工准备 Python、依赖、仓库路径
- 当前状态：已具备基本能力

## L1 便携分发
- 产物：独立 `auto-mas-cli.exe` 或带私有 Python 运行时的目录包
- 要求：
  - CLI 可通过 `AUTO_MAS_ROOT` 或同目录结构定位 `main.py`
  - CLI 可通过 `AUTO_MAS_PYTHON` 或内置运行时启动后端
  - 增加 `backend start/stop/status`
  - 默认日志和错误输出可用于排障
- 系统集成：
  - 不改注册表
  - 用户手工把目录加入 `PATH`

## L2 安装器分发
- 产物：Windows 安装器
- 要求：
  - 固定安装目录，例如 `%LocalAppData%\\AUTO-MAS\\cli`
  - 安装时自动写入用户级 `PATH`
  - 卸载时自动清理 `PATH`
  - 安装器可选创建开始菜单或桌面快捷方式
- 系统集成：
  - `PATH` 是主方案
  - `App Paths` 注册表是可选增强，不是必需项

## L3 产品级分发
- 产物：带升级能力和服务模式的 CLI 产品
- 要求：
  - 支持 `repo mode`、`bundled mode`、`service mode`
  - 后端与 CLI 生命周期分离
  - 支持版本查询、升级、回滚
  - 支持稳定的数据目录、日志目录、配置目录
  - 支持签名、校验和、CI 自动构建
- 系统集成：
  - Windows 安装器
  - 用户级 `PATH`
  - 可选自更新与服务注册

## 推荐顺序
1. 先完成 L1，把 CLI 从“源码可跑”变成“便携可用”。
2. 再做 L2，把安装目录和 `PATH` 集成补齐。
3. 最后再做 L3，处理升级、服务模式和签名。

## 边界
- `PATH` 集成属于安装层，不应该塞进后端。
- 后端只负责现有 API 和调度，不负责 CLI 自身安装。
- CLI 分发逻辑应该留在 `app/cli` 或独立打包脚本，不侵入 `app/core`。
