"""Command-line entry point with explicit inputs, predictable exit codes, and safe output."""

import argparse
import json
import math
import sys
from pathlib import Path

from .core import InputError, read_text, render, within_root
from .engine import SKILLS, TEXT_SKILLS, run
from .metadata import validate_library
from .registry import verify_registry


def reject_constant(_):
    raise InputError("JSON nonfinite numbers are not supported")


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise InputError("JSON numeric overflow is not supported")
    return number


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InputError("JSON object keys must be unique")
        obj[key] = value
    return obj


def main(argv=None):
    # Reports are UTF-8 even when a Windows pipe inherits a legacy code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(
        description="Offline trust review assistance; no compliance verdicts"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List the 20 available skill helpers")
    validate = commands.add_parser(
        "validate", help="Validate this library's skill metadata and registry"
    )
    validate.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Repository root (not installed wheel)"
    )
    registry = commands.add_parser(
        "registry", help="Check registry structure; live URL requests require --live"
    )
    registry.add_argument("--registry", type=Path, default=Path("standards/registry.yaml"))
    registry.add_argument(
        "--live",
        action="store_true",
        help="Opt in to bounded official-host HTTP retrieval (no semantic verification)",
    )
    registry.add_argument("--timeout", type=float, default=5.0)
    registry.add_argument(
        "--output", type=Path, help="New JSON evidence file; existing files are never overwritten"
    )
    registry.add_argument(
        "--workspace-root",
        type=Path,
        help="Reject registry/output paths escaping this optional boundary",
    )
    review = commands.add_parser("run", help="Run bounded local analysis")
    review.add_argument("skill", choices=SKILLS)
    review.add_argument("--input", required=True, type=Path, help="Local UTF-8 file, up to 5 MB")
    review.add_argument("--format", choices=("json", "markdown"), default="json")
    review.add_argument(
        "--workspace-root",
        type=Path,
        help="Reject input/output paths escaping this optional boundary",
    )
    review.add_argument("--output", type=Path, help="Write a new file; refuses to overwrite")
    review.add_argument(
        "--fail-on-findings", action="store_true", help="Return 1 if findings are present"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(SKILLS))
            return 0
        if args.command == "validate":
            print(json.dumps(validate_library(args.root, SKILLS), sort_keys=True))
            return 0
        if args.command == "registry":
            within_root(args.registry, args.workspace_root)
            if args.output:
                within_root(args.output, args.workspace_root)
            # Reserve output first so an existing path cannot cause unnecessary network requests.
            stream = args.output.open("x", encoding="utf-8") if args.output else None
            try:
                result = verify_registry(args.registry, live=args.live, timeout=args.timeout)
                output = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
                if stream:
                    stream.write(output)
                else:
                    print(output, end="")
            finally:
                if stream:
                    stream.close()
            return (
                1 if any(e["retrieval_status"] != "retrieved" for e in result["retrievals"]) else 0
            )
        within_root(args.input, args.workspace_root)
        if args.output:
            within_root(args.output, args.workspace_root)
        text = read_text(args.input)
        data = (
            text
            if args.skill in TEXT_SKILLS
            else json.loads(
                text,
                parse_constant=reject_constant,
                parse_float=finite_float,
                object_pairs_hook=unique_object,
            )
        )
        result = run(args.skill, data)
        output = render(result, args.format)
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output)
        else:
            print(output, end="")
        return 1 if args.fail_on_findings and result["findings"] else 0
    except (InputError, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        # Do not echo data, file paths, tokens, or parser source fragments.
        reason = str(exc) if isinstance(exc, InputError) else type(exc).__name__
        print(f"trust-skills: input/output error: {reason}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
