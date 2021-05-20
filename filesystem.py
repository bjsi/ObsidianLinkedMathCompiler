import hashlib
import os
from const import MATH_FOLDER_REL, HISTORY_DATA_FN, INCLUDED_BLOCKS_FOLDER, IMAGES_FOLDER, DELETED_DATA_FN


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

    def get_history_file(self):
        return os.path.join(self.math_folder(), HISTORY_DATA_FN)

    def get_note_folder(self, note_file_path: str):
        return os.path.join(self.math_folder(), self.get_path_hash(note_file_path))

    def get_deleted_file(self):
        return os.path.join(self.math_folder(), DELETED_DATA_FN)

    @staticmethod
    def get_images_folder(note_folder: str):
        return os.path.join(note_folder, IMAGES_FOLDER)

    @staticmethod
    def get_included_blocks_folder(note_folder: str):
        return os.path.join(note_folder, INCLUDED_BLOCKS_FOLDER)

    @staticmethod
    def get_path_hash(file: str):
        return hashlib.sha1(file.encode()).hexdigest()[:15]