import os
from pathlib import Path

import markdown
import mdx_mathjax
import typing as T
from cloze import Cloze
import re
from collections import defaultdict

from filesystem import FileSystem
from mathsnippet import MathSnippet
from bs4 import BeautifulSoup
import datetime as dt
from const import MATHJAX_REGEX, CLOZE_TAG_REGEX, BLOCK_REF_HASH_REGEX, BLOCK_REF_REGEX, IMAGES_FOLDER


class MathFile:

    fs: FileSystem
    path: Path
    filepath_hash: str
    mdProcessor = markdown.Markdown(extensions=[mdx_mathjax.MathJaxExtension()])

    def __init__(self, fs: FileSystem, path: Path):
        self.fs = fs
        self.path = path
        self.filepath_hash = self.fs.get_path_hash(str(path))

    @staticmethod
    def find_mathjax_snippet(html: str):
        return re.search(MATHJAX_REGEX, html)

    @staticmethod
    def replace(orig: str, start: int, end: int, replacement: str):
        return orig[0:start] + replacement + orig[end:]

    def convert_math_to_images(self, html: str):
        snippet = self.find_mathjax_snippet(html)
        while snippet is not None:
            image_folder = os.path.join(self.fs.math_folder(), self.filepath_hash, IMAGES_FOLDER)
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)

            s = MathSnippet(image_folder, snippet)
            s.generate_image()
            html = self.replace(html, s.match.start(), s.match.end(), s.img_tag())
            snippet = self.find_mathjax_snippet(html)

        return html

    @staticmethod
    def create_cloze_span(soup):
        cloze_span = soup.new_tag("span")
        cloze_span["class"] = "cloze"
        cloze_span.string = "[...]"
        return cloze_span

    def create_cloze_cards(self, html: str):
        clozes = []
        soup = BeautifulSoup(html, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        for tag in c_tags:
            answer = tag.decode_contents()
            span = self.create_cloze_span(soup)
            tag.replace_with(span)
            question = str(soup)
            cloze = Cloze(answer, question, self.fs, tag, str(self.path), soup)
            cloze.save_question()
            cloze.save_answer()
            cloze.save_metadata()
            clozes.append(cloze)
            span.replace_with(tag)

        return clozes

    @staticmethod
    def remove_block_ref_hashes(md: str):
        return re.sub(BLOCK_REF_HASH_REGEX, lambda x: x.group(1), md)

    def get_blockref_text(self, fp: str, ref_hash: str) -> str:
        try:
            with open(fp) as f:
                text = f.read()
                block = re.search(r"(.+)( \^" + ref_hash + ")", text).group(1).rstrip()
                return self.add_data_path_to_clozes(block, fp)
        except Exception as e:
            print(f"Failed to get blockref text for hash: {ref_hash} in file: {fp} with exception {e}")
            return ""

    def process_blockref_match(self, mobj):
        file = mobj.group(1)
        ref_hash = mobj.group(2)
        if file is None or ref_hash is None:
            print("Failed to process blockref match because file or hash group were None.")
            return ""
        return self.get_blockref_text(os.path.join(self.fs.obsidian_vault_root, file), ref_hash)

    def replace_blockrefs_with_text(self, md: str):
        return re.sub(BLOCK_REF_REGEX, lambda x: self.process_blockref_match(x), md)

    @staticmethod
    def update_original_md(clozes: T.List[Cloze], md) -> str:
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        if len(c_tags) != len(clozes):
            print("Warning: when updating original md the number of clozes was different.")

        for tag, cloze in zip(c_tags, clozes):
            tag.attrs.clear()
            tag.name = "c" + os.path.basename(cloze.cloze_folder)

        return str(soup)

    def clear_old_images(self):
        image_folder = os.path.join(self.fs.math_folder(), self.filepath_hash, IMAGES_FOLDER)
        if not os.path.exists(image_folder):
            return

        files = os.listdir(image_folder)
        for item in files:
            if item.endswith(".jpg"):
                os.remove(os.path.join(image_folder, item))

    @staticmethod
    def has_clozes(md: str):
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        return c_tags is not None and len(c_tags) > 0

    # TODO: add cleared folders to the deleted list
    def clear_unused_cloze_folders(self, md: str):
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))

        used = defaultdict(list)  # filepath: [cloze number, cloze number ...]
        for tag in c_tags:
            if tag.name == "c":
                continue

            cloze_num = re.search(CLOZE_TAG_REGEX, tag.name).group(1)
            original_file = tag["data-path"]

            if original_file is None or cloze_num is None:
                print("Failed to remove unused folder: data-path or folder num is None.")

            used[original_file].append(cloze_num)

        parent_note_folder = self.fs.get_note_folder(str(self.path))
        for original_file, folder_nums in used.items():
            folder_path = os.path.join(parent_note_folder, self.fs.get_path_hash(original_file))
            cloze_folders = next(os.walk(folder_path))[1]
            for cloze_folder in cloze_folders:
                if cloze_folder not in folder_nums:
                    full_path = os.path.join(folder_path, original_file)
                    print(f"Removing unused cloze folder: {full_path}")
                    os.remove(full_path)

    def regenerate_cards(self):
        start = dt.datetime.now()
        original_md = self.read()

        original_md = self.add_data_path_to_clozes(original_md, str(self.path))
        converted_md = self.replace_blockrefs_with_text(original_md)
        converted_md = self.remove_block_ref_hashes(converted_md)

        if not self.has_clozes(converted_md):
            print(f"{self.path} does not contain any clozes. Returning early.")
            return

        self.clear_unused_cloze_folders(converted_md)

        html = self.mdProcessor.convert(converted_md)
        self.clear_old_images()
        html = self.convert_math_to_images(html)

        clozes = self.create_cloze_cards(html)

        updated_md = self.update_original_md([c for c in clozes if c.tag["data-path"] == str(self.path)], original_md)
        self.write(updated_md)
        end = dt.datetime.now()
        print(f"Finished processing: {self.path} in {end - start}")

    def read(self) -> str:
        try:
            with open(self.path) as fobj:
                return fobj.read()
        except Exception as e:
            print(f"Failed to read MathFile with exception {e}")

    def write(self, data: str):
        try:
            with open(self.path, 'w') as fobj:
                fobj.write(data)
        except Exception as e:
            print(f"Failed to write to MathFile with exception {e}")

    @staticmethod
    def add_data_path_to_clozes(md: str, file_path: str):
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        for tag in c_tags:
            tag["data-path"] = file_path
        return str(soup)
