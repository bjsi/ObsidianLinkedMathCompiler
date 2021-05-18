import json
import os
import typing as T
from pathlib import Path
import re

import bs4
import frontmatter

from const import QUESTION_HTML_FN, ANSWER_HTML_FN, CLOZE_DATA_FN, CLOZE_TAG_REGEX
from filesystem import FileSystem
from references import References


class Cloze:

    tag: bs4.Tag
    question_path: str
    answer_path: str
    folder_path: str
    note_folder: str
    imported: bool = False
    references: References
    note_filepath: str
    fs: FileSystem

    def __init__(self, answer_content: str, question_content: str, fs: FileSystem, tag: bs4.Tag, note_filepath: str):
        self.answer_content = answer_content
        self.question_content = question_content
        self.fs = fs
        self.note_folder = fs.get_path_hash(note_filepath)
        self.note_filepath = note_filepath
        self.tag = tag

        match = re.search(CLOZE_TAG_REGEX, tag.name)
        folder_num = match.group(1)
        self.cloze_folder = self.find_or_create_folder(folder_num)

        meta = self.read_metadata()
        self.imported = meta.get("imported", False)

        item_was_deleted = False
        qpath = meta.get("question_path")
        if (not qpath) or \
                (self.imported and not os.path.exists(qpath)):  # item was deleted
            item_was_deleted = True
            qpath = os.path.join(self.cloze_folder, QUESTION_HTML_FN)
        self.question_path = qpath

        apath = meta.get("answer_path")
        if (not apath) or \
                (self.imported and not os.path.exists(apath)):  # item was deleted
            item_was_deleted = True
            apath = os.path.join(self.cloze_folder, ANSWER_HTML_FN)
        self.answer_path = apath

        if item_was_deleted:
            self.imported = False

        self.create_references()

    def read_metadata(self):
        try:
            path = os.path.join(self.cloze_folder, CLOZE_DATA_FN)
            with open(path) as f:
                return json.loads(f.read())
        except Exception:
            return {}

    def find_or_create_folder(self, folder_num: str):
        note_folder = os.path.join(self.fs.math_folder(), self.note_folder)
        if folder_num:
            return os.path.join(note_folder, folder_num)

        subdirs = next(os.walk(note_folder))[1]
        max_num = max([int(x) for x in subdirs], default=0)
        return os.path.join(note_folder, str(max_num + 1))

    def create_references(self):
        self.references = References()
        metadata, content = frontmatter.parse(self.note_filepath)
        self.references.Link = "obsidian://open?path=" + self.note_filepath
        title = metadata.get("title")
        if not title:
            rel_path = str(Path(self.note_filepath)).replace(str(Path(self.fs.obsidian_vault_root)), "")
            split = [seg.rstrip(".md") for seg in rel_path.split("\\") if seg]
            title = ": ".join(split)

        self.references.Title = title
        self.references.Source = "Obsidian Vault: " + self.fs.obsidian_vault_name

    def create_folder(self):
        if not os.path.exists(self.cloze_folder):
            os.mkdir(self.cloze_folder)

    def save_answer(self):
        self.create_folder()
        try:
            with open(self.answer_path, "w") as fobj:
                fobj.write(self.answer_content)
        except Exception as e:
            print(f"Failed to save answer to {self.answer_path} with exception {e}")

    def save_question(self):
        self.create_folder()
        try:
            with open(self.question_path, "w") as fobj:
                fobj.write(self.question_content)
        except Exception as e:
            print(f"Failed to save question to {self.question_path} with exception {e}")

    def save_metadata(self):
        self.create_folder()
        data_file = os.path.join(self.cloze_folder, CLOZE_DATA_FN)
        try:
            with open(data_file, "w") as fobj:
                fobj.write(json.dumps(self.to_dict()))
        except Exception as e:
            print(f"Failed to save metadata to {data_file} with exception {e}.")

    def to_dict(self):
        return {
            "imported": self.imported,
            "question_path": self.question_path,
            "answer_path": self.answer_path,
            "folder": self.cloze_folder,
            "references": self.references.to_dict(),
        }
