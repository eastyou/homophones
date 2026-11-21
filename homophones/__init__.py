"""homophones：英语同音词查询、词义辨析与可打印练习页。"""

from __future__ import annotations

__version__ = "0.1.0"

from .cli import main
from .model import (
    HomophoneGroup,
    all_groups,
    find_group,
    match_items,
    meaning,
    normalize,
    quiz_items,
)
from .render import group_html, match_html, quiz_html

__all__ = [
    "__version__",
    "HomophoneGroup",
    "all_groups",
    "find_group",
    "normalize",
    "meaning",
    "quiz_items",
    "match_items",
    "quiz_html",
    "match_html",
    "group_html",
    "main",
]
