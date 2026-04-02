"""tmux-cli: CLI utility for tmux pane communication and command execution."""

from .tmux_cli_controller import TmuxCLIController, CLI
from .tmux_remote_controller import RemoteTmuxController
from .tmux_execution_helpers import (
    generate_execution_markers,
    wrap_command_with_markers,
    find_markers_in_output,
    parse_marked_output,
    poll_for_completion,
)

__version__ = "1.0.0"
__all__ = [
    "TmuxCLIController",
    "CLI",
    "RemoteTmuxController",
    "generate_execution_markers",
    "wrap_command_with_markers",
    "find_markers_in_output",
    "parse_marked_output",
    "poll_for_completion",
]
