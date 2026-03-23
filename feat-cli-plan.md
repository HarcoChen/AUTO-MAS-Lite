# feat/cli V1 实施计划（调度控制，HTTP 复用，Win 优先）

## 1. Summary
1. 从 `dev` 签出 `feat/cli`，采用独立入口（`python -m app.cli`），不改现有 Electron 启动链。
2. V1 命令范围：`queue list`、`task start`、`task stop`。
3. 后端生命周期：CLI 默认“自动拉起并回收”；若命令开始前后端已在运行，则不回收。
4. 平台范围：Windows 优先，仅保证 Win 可用；Linux 兼容放到后续迭代。
5. 按 `mas-skills` 选用子技能：
   - `mas-module-boundary`：CLI 与后端职责分层，避免直连核心调度对象。
   - `mas-function-design`：命令处理器、生命周期管理、退出码统一。
   - `mas-api-contract`：复用现有 HTTP 契约，保持兼容优先。

## 2. 关键实现变更
1. CLI 模块边界（新增 `app/cli`）
   - `entry`：参数解析与命令分发（`argparse`，不新增第三方依赖）。
   - `client`：HTTP 调用封装（复用现有 `OutBase` 风格错误处理）。
   - `watcher`：暂不实现（V1 不接入 WebSocket）。
   - `lifecycle`：后端探活、自动拉起、回收关闭。
   - `elevation`：Windows 非管理员时 UAC 提权重入（整条 CLI 命令在提权后继续执行）。

2. 命令行为定义（决策完成）
   - `queue list`：调用 `/api/queue/get`（`queueId=null`），默认文本表格，`--json` 输出原始结构化结果。
   - `task start --mode --task-id`：调用 `/api/dispatch/start`，输出 `taskId`。
   - `task stop --task-id`：调用 `/api/dispatch/stop`，支持 `ALL`。

3. UAC 与自动拉起回收
   - 先探活（`/api/info/version`）。
   - 后端不可用时：尝试启动 `main.py` 并等待就绪。
   - 若权限不足：触发 UAC，提权后重入同一命令（参数透传 + 临时结果文件回传退出码/输出）。
   - 命令结束后：仅当后端由本次 CLI 拉起时，调用 `/api/core/close` 并等待退出。

## 3. 测试与验收
1. 启动态：后端已运行时，CLI 不重复拉起，命令可直接成功。
2. 自动拉起：后端未运行时，CLI 自动拉起并执行命令，结束后自动回收。
3. UAC：非管理员终端执行命令可触发提权并完成（返回码正确）。
4. 调度闭环：`task start -> task stop` 全链路可用。
5. 输出契约：默认文本可读，`--json` 稳定可解析；失败场景有明确错误码与错误信息。

## 4. 分支与提交切分
1. `git switch dev && git pull && git switch -c feat/cli`
2. Commit 1：CLI 骨架（entry/client/output/lifecycle 基础）。
3. Commit 2：命令退出码统一 + 自动拉起回收稳定性处理。
4. Commit 3：UAC 提权重入与文档（CLI 用法、限制、示例）。

## 5. Assumptions
1. V1 仅 Win 保证可用，Linux 不在本次交付范围。
2. 不改现有后端业务接口语义（V1 不新增后端接口）。
3. 不改前端/Electron 代码路径，CLI 与现有 GUI 并存。
4. `task watch` 暂存到后续迭代（届时再引入 WS 与心跳逻辑）。
5. 当前仓库无现成测试框架，V1 以可重复手工 smoke + 命令回归脚本验收。
