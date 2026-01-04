#!/usr/bin/env python3
"""Helper script to run Alembic migrations.

Usage:
    python migrate.py upgrade    # Apply all pending migrations
    python migrate.py downgrade  # Rollback last migration
    python migrate.py revision --autogenerate -m "message"  # Create new migration
"""
import sys
from alembic.config import Config
from alembic import command

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [args...]")
        print("\nCommon commands:")
        print("  upgrade              - Apply all pending migrations")
        print("  downgrade            - Rollback last migration")
        print("  revision --autogenerate -m 'message'  - Create new migration")
        print("  current              - Show current migration version")
        print("  history              - Show migration history")
        sys.exit(1)
    
    alembic_cfg = Config("alembic.ini")
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    if cmd == "upgrade":
        revision = args[0] if args else "head"
        command.upgrade(alembic_cfg, revision)
    elif cmd == "downgrade":
        revision = args[0] if args else "-1"
        command.downgrade(alembic_cfg, revision)
    elif cmd == "revision":
        autogenerate = "--autogenerate" in args
        message_index = args.index("-m") if "-m" in args else -1
        message = args[message_index + 1] if message_index >= 0 else None
        command.revision(alembic_cfg, autogenerate=autogenerate, message=message)
    elif cmd == "current":
        command.current(alembic_cfg)
    elif cmd == "history":
        command.history(alembic_cfg)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()

