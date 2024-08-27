# Downloader CLI

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

3. Install the package in editable mode:

   ```sh
   rye sync
   rye run install
   ```

### Using Podman

1. Build the Docker image:

   ```sh
   podman build -t downloader-cli .
   ```

2. Run the CLI commands:

   - Generate a Podman command:

     ```sh
     downloader podman-run
     ```

   - Generate a playlist:

     ```sh
     podman run -it --rm -v /host/path:/container/path downloader-cli generate-playlist --directory /container/path
     ```

   - Download using yt-dlp or aria2c:

     ```sh
     podman run -it --rm -v /host/path:/container/path downloader-cli download --path /container/path
     ```

## Available Commands

- `generate-playlist`: Generate an M3U8 playlist and serve the files via HTTP.
- `download`: Download files using yt-dlp or aria2c.
- `podman-run`: Interactively generate a Podman command to run downloader-cli.

For more details on each command, use the `--help` option:

```sh
    downloader generate-playlist --help
    downloader download --help
    downloader podman-run --help
```

## Configuration

The default settings for yt-dlp and aria2c can be configured in the `config.py` file.

## Dependencies

- Python 3.12+
- Rye
- Podman (for containerized usage)
- tmux (for background downloads)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
