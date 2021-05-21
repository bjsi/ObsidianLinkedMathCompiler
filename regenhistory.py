import json
import os
from pathlib import Path
import typing as T
import re

from filesystem import FileSystem
from const import BLOCK_REF_REGEX


class RegenHistory:

    fs: FileSystem
    data: T.Dict

    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.data = self.read()

    def read(self):
        try:
            with open(self.fs.get_history_file()) as f:
                return json.loads(f.read())
        except Exception:
            pass

        return {}

    def write(self):
        try:
            with open(self.fs.get_history_file(), 'w') as f:
                f.write(json.dumps(self.data))
        except Exception as e:
            print(f"Failed to get regeneration history with exception {e}")

    @staticmethod
    def get_modified_time(file):
        return int(os.path.getmtime(file))

    def get_blockref_files(self, md: str):
        files = []
        for file_tuple in re.findall(BLOCK_REF_REGEX, md):
            file = os.path.join(self.fs.obsidian_vault_root, file_tuple[0])
            if os.path.exists(file):
                files.append(file)
        return files

    def should_regen(self, file: Path):
        last_regen = self.data.get("global_last_regen", -1)
        last_modified = self.get_modified_time(file)

        # Simple case - this file was modified since the last regen.
        if last_modified > last_regen:
            return True

        # Complex case - some file included as a block ref was modified since last regen.
        md = file.read_text()
        block_ref_files = self.get_blockref_files(md)
        for ref_file in block_ref_files:
            ref_last_modified = self.get_modified_time(ref_file)

            # block refs file's last modified time > last regen time
            if ref_last_modified > last_regen:
                return True

        return False
