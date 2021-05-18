import os
import re
import uuid

import imgkit
from PIL import Image, ImageChops


class MathSnippet:

    match: re.Match
    image_path: str
    note_folder: str

    def __init__(self, note_folder: str, match: re.Match):
        self.match = match
        self.note_folder = note_folder

    def img_tag(self):
        return f"<img src='file:///{self.image_path}'>"

    @staticmethod
    def trim(im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        # Bounding box given as a 4-tuple defining the left, upper, right, and lower pixel coordinates.
        # If the image is completely empty, this method returns None.
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    def generate_image(self):
        html = f"""
        <html>
          <head>
          <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-AMS_HTML"></script>
          <script type="text/javascript">
            MathJax.Hub.Config({{
                "tex2jax": {{ inlineMath: [ [ '$', '$' ] ] }},
                "processEscapes": "true",
                "messageStyle": "none",
            }});
          </script>
          </head>
          <body>
          {self.match.group(0)}
          </body>
        </html>
        """
        options = {
            'quality': 100,
            'zoom': 2,
            'log-level': "none",
            'javascript-delay': 500,
        }
        name = uuid.uuid4().hex + ".jpg"
        self.image_path = os.path.join(self.note_folder, name)
        imgkit.from_string(html, self.image_path, options=options)
        bg = Image.open(self.image_path)  # The image to be cropped
        new_im = self.trim(bg)
        new_im.save(self.image_path)
