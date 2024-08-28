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

import typer
from typing import Optional
from pathlib import Path
from datetime import datetime
from rich.traceback import install as install_rich_traceback
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from .commands import ytdlp
from .utils.config import get_playlist_file
from .commands.generate_playlist import main as generate_playlist_main
from .commands.podman_run import podman_run
from .commands.mpv import mpv
from .commands.serve_watch_playlist import serve_watch_playlist
from typing import List

install_rich_traceback()

app = typer.Typer()


def path_callback(value: Optional[str] = None) -> Path:
    if value is None:
        value = prompt("Enter the download directory: ", completer=PathCompleter())
    path = Path(value).expanduser().resolve()
    if not path.exists():
        typer.echo(f"The path {path} does not exist. Creating it...")
        path.mkdir(parents=True, exist_ok=True)
    return path


@app.command()
def version():
    """
    Show the version of the downloader CLI.
    """
    from .utils.config import get_config_value

    typer.echo(get_config_value("version"))


@app.command()
def download(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Directory to download files",
        callback=path_callback,
    ),
    create_new_dir: bool = typer.Option(
        False,
        "--new-dir",
        "-d",
        help="Create a new directory for this download session",
    ),
):
    """Start the download process."""
    if create_new_dir:
        index = 1
        while True:
            new_dir_name = f"downloads_{datetime.now().strftime('%d_%m_%Y')}_{index}"
            new_path = path / new_dir_name
            if not new_path.exists():
                new_path.mkdir()
                path = new_path
                break
            index += 1

    typer.echo(f"Download directory: {path}")

    # Get the playlist file using the new function
    playlist_file = get_playlist_file()

    # Call the ytdlp.main() function with the necessary arguments
    ytdlp.main(str(path), playlist_file)


@app.command()
def generate_playlist(
    directories: List[Path] = typer.Option(
        None,
        "--directory",
        "-d",
        help="Directories containing the files (can be specified multiple times)",
    ),
    ip: str = typer.Option(None, "--ip", help="IP to bind the server to (optional)"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve the files"),
    use_localhost: bool = typer.Option(
        False, "--localhost", help="Use localhost instead of host IP"
    ),
):
    """Generate an M3U8 playlist from multiple directories and serve the files via HTTP."""
    if directories is None:
        directories = [get_directory()]

    for directory in directories:
        if not directory.is_dir():
            typer.echo(f"Error: {directory} is not a valid directory.")
            raise typer.Exit(code=1)

    generate_playlist_main(directories, ip, port, use_localhost)


def get_directory() -> Path:
    directory = prompt(
        "Enter the directory containing the files: ",
        completer=PathCompleter(),
    )
    return Path(directory).expanduser().resolve()


@app.command()
def serve_and_watch():
    """Serve a directory of MP4 files and generate a playlist."""
    serve_watch_playlist()


app.command()(podman_run)
app.command()(mpv)

if __name__ == "__main__":
    app()
