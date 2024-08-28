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
import typer
from pathlib import Path
import ipaddress
import requests
from ..utils.network import get_host_ip
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, FileResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn
import mimetypes
import logging
import html as html_module
from typing import List
from ..utils.config import get_config_value

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".3gp",
    ".3g2",
    ".gif",
    ".ts",
    ".vob",
    ".ogv",
    ".drc",
    ".gifv",
    ".mng",
    ".qt",
    ".yuv",
    ".rm",
    ".rmvb",
    ".asf",
    ".amv",
    ".m2v",
    ".svi",
    ".m2ts",
    ".mts",
    ".mxf",
    ".roq",
    ".nsv",
    ".f4v",
    ".f4p",
    ".f4a",
    ".f4b",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".bmp",
    ".tiff",
    ".tif",
    ".gif",
}


def get_public_ip() -> str:
    try:
        response = requests.get("https://api.ipify.org")
        return response.text
    except requests.RequestException:
        typer.echo("Failed to fetch public IP. Please provide it manually.")
        return typer.prompt("Enter the public IP of the VPS")


def validate_ip(ip: str) -> str:
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        typer.echo(f"Invalid IP address: {ip}")
        return typer.prompt("Enter a valid IP address")


def get_whitelisted_ips():
    whitelist = get_config_value("ip_whitelist")
    if isinstance(whitelist, list):
        return whitelist
    elif isinstance(whitelist, str):
        return [whitelist]
    else:
        return []  # Return an empty list if the value is not a list or string


def generate_m3u8(
    directories: List[Path], ip: str, port: int, use_localhost: bool
) -> Path:
    playlist_content = "#EXTM3U\n"
    base_url = f"http://{'localhost' if use_localhost else ip}:{port}"

    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(
                    tuple(VIDEO_EXTENSIONS.union(IMAGE_EXTENSIONS))
                ):
                    relative_path = os.path.relpath(root, directory.parent)
                    file_url = f"{base_url}/{relative_path}/{file}"
                    playlist_content += f"#EXTINF:-1,{file}\n{file_url}\n"

    playlist_path = directories[0].parent / "playlist.m3u8"
    with open(playlist_path, "w") as f:
        f.write(playlist_content)

    return playlist_path


async def handle_root_request(request):
    directories = request.app.state.directories
    html_content = "<h1>File List</h1>"
    for directory in directories:
        html_content += f"<h2>{directory}</h2><ul>"
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(
                    tuple(VIDEO_EXTENSIONS.union(IMAGE_EXTENSIONS))
                ):
                    relative_path = os.path.relpath(root, directory.parent)
                    file_url = f"/{relative_path}/{file}"
                    html_content += (
                        f'<li><a href="{file_url}">{html_module.escape(file)}</a></li>'
                    )
        html_content += "</ul>"
    html_content += '<p><a href="/playlist.m3u8">Download M3U8 Playlist</a></p>'
    return HTMLResponse(html_content)


async def handle_file_request(request):
    file_path = request.path_params["file_path"]
    directories = request.app.state.directories
    for directory in directories:
        full_path = directory.parent / file_path
        if full_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(full_path))
            headers = {"Content-Type": mime_type} if mime_type else None
            return FileResponse(str(full_path), headers=headers)
    return PlainTextResponse("File not found", status_code=404)


def check_ip_whitelist(request):
    client_ip = request.client.host
    whitelisted_ips = get_whitelisted_ips()

    if not whitelisted_ips or client_ip in whitelisted_ips:
        return True
    else:
        return False


async def ip_whitelist_middleware(request, call_next):
    if not check_ip_whitelist(request):
        return PlainTextResponse("Access denied", status_code=403)
    response = await call_next(request)
    return response


def start_http_server(directories: List[Path], ip: str, port: int):
    routes = [
        Route("/", handle_root_request),
        Route("/{file_path:path}", handle_file_request),
    ]

    app = Starlette(
        routes=routes,
        middleware=[
            {
                "middleware": ip_whitelist_middleware,
            }
        ],
    )
    app.state.directories = directories

    logger.info(f"Serving at http://{ip}:{port}")
    logger.info(
        f"Serving files from directories: {', '.join(str(d) for d in directories)}"
    )
    logger.info(f"Playlist available at http://{ip}:{port}/playlist.m3u8")
    whitelisted_ips = get_whitelisted_ips()
    if whitelisted_ips:
        logger.info(f"Whitelisted IPs: {', '.join(whitelisted_ips)}")
    else:
        logger.info("No IP whitelist configured")
    print("Access log:")

    uvicorn.run(app, host=ip, port=port)


def main(
    directories: List[Path] = typer.Option(
        ...,
        "--directory",
        "-d",
        help="Directories containing the files (can be specified multiple times)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    ip: str = typer.Option(None, "--ip", help="IP to bind the server to (optional)"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve the files"),
    use_localhost: bool = typer.Option(
        False, "--localhost", help="Use localhost instead of host IP"
    ),
):
    """Generate an M3U8 playlist from multiple directories and serve the files via HTTP."""
    if use_localhost:
        ip = "localhost"
    elif ip is None:
        ip = get_host_ip()
    else:
        ip = validate_ip(ip)

    logger.info(f"Using directories: {', '.join(str(d) for d in directories)}")

    playlist_path = generate_m3u8(directories, ip, port, use_localhost)
    typer.echo(f"Generated playlist: {playlist_path}")
    typer.echo(f"Playlist URL: http://{ip}:{port}/playlist.m3u8")

    typer.echo(f"Starting HTTP server at http://{ip}:{port}")
    typer.echo("Press CTRL+C to stop the server")

    try:
        start_http_server(directories, ip, port)
    except KeyboardInterrupt:
        typer.echo("Server stopped")


if __name__ == "__main__":
    typer.run(main)
