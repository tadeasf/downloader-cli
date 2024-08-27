import toml


def increment_version():
    with open("pyproject.toml", "r") as f:
        data = toml.load(f)

    version = data["project"]["version"]
    major, minor, patch = map(int, version.split("."))

    data["project"]["version"] = f"{major}.{minor}.{patch+1}"

    with open("pyproject.toml", "w") as f:
        toml.dump(data, f)


if __name__ == "__main__":
    increment_version()
