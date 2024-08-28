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

import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter, WordCompleter


def get_path(prompt_text: str, default: str = "") -> str:
    return prompt(
        prompt_text,
        default=default,
        completer=PathCompleter(),
    )


def podman_run():
    """Interactively generate a Podman command to run downloader-cli."""
    print("Welcome to the downloader-cli Podman command generator!")

    command_completer = WordCompleter(["generate-playlist", "download", "mpv"])
    command = prompt(
        "Which command do you want to run? (generate-playlist/download/mpv): ",
        completer=command_completer,
    )

    host_path = get_path("Enter the path on your host machine: ")
    host_path = os.path.abspath(os.path.expanduser(host_path))

    container_path = get_path("Enter the path inside the container: ", default="/data")

    base_cmd = f"podman run -it --rm -p 8000:8000 -v {host_path}:{container_path} downloader-cli {command}"

    if command == "generate-playlist":
        directory = get_path(
            "Enter the directory containing the files (relative to the container path): ",
            default=".",
        )
        use_localhost = prompt("Use localhost? (y/n): ").lower() == "y"
        localhost_flag = "--localhost" if use_localhost else ""
        full_cmd = f"{base_cmd} --directory {os.path.join(container_path, directory)} {localhost_flag}"
    elif command == "download":
        download_path = get_path(
            "Enter the download path (relative to the container path): "
        )
        full_cmd = f"{base_cmd} --path {os.path.join(container_path, download_path)}"
    elif command == "mpv":
        playlist_path = get_path(
            "Enter the path to the .m3u8 file (relative to the container path): "
        )
        full_cmd = f"{base_cmd} {os.path.join(container_path, playlist_path)}"
    else:
        print("Invalid command selected.")
        return

    print("\nHere's your Podman command:")
    print(full_cmd)
    print(
        "\nYou can now copy and paste this command to run downloader-cli in a Podman container."
    )
