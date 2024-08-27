import os
import yaml
from typing import Dict, Any
import toml
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

CONFIG_DIR = os.path.expanduser("~/.config/downloader_cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yml")


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        return create_default_config()

    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def create_default_config() -> Dict[str, Any]:
    default_config = {
        "aria2c": "-x 16 -s 16 -j 10 -k 20M --min-split-size=20M --split=10",
        "ytdlp": '--external-downloader aria2c --external-downloader-args "aria2c:-x 16 -s 16"',
        "playlist_file": "",
        "version": get_version_from_pyproject(),
    }

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(default_config, f)

    return default_config


def get_config_value(key: str) -> Any:
    config = load_config()
    return config.get(key)


def get_version_from_pyproject() -> str:
    pyproject_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "pyproject.toml"
    )
    with open(pyproject_path, "r") as f:
        pyproject_data = toml.load(f)
    return pyproject_data["project"]["version"]


def get_playlist_file() -> str:
    config = load_config()
    playlist_file = config.get("playlist_file", "")

    if not playlist_file or not os.path.exists(playlist_file):
        playlist_file = prompt(
            "Enter the path to the playlist text file: ",
            completer=PathCompleter(),
        )

        # Update the config with the new playlist file
        config["playlist_file"] = playlist_file
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f)

    return playlist_file


def update_config(key: str, value: Any) -> None:
    config = load_config()
    config[key] = value
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f)
