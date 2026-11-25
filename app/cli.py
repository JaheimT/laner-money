"""Command-line admin tasks.

    python -m app.cli set-password      # set or change the login password

In Docker:
    docker compose exec laner python -m app.cli set-password
"""

import getpass
import sys

from app import auth
from app.db import SessionLocal


def set_password() -> int:
    first = getpass.getpass(f"New password (at least {auth.PASSWORD_MIN} characters): ")
    problem = auth.check_new_password(first)
    if problem:
        print(problem, file=sys.stderr)
        return 1
    if getpass.getpass("Type it again: ") != first:
        print("Passwords didn't match. Nothing changed.", file=sys.stderr)
        return 1
    with SessionLocal() as session:
        auth.set_password(session, first)
    print("Password set. Any existing logins have been signed out.")
    return 0


COMMANDS = {"set-password": set_password}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return COMMANDS[argv[0]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
