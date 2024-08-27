import typer
from typing import Optional
from pathlib import Path
from datetime import datetime
from rich.traceback import install as install_rich_traceback
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from .commands import ytdlp
from .utils.config import get_playlist_file

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


if __name__ == "__main__":
    app()
