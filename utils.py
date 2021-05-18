import typing as T
from pathlib import Path


def get_files(path: str, ext: str, recurse: bool = False) -> T.Iterable[Path]:
    """
    yield files in path with suffix ext. Optionally, recurse directories.
    """

    path = Path(path).expanduser().resolve()

    if path.is_dir():
        for p in path.iterdir():
            if p.is_file() and p.suffix == ext:
                yield p
            elif p.is_dir():
                if recurse:
                    yield from get_files(p, ext, recurse)
    elif path.is_file():
        yield path
    else:
        raise FileNotFoundError(path)
