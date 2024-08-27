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
import http.server
import socketserver
import threading
import ipaddress
import requests


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
    for file in sorted(directory.glob("*")):
        if file.is_file() and file.name != "playlist.m3u8":
            playlist_content += f"http://{host}:{port}/{file.name}\n"

    playlist_path = directory / "playlist.m3u8"
    with open(playlist_path, "w") as f:
        f.write(playlist_content)

    return str(playlist_path)


def start_http_server(directory: str, port: int):
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at port {port}")
        httpd.serve_forever()


def main(
    directory: Path = typer.Option(
        ".",
        "--directory",
        "-d",
        help="Directory containing the files (default: current directory)",
    ),
    ip: str = typer.Option(None, "--ip", help="Public IP of the VPS (optional)"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve the files"),
    use_localhost: bool = typer.Option(
        False, "--localhost", help="Use localhost instead of public IP"
    ),
):
    """Generate an M3U8 playlist and serve the files via HTTP."""
    directory = Path(directory).expanduser().resolve()

    if not directory.is_dir():
        typer.echo(f"Error: {directory} is not a valid directory.")
        raise typer.Exit(code=1)

    if not use_localhost:
        if ip is None:
            ip = get_public_ip()
        else:
            ip = validate_ip(ip)
    else:
        ip = "localhost"

    playlist_path = generate_m3u8(directory, ip, port, use_localhost)
    typer.echo(f"Generated playlist: {playlist_path}")

    server_thread = threading.Thread(
        target=start_http_server, args=(str(directory), port)
    )
    server_thread.daemon = True
    server_thread.start()

    typer.echo(f"HTTP server started at http://{ip}:{port}")
    typer.echo("Press CTRL+C to stop the server")

    try:
        server_thread.join()
    except KeyboardInterrupt:
        typer.echo("Server stopped")


if __name__ == "__main__":
    typer.run(main)
