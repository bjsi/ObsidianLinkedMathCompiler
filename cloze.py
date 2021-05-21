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
    parent_note_folder: str
    original_note_folder: str
    original_note_path: str
    parent_note_filepath: str
    imported: bool = False
    references: References
    fs: FileSystem
    note_soup: bs4.BeautifulSoup

    def __init__(self, answer_content: str, question_content: str, fs: FileSystem, tag: bs4.Tag, parent_note_filepath: str, note_soup: bs4.BeautifulSoup):
        self.answer_content = answer_content
        self.question_content = question_content
        self.fs = fs
        self.tag = tag
        self.note_soup = note_soup
        self.parent_note_filepath = parent_note_filepath

        self.original_note_path = tag["data-path"]
        self.parent_note_folder = os.path.join(self.fs.math_folder(), self.fs.get_path_hash(parent_note_filepath))
        self.original_note_folder = os.path.join(self.parent_note_folder, self.fs.get_path_hash(self.original_note_path))

        self.cloze_folder = self.find_or_create_folder(self.get_folder_num(tag))
        self.tag.name = "c" + os.path.basename(self.cloze_folder)

        meta = self.read_metadata()
        self.imported = meta.get("imported", False)

        item_was_deleted = False
        qpath = meta.get("question_path")
        apath = meta.get("answer_path")

        if self.item_deleted(qpath, apath):
            qpath = os.path.join(self.cloze_folder, QUESTION_HTML_FN)
            apath = os.path.join(self.cloze_folder, ANSWER_HTML_FN)

        self.question_path = qpath
        self.answer_path = apath

        if item_was_deleted:
            self.imported = False

        self.create_references()

    def item_deleted(self, qpath: str, apath: str):
        if not qpath or not apath:
            return True

        if self.imported and \
                (self.component_deleted(qpath) or self.component_deleted(apath)):
            return True

    @staticmethod
    def component_deleted(sm_component: str):
        try:
            with open(sm_component) as f:
                text = f.read()
                soup = bs4.BeautifulSoup(text, features="html.parser")
                found = soup.find("div", attrs={"obsidian-math": "true"})
                if found is None:
                    return True
                return False
        except Exception:
            return True

    def read_metadata(self):
        try:
            path = os.path.join(self.cloze_folder, CLOZE_DATA_FN)
            with open(path) as f:
                return json.loads(f.read())
        except Exception:
            return {}

    def find_or_create_folder(self, folder_num: str):
        if folder_num:
            return os.path.join(self.original_note_folder, folder_num)

        c_tags = self.note_soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        c_tags = [tag for tag in c_tags if tag["data-path"] == self.original_note_path]
        nums = [int(re.search(CLOZE_TAG_REGEX, tag.name).group(1)) for tag in c_tags if tag.name != "c"]
        n = 1
        while True:
            if n not in nums:
                return os.path.join(self.original_note_folder, str(n))
            n += 1

    def create_references(self):
        self.references = References()
        metadata, content = frontmatter.parse(self.parent_note_filepath)
        self.references.Link = "obsidian://open?path=" + self.parent_note_filepath
        title = metadata.get("title")
        if not title:
            rel_path = str(Path(self.parent_note_filepath)).replace(str(Path(self.fs.obsidian_vault_root)), "")
            split = [seg.rstrip(".md") for seg in rel_path.split("\\") if seg]
            title = ": ".join(split)

        self.references.Title = title
        self.references.Source = "Obsidian Vault: " + self.fs.obsidian_vault_name

    def create_folder(self):
        if not os.path.exists(self.cloze_folder):
            os.makedirs(self.cloze_folder)

    def save_answer(self):
        self.create_folder()
        try:
            with open(self.answer_path, "w") as fobj:
                fobj.write("<div obsidian-math='true'>Obsidian Math</div>" + self.answer_content)
        except Exception as e:
            print(f"Failed to save answer to {self.answer_path} with exception {e}")

    def save_question(self):
        self.create_folder()
        try:
            with open(self.question_path, "w") as fobj:
                fobj.write("<div obsidian-math='true'>Obsidian Math</div>" + self.question_content)
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

    @staticmethod
    def get_folder_num(tag):
        match = re.search(CLOZE_TAG_REGEX, tag.name)
        return match.group(1)
