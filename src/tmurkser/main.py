import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path

from tomlkit import parse
from libtmux import Server


SERVER: Server


@dataclass
class StandardWindow:
    name: str
    path: Path


@dataclass
class StandardSession:
    name: str
    windows: list[StandardWindow]


def load_config(path: Path) -> list[StandardSession]:
    """Load the tmux configuration.

    Returns:
        list[StandardSession]: A list of standard sessions.
    """
    # This function is a placeholder for loading configuration from a file
    # or other sources. For now, it returns the hardcoded standard sessions.
    config: list[StandardSession] = []
    with open(path, "rb") as f:
        data = parse(f.read())

        for session in data["sessions"]:
            session_name = session["name"]
            windows = [
                StandardWindow(name=window["name"], path=Path(window["path"]))
                for window in session["windows"]
            ]
            config.append(StandardSession(name=session_name, windows=windows))

    return config


def open_default_sessions():
    """Open default sessions in tmux.

    Args:
        server (Server): The tmux server instance.
    """
    server: Server = SERVER

    for session in load_config(Path("sessions.toml")):
        # Check if the session already exists
        existing_session = server.sessions.filter(session_name=session.name)
        if existing_session:
            print(f"Session {session.name} already exists.")
            continue

        # Create a new session
        window = session.windows.pop(0)
        new_session = server.new_session(
            session_name=session.name,
            attach=False,
            window_name=window.name,
        )

        new_session.windows[0].active_pane.send_keys(
            f" cd {window.path} && clear", enter=True
        )

        for window in session.windows:
            new_session.new_window(
                window_name=window.name, start_directory=str(window.path)
            )


def main():
    """Run the tmurkser script."""
    global SERVER
    SERVER = Server()

    parser = ArgumentParser(
        prog="tmurkser",
        description="A tmux session manager",
        epilog="Licensed under the MIT license. (c) 2025 Simon Barth",
    )
    subparsers = parser.add_subparsers(help="commands help", dest="command")

    save_parser = subparsers.add_parser("save", help="Save the current sessions")

    target_group = save_parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--all", "-a", action="store_true", help="Save all current sessions"
    )
    target_group.add_argument(
        "--session", nargs="*", help="Name of the session(s) to save"
    )
    target_group.add_argument(
        "--exclude",
        nargs="*",
        help="Name of the session(s) to exclude. All others will be saved",
    )

    parser.add_argument("--load", action="store_true", help="Load the saved sessions")

    args = parser.parse_args()

    if args.load:
        open_default_sessions()
    sys.exit(0)
