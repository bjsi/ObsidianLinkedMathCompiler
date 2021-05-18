import hashlib
import os
from const import MATH_FOLDER_REL, HISTORY_DATA_FN, CLOZE_DATA_FN


class FileSystem:

    root: str
    sm_collection_root: str
    obsidian_vault_root: str
    obsidian_vault_name: str

    def __init__(self, sm_collection_root: str, obsidian_vault_root: str):
        self.sm_collection_root = sm_collection_root
        self.obsidian_vault_root = obsidian_vault_root
        self.obsidian_vault_name = os.path.basename(obsidian_vault_root)

    def math_folder(self):
        return os.path.join(self.sm_collection_root, MATH_FOLDER_REL)

    def regen_history_file(self):
        return os.path.join(self.math_folder(), HISTORY_DATA_FN)

    @staticmethod
    def get_path_hash(file: str):
        return hashlib.sha1(file.encode()).hexdigest()[:15]
