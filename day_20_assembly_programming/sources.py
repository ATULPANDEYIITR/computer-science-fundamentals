from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src"

REQUIRED_FILES = [
    "01_conditions.s",
    "02_loops.s",
    "03_functions.s",
    "04_stack.s",
    "05_recursion.s",
    "06_array_processing.s",
    "07_integrated_lab.s",
]

REQUIRED_PATTERNS = {
    "01_conditions.s": [
        r"\.data",
        r"\.text",
        r"\bmain:",
        r"\bbeq\b|\bbne\b|\bslt\b",
        r"\bsyscall\b",
    ],
    "02_loops.s": [
        r"\.text",
        r"\bmain:",
        r"\bloop_",
        r"\bj\b",
        r"\bslt\b",
    ],
    "03_functions.s": [
        r"\bjal\b",
        r"\bjr\s+\$ra",
        r"\badd_numbers:",
    ],
    "04_stack.s": [
        r"\$sp",
        r"\bsw\b",
        r"\blw\b",
        r"\baddi\s+\$sp",
        r"\bjal\b",
        r"\bjr\s+\$ra",
    ],
    "05_recursion.s": [
        r"\bjal\s+factorial_recursive",
        r"\bfactorial_recursive:",
        r"\bjr\s+\$ra",
    ],
    "06_array_processing.s": [
        r"\barray_sum:",
        r"\barray_max:",
        r"\blw\b",
        r"\bsll\b",
        r"\bjal\b",
    ],
    "07_integrated_lab.s": [
        r"\bmain:",
        r"\bjal\b",
        r"\$sp",
        r"\bsw\b",
        r"\blw\b",
        r"\bbeq\b|\bbne\b|\bslt\b",
        r"\bloop_",
    ],
}


def validate() -> list[str]:
    errors: list[str] = []

    for filename in REQUIRED_FILES:
        path = SOURCE_DIR / filename

        if not path.is_file():
            errors.append(f"Missing required assembly file: {path}")
            continue

        content = path.read_text(encoding="utf-8")

        if not content.strip():
            errors.append(f"Assembly file is empty: {path}")

        for pattern in REQUIRED_PATTERNS.get(filename, []):
            if not re.search(pattern, content):
                errors.append(
                    f"{filename} does not contain required pattern: {pattern}"
                )

        labels = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*):", content, re.MULTILINE)
        label_set = set(labels)

        for target in re.findall(
            r"^\s*(?:beq|bne|bltz|bgez|bgtz|blez|j|jal)\s+"
            r"(?:\$[A-Za-z0-9]+,\s*)?(?:\$[A-Za-z0-9]+,\s*)?"
            r"([A-Za-z_][A-Za-z0-9_]*)",
            content,
            re.MULTILINE,
        ):
            if target not in label_set:
                errors.append(
                    f"{filename} references a branch/jump label that is not defined: {target}"
                )

    return errors


def main() -> int:
    errors = validate()

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Validated {len(REQUIRED_FILES)} MIPS assembly source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
