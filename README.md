# ReviewSubagent

A small, dependency-free Python todo-list CLI. Use it as a sample project for
the reviewer agent in `.claude/agents/reviewer.md`.

## Requirements

Python 3.10 or newer.

## Usage

```powershell
python todo_app.py --data-file tasks.json add "Write tests"
python todo_app.py --data-file tasks.json list
python todo_app.py --data-file tasks.json done 1
```

The `--data-file` option is optional. By default, tasks are saved to
`~/.todo-cli/tasks.json`.

## Tests

```powershell
python -m unittest
```
