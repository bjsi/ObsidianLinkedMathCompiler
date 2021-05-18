import os
from pathlib import Path

import markdown
import mdx_mathjax
import typing as T
from cloze import Cloze
import re

from filesystem import FileSystem
from mathsnippet import MathSnippet
from bs4 import BeautifulSoup
import datetime as dt
from const import MATHJAX_REGEX, CLOZE_TAG_REGEX, BLOCK_REF_HASH_REGEX, BLOCK_REF_REGEX, MATH_FOLDER_REL


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
            note_folder = os.path.join(self.fs.sm_collection_root, MATH_FOLDER_REL, self.filepath_hash)
            if not os.path.exists(note_folder):
                os.mkdir(note_folder)

            s = MathSnippet(note_folder, snippet)
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
            cloze = Cloze(answer, question, self.fs, tag, str(self.path))
            cloze.save_question()
            cloze.save_answer()
            cloze.save_metadata()
            clozes.append(cloze)
            span.replace_with(tag)

        return clozes

    @staticmethod
    def __remove_block_ref_hashes(md: str):
        return re.sub(BLOCK_REF_HASH_REGEX, lambda x: x.group(1), md)

    @staticmethod
    def __get_blockref_text(fp: str, ref_hash: str) -> str:
        with open(fp) as fobj:
            text = fobj.read()
            # Finds the block with the specified hash
            return re.search(r"(.+)( \^" + ref_hash + ")", text).group(1).rstrip()

    def __process_blockref_match(self, mobj):
        file = mobj.group(1)
        ref_hash = mobj.group(2)
        new_text = self.__get_blockref_text(os.path.join(self.fs.obsidian_vault_root, file), ref_hash)
        return new_text

    def __update_block_refs(self, md: str):
        return re.sub(BLOCK_REF_REGEX, lambda x: self.__process_blockref_match(x), md)

    @staticmethod
    def update_original_md(clozes: T.List[Cloze], md) -> str:
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        for tag, cloze in zip(c_tags, clozes):
            tag.name = "c" + os.path.basename(cloze.cloze_folder)
            tag.attrs.clear()
        return str(soup)

    def clear_old_images(self):
        note_folder = os.path.join(self.fs.math_folder(), self.filepath_hash)
        if not os.path.exists(note_folder):
            return

        files = os.listdir(note_folder)
        for item in files:
            if item.endswith(".jpg"):
                os.remove(os.path.join(note_folder, item))

    def has_clozes(self, md: str):
        soup = BeautifulSoup(md)
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        return c_tags is not None

    def regenerate_cards(self):
        start = dt.datetime.now()
        original_md = self.read()

        if not self.has_clozes(original_md):
            return

        original_md = self.add_attr_to_original_clozes(original_md)

        converted_md = self.__update_block_refs(original_md)
        converted_md = self.__remove_block_ref_hashes(original_md)

        html = self.mdProcessor.convert(converted_md)
        self.clear_old_images()
        html = self.convert_math_to_images(html)

        clozes = self.create_cloze_cards(html)

        updated_md = self.update_original_md([c for c in clozes if c.tag.get("og") == "true"], original_md)
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

    def add_attr_to_original_clozes(self, md: str):
        soup = BeautifulSoup(md, features="html.parser")
        c_tags = soup.findAll(lambda x: re.search(CLOZE_TAG_REGEX, x.name))
        for tag in c_tags:
            tag["og"] = "true"

        return str(soup)
