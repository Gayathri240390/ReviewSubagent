import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from todo_app import add_task, complete_task, load_tasks, main


class TodoAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "nested" / "tasks.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_and_complete_tasks(self) -> None:
        first = add_task(self.data_file, "  Write tests  ")
        second = add_task(self.data_file, "Review changes")

        self.assertEqual(first["id"], 1)
        self.assertEqual(first["title"], "Write tests")
        self.assertEqual(second["id"], 2)

        completed = complete_task(self.data_file, first["id"])
        self.assertTrue(completed["completed"])
        self.assertFalse(load_tasks(self.data_file)[1]["completed"])

    def test_reject_empty_title(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            add_task(self.data_file, "   ")

    def test_reject_unknown_task(self) -> None:
        with self.assertRaisesRegex(ValueError, "was not found"):
            complete_task(self.data_file, 42)

    def test_reject_invalid_task_file(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text(json.dumps({"not": "a task list"}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Unexpected task data"):
            load_tasks(self.data_file)

    def write_raw(self, content: str) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text(content, encoding="utf-8")

    def test_reject_malformed_json(self) -> None:
        self.write_raw("{not json")
        with self.assertRaisesRegex(ValueError, "Invalid task file"):
            load_tasks(self.data_file)

    def test_reject_boolean_id(self) -> None:
        self.write_raw(json.dumps([{"id": True, "title": "x", "completed": False}]))
        with self.assertRaisesRegex(ValueError, "Unexpected task data"):
            load_tasks(self.data_file)

    def test_reject_duplicate_ids(self) -> None:
        task = {"id": 1, "title": "x", "completed": False}
        self.write_raw(json.dumps([task, task]))
        with self.assertRaisesRegex(ValueError, "Duplicate task IDs"):
            load_tasks(self.data_file)

    def test_reject_completing_twice(self) -> None:
        task = add_task(self.data_file, "Once")
        complete_task(self.data_file, task["id"])
        with self.assertRaisesRegex(ValueError, "already complete"):
            complete_task(self.data_file, task["id"])

    def test_save_leaves_no_temp_file(self) -> None:
        add_task(self.data_file, "Clean up")
        self.assertEqual(
            [p.name for p in self.data_file.parent.iterdir()], ["tasks.json"]
        )

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--data-file", str(self.data_file), *args])
        return code, out.getvalue(), err.getvalue()

    def test_cli_add_list_done(self) -> None:
        self.assertEqual(self.run_cli("list"), (0, "No tasks yet.\n", ""))
        self.assertEqual(self.run_cli("add", "Ship it")[0], 0)
        self.assertEqual(self.run_cli("done", "1")[0], 0)
        code, out, _ = self.run_cli("list")
        self.assertEqual((code, out), (0, "[x] 1: Ship it\n"))

    def test_cli_reports_errors(self) -> None:
        code, out, err = self.run_cli("done", "99")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Task 99 was not found.", err)


if __name__ == "__main__":
    unittest.main()
