"""命令行入口：查询同音组、查看释义、生成可打印练习页。"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Sequence, cast

from . import __version__
from .model import all_groups, find_group, match_items, meaning, normalize, quiz_items
from .render import group_html, match_html, quiz_html


def _ensure_utf8_console() -> None:
    """尽力把标准输出与标准错误切换为 UTF-8，失败时静默跳过。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            continue


def _write_file(path: str, content: str) -> None:
    """把 HTML 内容写入文件，失败时抛出中文 ``ValueError``。"""
    if not isinstance(path, str):
        raise TypeError("输出路径必须是字符串")
    if not path.strip():
        raise ValueError("输出路径不能为空")

    directory = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as exc:
        raise ValueError(
            "无法创建输出目录：%s（%s）" % (directory, exc.strerror or exc)
        ) from None

    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError(
            "写入文件失败：%s（%s）" % (path, exc.strerror or exc)
        ) from None


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="homophones",
        description="英语同音词：同音组查询、词义辨析与可打印练习页。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="homophones %s" % __version__,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    find_parser = subparsers.add_parser("find", help="查询单词所在的同音组")
    find_parser.add_argument("word", help="要查询的英文单词")

    meaning_parser = subparsers.add_parser("meaning", help="查看单词的中文释义")
    meaning_parser.add_argument("word", help="要查询的英文单词")

    quiz_parser = subparsers.add_parser("quiz", help="生成填空题练习页")
    quiz_parser.add_argument("--count", type=int, default=10, help="题目数量（1~40）")
    quiz_parser.add_argument("--seed", type=int, default=None, help="随机种子")
    quiz_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    match_parser = subparsers.add_parser("match", help="生成词义配对练习页")
    match_parser.add_argument("--count", type=int, default=8, help="配对数量（1~20）")
    match_parser.add_argument("--seed", type=int, default=None, help="随机种子")
    match_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    groups_parser = subparsers.add_parser("groups", help="输出同音组速查表")
    groups_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    return parser


def _run(args: argparse.Namespace) -> int:
    """按子命令执行并返回退出码。"""
    command = args.command

    if command == "find":
        group = find_group(args.word)
        print("同音组：%s" % " / ".join(group.words))
        for word in group.words:
            print("  %s：%s" % (word, group.meanings[word]))
        print("例句：%s" % group.sentence)
        print("答案：%s" % group.answer)
        print("提示：%s" % group.hint)
        return 0

    if command == "meaning":
        print("%s：%s" % (normalize(args.word), meaning(args.word)))
        return 0

    if command == "quiz":
        items = quiz_items(args.count, args.seed)
        if args.output:
            _write_file(args.output, quiz_html(items, "同音词填空练习", with_answers=True))
            print("已生成：%s" % args.output)
            return 0
        for item in items:
            options = cast(Sequence[str], item["options"])
            print("%s. %s" % (item["number"], item["sentence"]))
            print("   候选：%s" % " / ".join(options))
            print("   提示：%s" % item["hint"])
        return 0

    if command == "match":
        pairs = match_items(args.count, args.seed)
        if args.output:
            _write_file(args.output, match_html(pairs, "同音词配对练习"))
            print("已生成：%s" % args.output)
            return 0
        for number, (word, explanation) in enumerate(pairs, start=1):
            print("%d. %s —— %s" % (number, word, explanation))
        return 0

    if command == "groups":
        groups = all_groups()
        if args.output:
            _write_file(args.output, group_html(groups, "同音词速查表"))
            print("已生成：%s" % args.output)
            return 0
        rows: List[str] = []
        for group in groups:
            rows.append(" / ".join(group.words))
        print("共 %d 组同音词：" % len(rows))
        for row in rows:
            print("  %s" % row)
        return 0

    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，返回进程退出码（成功 0，参数错误 2）。"""
    _ensure_utf8_console()
    try:
        if argv is not None and (
            isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence)
        ):
            raise TypeError("命令行参数必须是字符串序列")
        parser = _build_parser()
        args = parser.parse_args(argv)
        if not getattr(args, "command", None):
            parser.print_help()
            return 2
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
