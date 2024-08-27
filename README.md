# downloader-cli

A command-line interface tool for downloading and managing playlists.

## Setup and Usage

### Using Rye

1. Install Rye if you haven't already:

   ```sh
   curl -sSf https://rye-up.com/get | bash
   ```

2. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/downloader-cli.git
   cd downloader-cli
   ```

3. Set up the virtual environment and install dependencies:

   ```sh
   rye sync
   ```

4. Build and install the package locally:

   ```sh
   rye build
   pip install dist/*.whl
   ```

5. Run the CLI commands:

   - Generate a playlist:

     ```sh
     downloader generate-playlist --directory /path/to/files
     ```

   - Download using yt-dlp or aria2c:

     ```sh
     downloader download --path /path/to/download
     ```

### Using Podman

1. Build the Docker image:

   ```sh
   podman build -t downloader-cli .
   ```

2. Run the CLI commands:

   - Generate a playlist:

     ```sh
     podman run -it --rm -v /host/path:/container/path downloader-cli generate-playlist --directory /container/path
     ```

   - Download using yt-dlp or aria2c:

     ```sh
     podman run -it --rm -v /host/path:/container/path downloader-cli download --path /container/path
     ```

## Commands

### generate-playlist

Generates an M3U8 playlist and serves the files via HTTP.

Options:

- `--directory`, `-d`: Directory containing the files
- `--ip`: Public IP of the VPS (optional)
- `--port`, `-p`: Port to serve the files (default: 8000)
- `--localhost`: Use localhost instead of public IP

### download

Downloads files using either yt-dlp or aria2c.

Options:

- `--path`, `-p`: Directory to download files

## Note

When using Podman, make sure to adjust the volume mounting (`-v` option) to access files on your host system.
