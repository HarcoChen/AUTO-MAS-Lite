from __future__ import annotations

import argparse
import sys
from typing import Any

from .client import ApiClient, CliError
from .lifecycle import BackendLifecycle
from .output import print_json, print_kv, print_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-mas-cli", description="AUTO-MAS CLI")
    parser.add_argument("--api-url", default="http://127.0.0.1:36163")
    parser.add_argument("--app-root", default=None)
    parser.add_argument("--python-exe", default=None)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--no-auto-start", action="store_true")
    parser.add_argument("--keep-backend", action="store_true")

    subparsers = parser.add_subparsers(dest="group", required=True)

    backend_parser = subparsers.add_parser("backend", help="后端控制命令")
    backend_subparsers = backend_parser.add_subparsers(
        dest="backend_cmd", required=True
    )
    backend_subparsers.add_parser("status", help="查看后端状态")
    backend_subparsers.add_parser("start", help="启动后端")
    backend_subparsers.add_parser("stop", help="停止后端")

    queue_parser = subparsers.add_parser("queue", help="队列相关命令")
    queue_subparsers = queue_parser.add_subparsers(dest="queue_cmd", required=True)
    queue_subparsers.add_parser("list", help="列出队列")

    task_parser = subparsers.add_parser("task", help="任务相关命令")
    task_subparsers = task_parser.add_subparsers(dest="task_cmd", required=True)

    start_parser = task_subparsers.add_parser("start", help="启动任务")
    start_parser.add_argument("--mode", required=True, choices=["AutoProxy", "ManualReview", "ScriptConfig"])
    start_parser.add_argument("--task-id", required=True)

    stop_parser = task_subparsers.add_parser("stop", help="停止任务")
    stop_parser.add_argument("--task-id", required=True)

    return parser


def _format_queue_rows(payload: dict[str, Any]) -> list[str]:
    index = payload.get("index", [])
    data = payload.get("data", {})
    rows: list[str] = []
    for item in index:
        uid = item.get("uid", "")
        queue = data.get(uid, {})
        name = queue.get("Info", {}).get("Name", "")
        rows.append(f"{uid}\t{name}")
    return rows


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(_normalize_global_args(argv or []))

    client = ApiClient(base_url=args.api_url)
    lifecycle = BackendLifecycle(
        client=client,
        app_root=args.app_root,
        python_executable=args.python_exe,
        keep_backend=args.keep_backend,
    )

    try:
        if _should_keep_backend(args):
            lifecycle.keep_backend = True

        if _should_auto_start_backend(args):
            if args.no_auto_start:
                if not lifecycle.status()["ready"]:
                    raise CliError("后端未运行，请先启动后端或移除 --no-auto-start")
            else:
                lifecycle.ensure_ready()

        if args.group == "backend" and args.backend_cmd == "start":
            lifecycle.start_backend()
        elif args.group == "backend" and args.backend_cmd == "stop":
            if not lifecycle.status()["ready"]:
                raise CliError("后端未运行，无需停止")
            lifecycle.stop_backend()
        elif args.group == "task" and args.task_cmd == "stop":
            if not lifecycle.status()["ready"]:
                raise CliError("后端未运行，无法停止任务")

        _dispatch(args, client, lifecycle)
        return 0
    except CliError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    finally:
        lifecycle.close_if_started()


def _should_auto_start_backend(args: argparse.Namespace) -> bool:
    return (
        (args.group == "queue" and args.queue_cmd == "list")
        or (args.group == "task" and args.task_cmd == "start")
    )


def _should_keep_backend(args: argparse.Namespace) -> bool:
    return (
        args.keep_backend
        or (args.group == "backend" and args.backend_cmd == "start")
        or (args.group == "task" and args.task_cmd == "start")
    )


def _normalize_global_args(argv: list[str]) -> list[str]:
    options_with_values = {"--api-url", "--app-root", "--python-exe"}
    flag_options = {"--json", "--no-auto-start", "--keep-backend"}
    global_tokens: list[str] = []
    remaining_tokens: list[str] = []

    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token in options_with_values:
            global_tokens.append(token)
            if idx + 1 < len(argv):
                global_tokens.append(argv[idx + 1])
                idx += 2
                continue
        elif token in flag_options:
            global_tokens.append(token)
            idx += 1
            continue

        remaining_tokens.append(token)
        idx += 1

    return [*global_tokens, *remaining_tokens]


def _dispatch(
    args: argparse.Namespace, client: ApiClient, lifecycle: BackendLifecycle
) -> None:
    if args.group == "backend" and args.backend_cmd == "status":
        result = lifecycle.status()
        if args.json_output:
            print_json(result)
            return
        print_kv("backend", "running" if result["ready"] else "stopped")
        print_kv("apiUrl", str(result["apiUrl"]))
        print_kv("appRoot", str(result["appRoot"]))
        print_kv("python", str(result["pythonExecutable"]))
        return

    if args.group == "backend" and args.backend_cmd == "start":
        result = lifecycle.status()
        if args.json_output:
            print_json(result)
            return
        print("后端已启动")
        print_kv("apiUrl", str(result["apiUrl"]))
        return

    if args.group == "backend" and args.backend_cmd == "stop":
        if args.json_output:
            print_json({"success": True, "message": "后端停止请求已发送"})
            return
        print("后端停止请求已发送")
        return

    if args.group == "queue" and args.queue_cmd == "list":
        result = client.post("/api/queue/get", {"queueId": None})
        if args.json_output:
            print_json(result)
            return
        rows = _format_queue_rows(result)
        if not rows:
            print("无队列数据")
            return
        print_rows("queueId\tname", rows)
        return

    if args.group == "task" and args.task_cmd == "start":
        result = client.post(
            "/api/dispatch/start",
            {"mode": args.mode, "taskId": args.task_id},
        )
        if args.json_output:
            print_json(result)
            return
        print_kv("taskId", str(result.get("taskId", "")))
        return

    if args.group == "task" and args.task_cmd == "stop":
        result = client.post("/api/dispatch/stop", {"taskId": args.task_id})
        if args.json_output:
            print_json(result)
            return
        print(result.get("message", "任务停止请求已发送"))
        return

    raise CliError("未知命令")
