"""cli.py 的单元测试。"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from typing import Sequence, Tuple, cast

from homophones import __version__, all_groups
from homophones.cli import _ensure_utf8_console, _write_file, main


def _run_cli(argv: Sequence[str]) -> Tuple[int, str, str]:
    """执行命令行并返回 (退出码, 标准输出, 标准错误)。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        with contextlib.redirect_stderr(stderr):
            code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class CliTestCase(unittest.TestCase):
    """提供捕获标准输出的辅助方法。"""

    def run_cli(self, argv: Sequence[str]) -> Tuple[int, str, str]:
        """执行命令行并返回 (退出码, 标准输出, 标准错误)。"""
        return _run_cli(argv)


class BasicCliTests(CliTestCase):
    """帮助、版本与参数校验。"""

    def test_help_exits_zero(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as context:
                main(["--help"])
        self.assertEqual(context.exception.code, 0)
        self.assertIn("homophones", stdout.getvalue())

    def test_version_exits_zero(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as context:
                main(["--version"])
        self.assertEqual(context.exception.code, 0)
        self.assertIn(__version__, stdout.getvalue())

    def test_no_args_returns_two(self) -> None:
        code, stdout, _ = self.run_cli([])
        self.assertEqual(code, 2)
        self.assertIn("usage", stdout)

    def test_unknown_subcommand_exits(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(["unknown"])
        self.assertEqual(context.exception.code, 2)

    def test_main_rejects_string_argv(self) -> None:
        code, _, stderr = self.run_cli(cast(Sequence[str], "find sea"))
        self.assertEqual(code, 2)
        self.assertIn("错误：命令行参数必须是字符串序列", stderr)

    def test_main_rejects_non_sequence_argv(self) -> None:
        code, _, stderr = self.run_cli(cast(Sequence[str], 123))
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)


class FindAndMeaningTests(CliTestCase):
    """find 与 meaning 子命令。"""

    def test_find_known_word(self) -> None:
        code, stdout, stderr = self.run_cli(["find", "sea"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("同音组：sea / see", stdout)
        self.assertIn("sea：大海；海洋", stdout)
        self.assertIn("答案：sea", stdout)

    def test_find_is_case_insensitive(self) -> None:
        code, stdout, _ = self.run_cli(["find", "  SEE "])
        self.assertEqual(code, 0)
        self.assertIn("同音组：sea / see", stdout)

    def test_find_unknown_word_returns_two(self) -> None:
        code, stdout, stderr = self.run_cli(["find", "zebra"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("错误：未知单词：zebra", stderr)

    def test_find_empty_word_returns_two(self) -> None:
        code, _, stderr = self.run_cli(["find", ""])
        self.assertEqual(code, 2)
        self.assertIn("错误：单词不能为空", stderr)

    def test_find_requires_word(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["find"])
        self.assertEqual(context.exception.code, 2)

    def test_meaning_known_word(self) -> None:
        code, stdout, _ = self.run_cli(["meaning", "Pear"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "pear：梨")

    def test_meaning_unknown_word_returns_two(self) -> None:
        code, _, stderr = self.run_cli(["meaning", "zebra"])
        self.assertEqual(code, 2)
        self.assertIn("错误：未知单词：zebra", stderr)


class QuizCliTests(CliTestCase):
    """quiz 子命令。"""

    def test_quiz_prints_questions(self) -> None:
        code, stdout, _ = self.run_cli(["quiz", "--count", "3", "--seed", "5"])
        self.assertEqual(code, 0)
        self.assertIn("1. ", stdout)
        self.assertIn("候选：", stdout)
        self.assertIn("提示：", stdout)

    def test_quiz_default_count(self) -> None:
        code, stdout, _ = self.run_cli(["quiz", "--seed", "1"])
        self.assertEqual(code, 0)
        self.assertIn("10. ", stdout)
        self.assertNotIn("11. ", stdout)

    def test_quiz_same_seed_same_output(self) -> None:
        first = self.run_cli(["quiz", "--count", "6", "--seed", "9"])
        second = self.run_cli(["quiz", "--count", "6", "--seed", "9"])
        self.assertEqual(first, second)

    def test_quiz_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "quiz.html")
            code, stdout, _ = self.run_cli(
                ["quiz", "--count", "5", "--seed", "2", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % path, stdout)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("答案：", content)
            self.assertIn("同音词填空练习", content)

    def test_quiz_count_out_of_range(self) -> None:
        code, _, stderr = self.run_cli(["quiz", "--count", "0"])
        self.assertEqual(code, 2)
        self.assertIn("错误：题目数量必须在 1 到 40 之间", stderr)

    def test_quiz_non_numeric_count_exits(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["quiz", "--count", "abc"])
        self.assertEqual(context.exception.code, 2)


class MatchCliTests(CliTestCase):
    """match 子命令。"""

    def test_match_prints_pairs(self) -> None:
        code, stdout, _ = self.run_cli(["match", "--count", "4", "--seed", "3"])
        self.assertEqual(code, 0)
        self.assertIn("1. ", stdout)
        self.assertIn("——", stdout)

    def test_match_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "match.html")
            code, stdout, _ = self.run_cli(
                ["match", "--count", "6", "--seed", "4", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % path, stdout)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("配对练习", content)
            self.assertIn("作答区", content)

    def test_match_count_out_of_range(self) -> None:
        code, _, stderr = self.run_cli(["match", "--count", "25"])
        self.assertEqual(code, 2)
        self.assertIn("错误：配对数量必须在 1 到 20 之间", stderr)


class GroupsCliTests(CliTestCase):
    """groups 子命令。"""

    def test_groups_prints_summary(self) -> None:
        code, stdout, _ = self.run_cli(["groups"])
        self.assertEqual(code, 0)
        self.assertIn("共 %d 组同音词：" % len(all_groups()), stdout)
        self.assertIn("sea / see", stdout)

    def test_groups_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "groups.html")
            code, stdout, _ = self.run_cli(["groups", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % path, stdout)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("同音词速查表", content)
            self.assertIn("<table>", content)

    def test_output_to_directory_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, _, stderr = self.run_cli(["groups", "-o", directory])
            self.assertEqual(code, 2)
            self.assertIn("错误：写入文件失败", stderr)


class WriteFileTests(unittest.TestCase):
    """_write_file 与 UTF-8 控制台测试。"""

    def test_write_file_rejects_empty_path(self) -> None:
        with self.assertRaises(ValueError):
            _write_file("   ", "<html></html>")

    def test_write_file_rejects_non_string_path(self) -> None:
        with self.assertRaises(TypeError):
            _write_file(cast(str, 123), "<html></html>")

    def test_write_file_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "nested", "docs", "page.html")
            _write_file(path, "<html>中文内容</html>")
            self.assertTrue(os.path.isfile(path))
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "<html>中文内容</html>")

    def test_write_file_handles_os_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _write_file(directory, "<html></html>")

    def test_ensure_utf8_console_handles_missing_reconfigure(self) -> None:
        original = sys.stdout
        sys.stdout = io.StringIO()
        try:
            _ensure_utf8_console()
        finally:
            sys.stdout = original

    def test_ensure_utf8_console_swallows_errors(self) -> None:
        class FailingStream:
            def reconfigure(
                self, encoding: str = "utf-8", errors: str = "replace"
            ) -> None:
                raise OSError("不支持重新配置")

            def write(self, text: str) -> int:
                return len(text)

        original_out, original_err = sys.stdout, sys.stderr
        sys.stdout = cast(io.TextIOBase, FailingStream())
        sys.stderr = cast(io.TextIOBase, FailingStream())
        try:
            _ensure_utf8_console()
        finally:
            sys.stdout = original_out
            sys.stderr = original_err

    def test_generated_html_is_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "quiz.html")
            code, _, _ = _run_cli(
                ["quiz", "--count", "2", "--seed", "8", "-o", path]
            )
            self.assertEqual(code, 0)
            with open(path, "rb") as handle:
                raw = handle.read()
            text = raw.decode("utf-8")
            self.assertIn("同音词", text)
            self.assertIn("提示：", text)


if __name__ == "__main__":
    unittest.main()
