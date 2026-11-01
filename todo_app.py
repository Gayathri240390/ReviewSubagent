"""A small JSON-backed command-line todo list."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def load_tasks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        tasks = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid task file: {path}") from error

    if not isinstance(tasks, list) or any(
        not isinstance(task, dict)
        # type() rather than isinstance(): bool is a subclass of int,
        # so isinstance(True, int) would wrongly accept "id": true.
        or type(task.get("id")) is not int
        or not isinstance(task.get("title"), str)
        or not isinstance(task.get("completed"), bool)
        for task in tasks
    ):
        raise ValueError(f"Unexpected task data in: {path}")

    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate task IDs in: {path}")
    return tasks


def save_tasks(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file, then swap it in, so a crash mid-write
    # never leaves a half-written tasks file behind.
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def add_task(path: Path, title: str) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty.")

    tasks = load_tasks(path)
    task = {
        "id": max((item["id"] for item in tasks), default=0) + 1,
        "title": title,
        "completed": False,
    }
    tasks.append(task)
    save_tasks(path, tasks)
    return task


def complete_task(path: Path, task_id: int) -> dict[str, Any]:
    tasks = load_tasks(path)
    for task in tasks:
        if task["id"] == task_id:
            if task["completed"]:
                raise ValueError(f"Task {task_id} is already complete.")
            task["completed"] = True
            save_tasks(path, tasks)
            return task
    raise ValueError(f"Task {task_id} was not found.")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a simple todo list.")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path.home() / ".todo-cli" / "tasks.json",
        help="Path to the JSON task file.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add_command = commands.add_parser("add", help="Add a task.")
    add_command.add_argument("title", help="Task description.")

    commands.add_parser("list", help="List all tasks.")

    done_command = commands.add_parser("done", help="Mark a task complete.")
    done_command.add_argument("task_id", type=int, help="Task ID.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "add":
            task = add_task(args.data_file, args.title)
            print(f"Added task {task['id']}: {task['title']}")
        elif args.command == "list":
            tasks = load_tasks(args.data_file)
            if not tasks:
                print("No tasks yet.")
            for task in tasks:
                status = "x" if task["completed"] else " "
                print(f"[{status}] {task['id']}: {task['title']}")
        else:
            task = complete_task(args.data_file, args.task_id)
            print(f"Completed task {task['id']}: {task['title']}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
