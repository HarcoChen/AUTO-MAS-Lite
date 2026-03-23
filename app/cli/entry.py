from __future__ import annotations

import argparse
import sys
from typing import Any

from .client import ApiClient, CliError
from .lifecycle import BackendLifecycle
from .output import print_json, print_kv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-mas-cli", description="AUTO-MAS CLI")
    parser.add_argument("--api-url", default="http://127.0.0.1:36163")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--no-auto-start", action="store_true")

    subparsers = parser.add_subparsers(dest="group", required=True)

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
    args = parser.parse_args(argv)

    client = ApiClient(base_url=args.api_url)
    lifecycle = BackendLifecycle(client=client)

    try:
        if not args.no_auto_start:
            lifecycle.ensure_ready()
        _dispatch(args, client)
        return 0
    except CliError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    finally:
        lifecycle.close_if_started()


def _dispatch(args: argparse.Namespace, client: ApiClient) -> None:
    if args.group == "queue" and args.queue_cmd == "list":
        result = client.post("/api/queue/get", {"queueId": None})
        if args.json_output:
            print_json(result)
            return
        rows = _format_queue_rows(result)
        if not rows:
            print("无队列数据")
            return
        print("queueId\tname")
        for row in rows:
            print(row)
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

