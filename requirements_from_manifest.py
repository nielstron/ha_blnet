"""
Open the manifest file and extract the requirements
"""
import json
import os

import fire


def get_requirements_from_manifest(manifest_file: str) -> list[str]:
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    return manifest["requirements"]

if __name__ == '__main__':
    reqs = fire.Fire(get_requirements_from_manifest)
    for req in reqs:
        print(req)