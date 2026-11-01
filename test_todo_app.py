import json
import tempfile
import unittest
from pathlib import Path

from todo_app import add_task, complete_task, load_tasks


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


if __name__ == "__main__":
    unittest.main()
