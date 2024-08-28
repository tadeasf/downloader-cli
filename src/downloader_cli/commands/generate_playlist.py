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
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import unquote, quote
import uvicorn
import html as html_module
from typing import List
from ..utils.config import get_config_value
import subprocess
import logging
from datetime import datetime
from functools import lru_cache

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
                    relative_path = os.path.relpath(root, directory)
                    encoded_path = quote(f"{directory.name}/{relative_path}/{file}")
                    file_url = f"{base_url}/{encoded_path}"
                    playlist_content += f"#EXTINF:-1,{file}\n{file_url}\n"

    # Find the next available index for the playlist file
    index = 1
    while True:
        playlist_path = directories[0].parent / f"playlist_{index}.m3u8"
        if not playlist_path.exists():
            break
        index += 1

    with open(playlist_path, "w") as f:
        f.write(playlist_content)

    return playlist_path


@lru_cache(maxsize=1000)
def get_file_info(file_path: Path, directory: Path) -> dict:
    stat = file_path.stat()
    file_info = {
        "name": file_path.name,
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "extension": file_path.suffix.lower(),
        "directory": directory,
    }

    if file_info["extension"] in VIDEO_EXTENSIONS:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
            )
            duration = float(result.stdout)
            file_info["duration"] = f"{int(duration // 60)}:{int(duration % 60):02d}"
        except subprocess.CalledProcessError:
            file_info["duration"] = "N/A"
        except ValueError:
            file_info["duration"] = "N/A"

    return file_info


async def calculate_file_info(directories: List[Path]):
    file_info_list = []
    for directory in directories:
        for file_path in directory.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in VIDEO_EXTENSIONS.union(IMAGE_EXTENSIONS)
            ):
                file_info_list.append(get_file_info(file_path, directory))
    return sorted(file_info_list, key=lambda x: x["created_at"], reverse=True)


async def handle_root_request(request):
    directories = request.app.state.directories
    files = request.app.state.file_info  # Use pre-calculated file info

    css = """
    <style>
        body {
            font-family: 'JetBrains Mono', monospace;
            background-color: #1e1e2e;
            color: #cdd6f4;
            margin: 0;
            padding: 20px;
        }
        h1 {
            color: #cba6f7;
            text-align: center;
        }
        .button-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .button {
            background-color: #cba6f7;
            color: #1e1e2e;
            border: none;
            padding: 10px 20px;
            margin: 0 10px;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #45475a;
        }
        th {
            background-color: #313244;
            color: #cba6f7;
            cursor: pointer;
            position: relative;
        }
        th:hover {
            background-color: #45475a;
        }
        th::after {
            content: '';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
        }
        th.asc::after {
            content: '▲';
        }
        th.desc::after {
            content: '▼';
        }
        tr:hover {
            background-color: #313244;
        }
        .file-link {
            color: #cdd6f4;
            text-decoration: none;
        }
        .file-link:hover {
            text-decoration: underline;
        }
    </style>
    """

    javascript = """
    <script>
    let sortedData = {};

    function sortTable(n) {
        const table = document.getElementById("fileTable");
        const tbody = table.getElementsByTagName("tbody")[0];
        const rows = Array.from(tbody.rows);
        
        if (sortedData[n] === undefined) {
            sortedData[n] = {
                asc: rows.slice().sort((a, b) => compareRows(a, b, n)),
                desc: rows.slice().sort((a, b) => compareRows(b, a, n))
            };
        }

        const currentOrder = tbody.getAttribute("data-order") || "asc";
        const newOrder = currentOrder === "asc" ? "desc" : "asc";
        
        sortedData[n][newOrder].forEach(row => tbody.appendChild(row));
        
        tbody.setAttribute("data-order", newOrder);
        
        // Update sorting indicators
        const headers = table.getElementsByTagName("th");
        for (let i = 0; i < headers.length; i++) {
            headers[i].classList.remove("asc", "desc");
        }
        headers[n].classList.add(newOrder);
    }

    function compareRows(row1, row2, n) {
        const cell1 = row1.cells[n].innerText;
        const cell2 = row2.cells[n].innerText;

        if (n === 1) { // Size column
            return Number(cell1.split(' ')[0]) - Number(cell2.split(' ')[0]);
        } else if (n === 3) { // Duration column
            if (cell2 === 'N/A') return -1;
            if (cell1 === 'N/A') return 1;
            return cell1.localeCompare(cell2);
        } else {
            return cell1.localeCompare(cell2);
        }
    }
    </script>
    """

    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>File Server</title>
        {css}
        {javascript}
    </head>
    <body>
        <h1>🚀 File Server</h1>
        <div class="button-container">
            <a href="/{request.app.state.playlist_file.name}" download><button class="button">⬇️ Download Playlist</button></a>
            <a href="/raw-playlist"><button class="button">👁️ View Raw Playlist</button></a>
        </div>
        <table id="fileTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">File Name</th>
                    <th onclick="sortTable(1)">Size</th>
                    <th onclick="sortTable(2)">Created At</th>
                    <th onclick="sortTable(3)">Duration</th>
                </tr>
            </thead>
            <tbody>
    """

    for file in files:
        if file["name"] == "playlist.m3u8":
            file_path = "/playlist.m3u8"
        else:
            file_path = f"/{file['directory'].name}/{file['name']}"

        content += f"""
                <tr>
                    <td><a href="{file_path}" target="_blank" class="file-link">{html_module.escape(file['name'])}</a></td>
                    <td>{file['size'] // 1024 // 1024} MB</td>
                    <td>{file['created_at']}</td>
                    <td>{file.get('duration', 'N/A')}</td>
                </tr>
        """

    content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content)


async def handle_raw_playlist(request):
    playlist_path = Path(request.app.state.directories[0]) / "playlist.m3u8"
    if playlist_path.exists():
        with open(playlist_path, "r") as f:
            content = f.read()
        return PlainTextResponse(content)
    else:
        return PlainTextResponse("Playlist not found", status_code=404)


async def handle_file_request(request):
    file_path = unquote(request.path_params["file_path"])
    directories = request.app.state.directories

    if file_path.startswith("playlist_") and file_path.endswith(".m3u8"):
        playlist_path = directories[0].parent / file_path
        if playlist_path.is_file():
            return FileResponse(playlist_path)

    for directory in directories:
        full_path = directory / file_path
        if full_path.is_file():
            return FileResponse(full_path)

        # Try to find the file by ignoring the directory name in the URL
        relative_path = Path(*Path(file_path).parts[1:])
        full_path = directory / relative_path
        if full_path.is_file():
            return FileResponse(full_path)

    return PlainTextResponse("File not found", status_code=404)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not check_ip_whitelist(request):
            return PlainTextResponse("Access denied", status_code=403)
        response = await call_next(request)
        return response


def start_http_server(directories: List[Path], ip: str, port: int, playlist_path: Path):
    routes = [
        Route("/", handle_root_request),
        Route("/raw-playlist", handle_raw_playlist),
        Route("/{file_path:path}", handle_file_request),
    ]

    middleware = [
        Middleware(IPWhitelistMiddleware),
    ]

    app = Starlette(
        routes=routes,
        middleware=middleware,
    )
    app.state.directories = directories
    app.state.playlist_file = playlist_path

    # Calculate file info at startup
    file_info = []
    for directory in directories:
        file_info.extend(
            [get_file_info(f, directory) for f in directory.glob("*") if f.is_file()]
        )

    # Add all playlist files to file_info
    parent_dir = directories[0].parent
    for playlist_file in parent_dir.glob("playlist_*.m3u8"):
        file_info.append(get_file_info(playlist_file, parent_dir))

    file_info.sort(key=lambda x: x["created_at"], reverse=True)
    app.state.file_info = file_info

    logger.info(f"Serving at http://{ip}:{port}")
    logger.info(
        f"Serving files from directories: {', '.join(str(d) for d in directories)}"
    )
    logger.info(f"Playlist available at http://{ip}:{port}/{playlist_path.name}")
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
    typer.echo(f"Playlist URL: http://{ip}:{port}/{playlist_path.name}")

    typer.echo(f"Starting HTTP server at http://{ip}:{port}")
    typer.echo("Press CTRL+C to stop the server")

    try:
        start_http_server(directories, ip, port, playlist_path)
    except KeyboardInterrupt:
        typer.echo("Server stopped")


if __name__ == "__main__":
    typer.run(main)


def check_ip_whitelist(request):
    client_ip = request.client.host
    whitelisted_ips = get_whitelisted_ips()
    return not whitelisted_ips or client_ip in whitelisted_ips
