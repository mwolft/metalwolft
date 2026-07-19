from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.database_identity import (  # noqa: E402
    DatabaseIdentityError,
    mask_database_identity,
    parse_database_identity,
    validate_database_identity,
)


def run_identity_check(
    environ: Mapping[str, str],
    *,
    output: Callable[[str], None] = print,
) -> int:
    try:
        identity = parse_database_identity(environ.get("DATABASE_URL"))
        validate_database_identity(
            identity,
            expected_host=environ.get("DATABASE_EXPECTED_HOST"),
            expected_name=environ.get("DATABASE_EXPECTED_NAME"),
            expected_user=environ.get("DATABASE_EXPECTED_USER"),
        )
    except DatabaseIdentityError as exc:
        output("Database identity check: FAILED")
        output(f"Reason: {exc}")
        return 1

    safe_identity = mask_database_identity(identity)
    output("Database identity check: OK")
    output(f"Scheme: {safe_identity['scheme']}")
    output(f"Host: {safe_identity['host']}")
    output(f"Port: {safe_identity['port'] or '(default)'}")
    output(f"Database: {safe_identity['database_name']}")
    output(f"User: {safe_identity['username']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_identity_check(os.environ)


if __name__ == "__main__":
    raise SystemExit(main())
