# Copyright 2024 tadeasfort
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from pathlib import Path


def mpv():
    """Start MPV with a specified .m3u8 file in the background."""
    playlist_path = (
        Path(
            prompt(
                "Enter the path to the .m3u8 file: ",
                completer=PathCompleter(
                    only_directories=False, file_filter=lambda x: x.endswith(".m3u8")
                ),
            )
        )
        .expanduser()
        .resolve()
    )

    if not playlist_path.exists() or not playlist_path.is_file():
        typer.echo(f"Error: {playlist_path} is not a valid file.")
        raise typer.Exit(code=1)

    try:
        subprocess.Popen(["mpv", str(playlist_path)], start_new_session=True)
        typer.echo(f"MPV started with playlist: {playlist_path}")
        typer.echo(
            "MPV is running in the background. You can exit this script without closing MPV."
        )
    except FileNotFoundError:
        typer.echo("Error: MPV is not installed or not in the system PATH.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(mpv)
