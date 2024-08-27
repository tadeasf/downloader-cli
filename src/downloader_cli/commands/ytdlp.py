import subprocess
from ..utils.config import get_config_value
import typer


def ask_yes_no(prompt: str) -> bool:
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        print("Please answer yes or no.")


def get_integer(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid integer.")


def check_tmux_installed() -> bool:
    return (
        subprocess.run(["which", "tmux"], capture_output=True, text=True).returncode
        == 0
    )


def get_download_settings(download_dir: str, playlist_file: str) -> dict:
    settings = {
        "download_dir": download_dir,
        "downloader": "yt-dlp"
        if typer.confirm(
            "Do you want to use yt-dlp + aria2c? (If no, only aria2c will be used)"
        )
        else "aria2c",
        "aria2c_settings": {},
        "ytdlp_settings": "",
        "playlist_file": playlist_file,
    }

    if settings["downloader"] == "aria2c":
        aria2c_config = get_config_value("aria2c")
        if typer.confirm(
            f"Do you want to use the default aria2c settings? ({aria2c_config})"
        ):
            settings["aria2c_settings"] = aria2c_config
        else:
            settings["aria2c_settings"] = typer.prompt("Enter custom aria2c settings")
    else:
        ytdlp_config = get_config_value("ytdlp")
        if typer.confirm(
            f"Do you want to use the default yt-dlp settings? ({ytdlp_config})"
        ):
            settings["ytdlp_settings"] = ytdlp_config
        else:
            settings["ytdlp_settings"] = typer.prompt("Enter custom yt-dlp settings")

    if settings["downloader"] == "yt-dlp":
        settings["shorten_names"] = typer.confirm(
            "Do you want to implement name shortening?"
        )

    return settings


def prepare_download_command(settings: dict) -> str:
    if settings["downloader"] == "yt-dlp":
        output_template = (
            "%(autonumber)s.%(ext)s"
            if settings.get("shorten_names", False)
            else "%(title)s.%(ext)s"
        )
        cmd = f"yt-dlp {settings['ytdlp_settings']} -a \"{settings['playlist_file']}\" --output \"{settings['download_dir']}/{output_template}\""
    else:
        cmd = f"aria2c --dir=\"{settings['download_dir']}\" -i \"{settings['playlist_file']}\" {settings['aria2c_settings']}"
    return cmd


def start_tmux_session(cmd: str) -> None:
    session_name = "download_session"
    subprocess.run(["tmux", "new-session", "-d", "-s", session_name, "bash"])
    subprocess.run(["tmux", "send-keys", "-t", session_name, cmd, "C-m"])

    if (
        subprocess.run(
            ["tmux", "has-session", "-t", session_name], capture_output=True
        ).returncode
        == 0
    ):
        print(f"Download started in a new tmux session named '{session_name}'.")
        print(
            f"You can attach to the session using 'tmux attach-session -t {session_name}'"
        )
        print(
            "The download will continue in the background even if you exit the shell."
        )
    else:
        print(
            "Failed to start tmux session. Please check your tmux installation and try again."
        )


def main(download_dir: str, playlist_file: str) -> None:
    if not check_tmux_installed():
        typer.echo("tmux is not installed. Please install tmux and try again.")
        raise typer.Exit(code=1)

    settings = get_download_settings(download_dir, playlist_file)
    cmd = prepare_download_command(settings)
    start_tmux_session(cmd)


if __name__ == "__main__":
    main()
