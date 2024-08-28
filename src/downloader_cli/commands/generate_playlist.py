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
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from ..utils.config import get_config_value
import asyncio
import mimetypes
import aiofiles
from datetime import datetime
import logging
import html

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
        raise typer.BadParameter("Invalid IP address")


def generate_m3u8(directory: Path, ip: str, port: int, use_localhost: bool) -> str:
    playlist_content = "#EXTM3U\n"
    host = "localhost" if use_localhost else ip
    video_files = []

    logger.debug(f"Scanning directory: {directory}")
    for file in sorted(directory.glob("*")):
        if file.is_file() and file.name != "playlist.m3u8":
            ext = file.suffix.lower()
            if ext in VIDEO_EXTENSIONS:
                video_files.append(file)
                logger.debug(f"Added video file to playlist: {file}")

    # Add video files to the playlist
    for file in video_files:
        playlist_content += f"http://{host}:{port}/{file.name}\n"

    playlist_path = directory / "playlist.m3u8"
    with open(playlist_path, "w") as f:
        f.write(playlist_content)

    logger.debug(f"Generated playlist at: {playlist_path}")
    return str(playlist_path)


def get_whitelisted_ips():
    return get_config_value("ip_whitelist")


async def check_ip_whitelist(request, handler):
    client_ip = request.remote
    whitelisted_ips = get_whitelisted_ips()

    if client_ip not in whitelisted_ips:
        return web.Response(status=403, text="Access denied")

    return await handler(request)


async def log_access(request, file_path):
    client_ip = request.remote
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Client IP: {client_ip} accessed file: {file_path}")


async def handle_root_request(request):
    directory = request.app["directory"]
    files = sorted(directory.glob("*"))

    video_files = [
        f for f in files if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
    image_files = [
        f for f in files if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    html_content = "<html><body>"
    html_content += "<h1>Playlist</h1>"
    html_content += '<p><a href="/playlist.m3u8">playlist.m3u8</a></p>'
    html_content += "<h1>Video Files</h1>"
    html_content += "<ul>"
    for file in video_files:
        html_content += (
            f'<li><a href="/{html.escape(file.name)}">{html.escape(file.name)}</a></li>'
        )
    html_content += "</ul>"

    html_content += "<h1>Image Files</h1>"
    html_content += "<ul>"
    for file in image_files:
        html_content += (
            f'<li><a href="/{html.escape(file.name)}">{html.escape(file.name)}</a></li>'
        )
    html_content += "</ul>"
    html_content += "</body></html>"

    return web.Response(text=html_content, content_type="text/html")


async def handle_file_request(request):
    file_path = request.match_info["file_path"]
    full_path = os.path.join(str(request.app["directory"]), file_path)

    logger.debug(f"Requested file: {file_path}")
    logger.debug(f"Full path: {full_path}")

    await log_access(request, file_path)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        logger.error(f"File not found: {full_path}")
        return web.Response(status=404, text="File not found")

    file_size = os.path.getsize(full_path)
    mime_type, _ = mimetypes.guess_type(full_path)

    logger.debug(f"File size: {file_size}, MIME type: {mime_type}")

    headers = {
        "Content-Type": mime_type or "application/octet-stream",
        "Accept-Ranges": "bytes",
    }

    if "range" in request.headers:
        try:
            range_header = request.headers["range"].strip().lower()
            range_match = range_header.split("=")[1]
            start, end = map(str.strip, range_match.split("-"))
            start = int(start)
            end = int(end) if end else file_size - 1
            chunk_size = end - start + 1

            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            headers["Content-Length"] = str(chunk_size)

            async with aiofiles.open(full_path, "rb") as f:
                await f.seek(start)
                chunk = await f.read(chunk_size)
                return web.Response(body=chunk, headers=headers, status=206)
        except ValueError:
            pass

    return web.FileResponse(full_path, headers=headers)


async def start_http_server(directory: Path, ip: str, port: int):
    app = web.Application(middlewares=[check_ip_whitelist])
    app["directory"] = directory
    app.router.add_get("/", handle_root_request)
    app.router.add_get("/{file_path:.*}", handle_file_request)

    # Setup CORS
    cors = cors_setup(
        app,
        defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, ip, port)
    await site.start()

    logger.info(f"Serving at http://{ip}:{port}")
    logger.info(f"Serving files from directory: {directory}")
    logger.info(f"Playlist available at http://{ip}:{port}/playlist.m3u8")
    logger.info(f"Whitelisted IPs: {', '.join(get_whitelisted_ips())}")
    print("Access log:")

    # Keep the server running
    while True:
        await asyncio.sleep(3600)  # Sleep for an hour


def main(
    directory: Path = typer.Option(
        ..., "--directory", "-d", help="Directory containing the files"
    ),
    ip: str = typer.Option(None, "--ip", help="IP to bind the server to (optional)"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve the files"),
    use_localhost: bool = typer.Option(
        False, "--localhost", help="Use localhost instead of host IP"
    ),
):
    """Generate an M3U8 playlist and serve the files via HTTP."""
    if use_localhost:
        ip = "localhost"
    elif ip is None:
        ip = get_host_ip()
    else:
        ip = validate_ip(ip)

    directory = Path(directory).resolve()
    logger.info(f"Using directory: {directory}")

    playlist_path = generate_m3u8(directory, ip, port, use_localhost)
    typer.echo(f"Generated playlist: {playlist_path}")
    typer.echo(f"Playlist URL: http://{ip}:{port}/playlist.m3u8")

    typer.echo(f"Starting HTTP server at http://{ip}:{port}")
    typer.echo("Press CTRL+C to stop the server")

    try:
        asyncio.run(start_http_server(directory, ip, port))
    except KeyboardInterrupt:
        typer.echo("Server stopped")


if __name__ == "__main__":
    typer.run(main)
