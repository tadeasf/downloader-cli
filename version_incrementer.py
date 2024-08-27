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

import re
import argparse
from typing import Literal, Optional


def increment_version(
    version_type: Optional[Literal["major", "minor", "patch"]] = None,
) -> None:
    with open("pyproject.toml", "r") as f:
        content = f.read()

    version_pattern = r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
    match = re.search(version_pattern, content)

    if not match:
        raise ValueError("Version not found in pyproject.toml")

    major, minor, patch = map(int, match.groups())

    if version_type is None or version_type == "patch":
        patch += 1
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "major":
        major += 1
        minor = 0
        patch = 0

    new_version = f"{major}.{minor}.{patch}"
    new_content = re.sub(version_pattern, f'version = "{new_version}"', content)

    with open("pyproject.toml", "w") as f:
        f.write(new_content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Increment version in pyproject.toml")
    parser.add_argument(
        "--type",
        type=str,
        choices=["major", "minor", "patch"],
        default=None,
        help="Version increment type (default: patch)",
    )
    args = parser.parse_args()

    increment_version(args.type)
    print(f"Version incremented successfully! ({args.type or 'patch'})")


if __name__ == "__main__":
    main()
