#!/usr/bin/env python3
"""Interactive AI-first CLI for architecture authoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from diagram_ops import (
    RAW_DIR,
    apply_prompt_delta,
    ensure_dirs,
    generate_new,
    now_name,
    plan_prompt_delta,
    render_file,
    summarize,
    startup_check,
    understand_diagram,
    validate_path,
)
from session_state import SessionState


HELP_TEXT = """Available commands:
  :start                Run startup checks and initialize session
  :help                 Show this help message
  :new <name>           Create a new working diagram file name
  :use <file>           Switch active file (name or path)
  :status               Show active file and last run status
  :validate             Validate active file
  :render               Render active file to PNG
  :show                 Show quick diagram summary
  :understand [file]    Parse active/existing drawio and explain structure
  :redefine <request>   Build redefine plan without mutating XML
  :apply                Apply last redefine plan
  :icon <aws4|none>     Set icon mode for future updates
  :quit                 Exit interactive session

Natural language mode:
  - Type a plain sentence to create/update the active diagram.
  - First sentence creates a diagram automatically.
  - Next sentences apply incremental deltas (add/remove/connect).
"""


def _resolve_user_file(value: str) -> Path:
    p = Path(value)
    if p.suffix != ".drawio":
        p = p.with_suffix(".drawio")
    if not p.is_absolute():
        p = RAW_DIR / p.name
    return p


def _run_validate_and_render(state: SessionState) -> None:
    if state.active_file is None:
        print("No active file.")
        return

    ok, msg = validate_path(state.active_file)
    state.last_validation_ok = ok
    state.last_validation_msg = msg
    print(msg)
    if not ok:
        return

    rok, rmsg, png = render_file(state.active_file)
    print(rmsg)
    if rok:
        state.last_rendered_png = png


def _run_startup(state: SessionState) -> None:
    ok, lines = startup_check()
    print("Startup checks:")
    for line in lines:
        print(f"- {line}")
    if ok:
        print("System ready. Describe your architecture in natural language.")
    else:
        print("Startup checks failed. Fix the errors above, then run :start again.")

    if state.active_file:
        print(f"Active file: {state.active_file}")
    else:
        print("No active file yet. Use :new <name> or type your first prompt.")


def _print_understanding(path: Path) -> None:
    details = understand_diagram(path)
    print(f"File: {details['file']}")
    print(f"Format: {details['format']}")
    print(f"Services: {details['services_count']} | Edges: {details['edges_count']}")

    boundaries = details.get("boundaries", [])
    boundary_items = boundaries if isinstance(boundaries, list) else []
    if boundary_items:
        print("Boundaries:")
        for item in boundary_items:
            print(f"- {item}")

    recognized = details.get("recognized_services", [])
    recognized_items = recognized if isinstance(recognized, list) else []
    if recognized_items:
        print("Recognized services:")
        for item in recognized_items:
            print(f"- {item}")

    unknown = details.get("unknown_components", [])
    unknown_items = unknown if isinstance(unknown, list) else []
    if unknown_items:
        print("Unknown components:")
        for item in unknown_items:
            print(f"- {item}")

    flows = details.get("inferred_flows", [])
    flow_items = flows if isinstance(flows, list) else []
    if flow_items:
        print("Inferred flows:")
        for flow in flow_items:
            print(f"- {flow}")


def _plan_redefine(state: SessionState, prompt: str) -> None:
    if state.active_file is None or not state.active_file.exists():
        print("No active file. Use :new/:use first or create one with a prompt.")
        return
    plan = plan_prompt_delta(state.active_file, prompt, icon_set=state.icon_set)
    state.pending_redefine_prompt = prompt
    state.pending_redefine_plan = plan
    print("Redefine plan:")
    for change in plan:
        print(f"- {change}")
    print("Run :apply to execute this plan.")


def _apply_pending_redefine(state: SessionState) -> None:
    if not state.pending_redefine_prompt:
        print("No pending redefine plan. Use :redefine <request> first.")
        return
    if state.active_file is None:
        print("No active file.")
        return

    changes = apply_prompt_delta(state.active_file, state.pending_redefine_prompt, icon_set=state.icon_set)
    print("Applied changes:")
    for change in changes:
        print(f"- {change}")
    state.pending_redefine_prompt = None
    state.pending_redefine_plan = []
    _run_validate_and_render(state)


def _create_from_prompt(state: SessionState, prompt: str, preset_name: str | None = None) -> None:
    name = preset_name or (state.active_file.stem if state.active_file else now_name("arch"))
    path = generate_new(name=name, prompt=prompt, icon_set=state.icon_set)
    state.active_file = path
    print(f"Generated: {path}")
    _run_validate_and_render(state)


def _update_from_prompt(state: SessionState, prompt: str) -> None:
    if state.active_file is None:
        _create_from_prompt(state, prompt)
        return
    changes = apply_prompt_delta(state.active_file, prompt, icon_set=state.icon_set)
    print("Changes:")
    for change in changes:
        print(f"- {change}")
    state.pending_redefine_prompt = None
    state.pending_redefine_plan = []
    _run_validate_and_render(state)


def run_repl(initial_file: Path | None = None, auto_start: bool = False) -> int:
    ensure_dirs()
    state = SessionState(active_file=initial_file if initial_file and initial_file.exists() else None)

    print("Archsmith interactive mode")
    print("Type :start to initialize the session, or :help for commands.")
    if state.active_file:
        print(f"Active file: {state.active_file}")

    if auto_start:
        _run_startup(state)

    while True:
        try:
            line = input("archsmith> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye")
            return 0

        if not line:
            continue
        state.history.append(line)

        if line.startswith(":"):
            parts = line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == ":start":
                _run_startup(state)
            elif cmd == ":help":
                print(HELP_TEXT)
            elif cmd == ":quit":
                print("Bye")
                return 0
            elif cmd == ":new":
                name = arg or now_name("arch")
                state.active_file = _resolve_user_file(name)
                state.pending_redefine_prompt = None
                state.pending_redefine_plan = []
                print(f"Active file set to: {state.active_file}")
                print("Now describe your architecture in natural language.")
            elif cmd == ":use":
                if not arg:
                    print("Usage: :use <file>")
                    continue
                path = _resolve_user_file(arg)
                if not path.exists():
                    print(f"File not found: {path}")
                    continue
                state.active_file = path
                state.pending_redefine_prompt = None
                state.pending_redefine_plan = []
                print(f"Active file: {state.active_file}")
            elif cmd == ":status":
                print(f"active_file={state.active_file}")
                print(f"icon_set={state.icon_set}")
                print(f"last_validation_ok={state.last_validation_ok}")
                if state.last_validation_msg:
                    print(state.last_validation_msg)
                if state.last_rendered_png:
                    print(f"last_png={state.last_rendered_png}")
                if state.pending_redefine_prompt:
                    print("pending_redefine=yes")
            elif cmd == ":validate":
                if state.active_file is None:
                    print("No active file.")
                    continue
                ok, msg = validate_path(state.active_file)
                state.last_validation_ok = ok
                state.last_validation_msg = msg
                print(msg)
            elif cmd == ":render":
                if state.active_file is None:
                    print("No active file.")
                    continue
                _run_validate_and_render(state)
            elif cmd == ":show":
                if state.active_file is None:
                    print("No active file.")
                    continue
                print(summarize(state.active_file))
            elif cmd == ":understand":
                target = state.active_file
                if arg:
                    target = _resolve_user_file(arg)
                if target is None:
                    print("No active file.")
                    continue
                if not target.exists():
                    print(f"File not found: {target}")
                    continue
                _print_understanding(target)
            elif cmd == ":redefine":
                if not arg:
                    print("Usage: :redefine <request>")
                    continue
                _plan_redefine(state, arg)
            elif cmd == ":apply":
                _apply_pending_redefine(state)
            elif cmd == ":icon":
                if arg not in {"aws4", "none"}:
                    print("Usage: :icon <aws4|none>")
                    continue
                state.icon_set = arg
                print(f"icon_set={state.icon_set}")
            else:
                print("Unknown command. Type :help")
            continue

        if state.active_file is None or not state.active_file.exists():
            _create_from_prompt(state, line, preset_name=state.active_file.stem if state.active_file else None)
        else:
            _update_from_prompt(state, line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Archsmith interactive CLI")
    parser.add_argument("--file", help="Optional existing .drawio file to use")
    parser.add_argument("--start", action="store_true", help="Run startup checks at launch")
    args = parser.parse_args()

    initial = _resolve_user_file(args.file) if args.file else None
    return run_repl(initial, auto_start=args.start)


if __name__ == "__main__":
    raise SystemExit(main())
