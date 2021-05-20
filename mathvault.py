import os
import time

from filesystem import FileSystem
from mathfile import MathFile
from regenhistory import RegenHistory
from utils import get_files
from const import MATH_FOLDER_REL


class MathVault:

    fs: FileSystem

    def __init__(self, obsidian_vault_root: str, sm_collection_root: str):
        if any(not os.path.exists(x) for x in [obsidian_vault_root, sm_collection_root]):
            print("Couldn't find the Obsidian Vault or SM collection.")
            raise FileNotFoundError()

        sm_math_folder = os.path.join(sm_collection_root, MATH_FOLDER_REL)
        if not os.path.exists(sm_math_folder):
            os.mkdir(sm_math_folder)

        self.fs = FileSystem(sm_collection_root, obsidian_vault_root)

    def get_math_files(self, history: RegenHistory):
        files = get_files(self.fs.obsidian_vault_root, ".md", True)
        return [
            MathFile(self.fs, file)
            for file in files if history.should_regen(file)
        ]

    def regenerate_cards(self):

        history = RegenHistory(self.fs)
        files = self.get_math_files(history)
        if files is None or len(files) == 0:
            print("No files to regenerate.")
            return

        for file in files:
            file.regenerate_cards()
            history.data[str(file.path)] = int(time.time())

        history.write()
        print("Regenerated cards.")
