import os
import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter


def get_path(prompt_text: str, default: str = "") -> str:
    return prompt(
        prompt_text,
        default=default,
        completer=PathCompleter(),
    )


def podman_run():
    """Interactively generate a Podman command to run downloader-cli."""
    print("Welcome to the downloader-cli Podman command generator!")

    command = typer.prompt(
        "Which command do you want to run? (generate-playlist/download)"
    )

    host_path = get_path("Enter the path on your host machine: ")
    host_path = os.path.abspath(os.path.expanduser(host_path))

    container_path = get_path("Enter the path inside the container: ", default="/data")

    base_cmd = (
        f"podman run -it --rm -v {host_path}:{container_path} downloader-cli {command}"
    )

    if command == "generate-playlist":
        directory = get_path(
            "Enter the directory containing the files (relative to the container path): "
        )
        full_cmd = f"{base_cmd} --directory {os.path.join(container_path, directory)}"
    elif command == "download":
        download_path = get_path(
            "Enter the download path (relative to the container path): "
        )
        full_cmd = f"{base_cmd} --path {os.path.join(container_path, download_path)}"
    else:
        print("Invalid command selected.")
        return

    print("\nHere's your Podman command:")
    print(full_cmd)
    print(
        "\nYou can now copy and paste this command to run downloader-cli in a Podman container."
    )
