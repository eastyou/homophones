"""render.py 的单元测试。"""

from __future__ import annotations

import unittest
from typing import Dict, List, Sequence, Tuple, cast

from homophones import HomophoneGroup
from homophones.model import all_groups, match_items, quiz_items
from homophones.render import group_html, match_html, quiz_html


def _item(
    sentence: str = "We went to the ____ for a swim.",
    hint: str = "指大海（名词）",
    options: Tuple[str, ...] = ("sea", "see"),
    answer: str = "sea",
) -> Dict[str, object]:
    """构造一条测试用题目。"""
    return {
        "number": 1,
        "sentence": sentence,
        "hint": hint,
        "options": options,
        "answer": answer,
        "meanings": {"sea": "大海", "see": "看见"},
    }


class QuizHtmlTests(unittest.TestCase):
    """quiz_html 测试。"""

    def test_quiz_html_basic_structure(self) -> None:
        page = quiz_html([_item()], "同音词练习")
        self.assertIsInstance(page, str)
        self.assertTrue(page.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', page)
        self.assertIn('<meta charset="utf-8">', page)
        self.assertIn("</html>", page)

    def test_quiz_html_has_a4_and_print_styles(self) -> None:
        page = quiz_html([_item()], "练习")
        self.assertIn("@page", page)
        self.assertIn("size: A4", page)
        self.assertIn("@media print", page)

    def test_quiz_html_renders_items(self) -> None:
        items = quiz_items(6, seed=1)
        page = quiz_html(items, "练习")
        self.assertEqual(page.count('class="card"'), 6)
        for item in items:
            self.assertIn(cast(str, item["hint"]), page)

    def test_quiz_html_marks_blank(self) -> None:
        page = quiz_html([_item()], "练习")
        self.assertIn('class="blank"', page)
        self.assertIn("____", page)

    def test_quiz_html_renders_options(self) -> None:
        page = quiz_html([_item(options=("sea", "see", "si"))], "练习")
        self.assertIn(">sea</li>", page)
        self.assertIn(">see</li>", page)
        self.assertIn(">si</li>", page)

    def test_quiz_html_without_answers(self) -> None:
        page = quiz_html([_item()], "练习")
        self.assertNotIn("答案：", page)

    def test_quiz_html_with_answers(self) -> None:
        page = quiz_html([_item()], "练习", with_answers=True)
        self.assertIn("答案：sea", page)

    def test_quiz_html_escapes_title(self) -> None:
        page = quiz_html([_item()], '<script>alert("x")</script>')
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert", page)

    def test_quiz_html_escapes_content(self) -> None:
        item = _item(sentence="Fill ____ <i>now</i>.", hint="提示 <b>重点</b>")
        page = quiz_html([item], "练习")
        self.assertIn("&lt;i&gt;now&lt;/i&gt;", page)
        self.assertIn("&lt;b&gt;重点&lt;/b&gt;", page)
        self.assertNotIn("<i>now</i>", page)

    def test_quiz_html_empty_items(self) -> None:
        page = quiz_html([], "练习")
        self.assertIn("暂无题目。", page)

    def test_quiz_html_blank_is_not_replaced_twice(self) -> None:
        page = quiz_html([_item(sentence="A ____ and ____ here.")], "练习")
        self.assertIn("____", page)

    def test_quiz_html_title_type_error(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html([_item()], cast(str, 123))

    def test_quiz_html_empty_title(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_item()], "   ")

    def test_quiz_html_items_type_error(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html(cast(Sequence[Dict[str, object]], 123), "练习")

    def test_quiz_html_string_items_error(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html(cast(Sequence[Dict[str, object]], "abc"), "练习")

    def test_quiz_html_with_answers_type_error(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html([_item()], "练习", with_answers=cast(bool, "yes"))

    def test_quiz_html_item_must_be_dict(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html(cast(List[Dict[str, object]], ["bad"]), "练习")

    def test_quiz_html_requires_hint(self) -> None:
        item = {"sentence": "A ____ here.", "options": ("a", "b"), "answer": "a"}
        with self.assertRaises(ValueError):
            quiz_html([cast(Dict[str, object], item)], "练习")

    def test_quiz_html_requires_sentence(self) -> None:
        item = {"hint": "提示", "options": ("a", "b"), "answer": "a"}
        with self.assertRaises(ValueError):
            quiz_html([cast(Dict[str, object], item)], "练习")

    def test_quiz_html_answer_must_be_option(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_item(answer="si")], "练习")

    def test_quiz_html_option_count_checked(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_item(options=("a", "b", "c", "d"))], "练习")

    def test_quiz_html_options_must_not_be_string(self) -> None:
        item = cast(Dict[str, object], _item())
        item["options"] = "sea"
        with self.assertRaises(ValueError):
            quiz_html([item], "练习")


class MatchHtmlTests(unittest.TestCase):
    """match_html 测试。"""

    def test_match_html_basic_structure(self) -> None:
        page = match_html([("sea", "大海"), ("see", "看见")], "配对练习")
        self.assertTrue(page.startswith("<!DOCTYPE html>"))
        self.assertIn("配对练习", page)
        self.assertIn("作答区", page)
        self.assertIn("1. ____", page)
        self.assertIn("2. ____", page)

    def test_match_html_renders_words_and_meanings(self) -> None:
        page = match_html([("sea", "大海"), ("see", "看见")], "配对练习")
        self.assertIn("<li>sea</li>", page)
        self.assertIn("<li>see</li>", page)
        self.assertIn("<li>大海</li>", page)
        self.assertIn("<li>看见</li>", page)

    def test_match_html_meanings_are_sorted(self) -> None:
        page = match_html([("sea", "看见"), ("see", "大海")], "配对练习")
        self.assertLess(page.index("大海"), page.index("看见"))

    def test_match_html_uses_match_items(self) -> None:
        pairs = match_items(5, seed=3)
        page = match_html(pairs, "配对练习")
        for word, explanation in pairs:
            self.assertIn("<li>%s</li>" % word, page)
            self.assertIn("<li>%s</li>" % explanation, page)

    def test_match_html_has_print_styles(self) -> None:
        page = match_html([("sea", "大海")], "配对练习")
        self.assertIn("@media print", page)
        self.assertIn("size: A4", page)

    def test_match_html_empty_pairs(self) -> None:
        page = match_html([], "配对练习")
        self.assertIn("暂无配对数据。", page)

    def test_match_html_escapes_text(self) -> None:
        page = match_html([("sea", "<b>大海</b>")], "<标题>")
        self.assertIn("&lt;b&gt;大海&lt;/b&gt;", page)
        self.assertIn("&lt;标题&gt;", page)

    def test_match_html_pairs_type_error(self) -> None:
        with self.assertRaises(TypeError):
            match_html(cast(Sequence[Tuple[str, str]], 42), "配对练习")

    def test_match_html_invalid_pair_shape(self) -> None:
        with self.assertRaises(TypeError):
            match_html(cast(Sequence[Tuple[str, str]], [("sea",)]), "配对练习")

    def test_match_html_invalid_word(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("  ", "大海")], "配对练习")

    def test_match_html_invalid_meaning(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("sea", "  ")], "配对练习")

    def test_match_html_title_type_error(self) -> None:
        with self.assertRaises(TypeError):
            match_html([("sea", "大海")], cast(str, None))


class GroupHtmlTests(unittest.TestCase):
    """group_html 测试。"""

    def test_group_html_basic_structure(self) -> None:
        page = group_html(all_groups()[:3], "同音词速查表")
        self.assertTrue(page.startswith("<!DOCTYPE html>"))
        self.assertIn("同音词速查表", page)
        self.assertIn("<table>", page)
        self.assertIn("<tbody>", page)

    def test_group_html_renders_all_groups(self) -> None:
        groups = all_groups()
        page = group_html(groups, "速查表")
        total_words = sum(len(group.words) for group in groups)
        self.assertEqual(page.count("<strong>"), total_words)
        self.assertIn("sea", page)
        self.assertIn("大海；海洋", page)

    def test_group_html_has_print_styles(self) -> None:
        page = group_html(all_groups()[:1], "速查表")
        self.assertIn("@page", page)
        self.assertIn("@media print", page)

    def test_group_html_empty_groups(self) -> None:
        page = group_html([], "速查表")
        self.assertIn("暂无同音组数据。", page)

    def test_group_html_escapes_text(self) -> None:
        group = HomophoneGroup(
            words=("sea", "see"),
            meanings={"sea": "大<海>", "see": "看见"},
            sentence="A ____ here.",
            answer="sea",
            hint="提示",
        )
        page = group_html([group], "速查表")
        self.assertIn("大&lt;海&gt;", page)

    def test_group_html_rejects_non_group_items(self) -> None:
        with self.assertRaises(TypeError):
            group_html(cast(Sequence[HomophoneGroup], ["sea"]), "速查表")

    def test_group_html_groups_type_error(self) -> None:
        with self.assertRaises(TypeError):
            group_html(cast(Sequence[HomophoneGroup], 3), "速查表")

    def test_group_html_empty_title(self) -> None:
        with self.assertRaises(ValueError):
            group_html([], "")


if __name__ == "__main__":
    unittest.main()
