import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from ..utils.network import get_host_ip

app = FastAPI()


def generate_playlist(directory: Path, ip: str, port: int) -> Path:
    playlist_content = "#EXTM3U\n"
    for file in directory.glob("**/*.mp4"):
        relative_path = file.relative_to(directory)
        url = f"http://{ip}:{port}/videos/{relative_path}"
        playlist_content += f"#EXTINF:-1,{file.name}\n{url}\n"

    playlist_path = directory / "playlist.m3u8"
    playlist_path.write_text(playlist_content)
    return playlist_path


def serve_watch_playlist():
    directory = (
        Path(
            prompt(
                "Enter the directory containing the MP4 files: ",
                completer=PathCompleter(only_directories=True),
            )
        )
        .expanduser()
        .resolve()
    )

    if not directory.is_dir():
        print(f"Error: {directory} is not a valid directory.")
        return

    ip = get_host_ip()
    port = 8000

    playlist_path = generate_playlist(directory, ip, port)
    print(f"Generated playlist: {playlist_path}")

    app.mount("/videos", StaticFiles(directory=str(directory)), name="videos")

    @app.get("/")
    async def read_root(request: Request):
        video_files = [f for f in directory.glob("**/*.mp4")]
        video_list = "\n".join(
            [
                f'<li><a href="/videos/{f.relative_to(directory)}">{f.name}</a></li>'
                for f in video_files
            ]
        )
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Video Playlist</title>
            </head>
            <body>
                <h1>Video Playlist</h1>
                <a href="/playlist.m3u8">Download Playlist</a>
                <ul>
                    {video_list}
                </ul>
            </body>
        </html>
        """)

    @app.get("/playlist.m3u8")
    async def get_playlist():
        return FileResponse(playlist_path)

    print(f"Starting server at http://{ip}:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    serve_watch_playlist()
