"""model.py 的单元测试。"""

from __future__ import annotations

import unittest
from typing import Dict, Optional, Tuple, cast

from homophones import (
    HomophoneGroup,
    __version__,
    all_groups,
    find_group,
    match_items,
    meaning,
    normalize,
    quiz_items,
)
from homophones.model import _validate_group


def _group(
    words: Tuple[str, ...] = ("sea", "see"),
    meanings: Optional[Dict[str, str]] = None,
    sentence: str = "We went to the ____ for a swim.",
    answer: str = "sea",
    hint: str = "指大海（名词）",
) -> HomophoneGroup:
    """构造一个便于修改的测试用同音组。"""
    if meanings is None:
        meanings = {"sea": "大海", "see": "看见"}
    return HomophoneGroup(
        words=words,
        meanings=meanings,
        sentence=sentence,
        answer=answer,
        hint=hint,
    )


class ModelDataTests(unittest.TestCase):
    """内置数据完整性测试。"""

    def test_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_all_groups_is_list_of_groups(self) -> None:
        groups = all_groups()
        self.assertIsInstance(groups, list)
        for group in groups:
            self.assertIsInstance(group, HomophoneGroup)

    def test_all_groups_has_enough_groups(self) -> None:
        self.assertGreaterEqual(len(all_groups()), 60)

    def test_all_groups_returns_new_list(self) -> None:
        first = all_groups()
        second = all_groups()
        self.assertIsNot(first, second)
        first.clear()
        self.assertGreaterEqual(len(all_groups()), 60)

    def test_group_word_arity(self) -> None:
        for group in all_groups():
            self.assertIsInstance(group.words, tuple)
            self.assertIn(len(group.words), (2, 3), group.words)

    def test_group_words_are_lowercase(self) -> None:
        for group in all_groups():
            for word in group.words:
                self.assertEqual(word, normalize(word), word)

    def test_group_words_unique_inside_group(self) -> None:
        for group in all_groups():
            self.assertEqual(len(set(group.words)), len(group.words), group.words)

    def test_words_unique_across_groups(self) -> None:
        seen: Dict[str, str] = {}
        for group in all_groups():
            for word in group.words:
                self.assertNotIn(word, seen)
                seen[word] = group.answer
        self.assertEqual(
            len(seen), sum(len(group.words) for group in all_groups())
        )

    def test_group_meanings_match_words(self) -> None:
        for group in all_groups():
            self.assertEqual(set(group.meanings.keys()), set(group.words))
            for word in group.words:
                self.assertTrue(group.meanings[word].strip(), word)

    def test_group_sentence_has_single_blank(self) -> None:
        for group in all_groups():
            self.assertEqual(group.sentence.count("____"), 1, group.sentence)
            self.assertGreater(len(group.sentence.strip()), 4)

    def test_group_answer_is_in_group(self) -> None:
        for group in all_groups():
            self.assertIn(normalize(group.answer), group.words)

    def test_group_hint_non_empty(self) -> None:
        for group in all_groups():
            self.assertIsInstance(group.hint, str)
            self.assertTrue(group.hint.strip())

    def test_every_group_can_be_queried(self) -> None:
        for group in all_groups():
            for word in group.words:
                self.assertIs(find_group(word), group)

    def test_quiz_source_groups_cover_all_words(self) -> None:
        words = [word for group in all_groups() for word in group.words]
        for word in words:
            self.assertTrue(meaning(word).strip())


class ValidateGroupTests(unittest.TestCase):
    """_validate_group 的异常分支测试。"""

    def test_validate_group_accepts_valid_group(self) -> None:
        _validate_group(_group())

    def test_validate_group_rejects_duplicate_words(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(words=("sea", "SEA")))

    def test_validate_group_rejects_missing_meaning(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(meanings={"sea": "大海"}))

    def test_validate_group_rejects_extra_meaning(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(
                _group(meanings={"sea": "大海", "see": "看见", "saw": "锯"})
            )

    def test_validate_group_rejects_answer_outside_group(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(answer="sea2"))

    def test_validate_group_rejects_sentence_without_blank(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(sentence="We went to the sea."))

    def test_validate_group_rejects_wrong_word_count(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(words=("sea",), meanings={"sea": "大海"}))

    def test_validate_group_rejects_non_string_word(self) -> None:
        group = HomophoneGroup(
            words=("sea", cast(str, 1)),
            meanings={"sea": "大海", "1": "一"},
            sentence="We went to the ____.",
            answer="sea",
            hint="提示",
        )
        with self.assertRaises(ValueError):
            _validate_group(group)

    def test_validate_group_rejects_empty_meaning(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(
                _group(meanings={"sea": "大海", "see": "   "})
            )

    def test_validate_group_rejects_bad_hint(self) -> None:
        with self.assertRaises(ValueError):
            _validate_group(_group(hint="   "))

    def test_validate_group_rejects_non_group(self) -> None:
        with self.assertRaises(TypeError):
            _validate_group(cast(HomophoneGroup, "sea / see"))


class NormalizeAndQueryTests(unittest.TestCase):
    """normalize / find_group / meaning 测试。"""

    def test_normalize_basic(self) -> None:
        self.assertEqual(normalize("sea"), "sea")

    def test_normalize_strips_and_casefolds(self) -> None:
        self.assertEqual(normalize("  See  "), "see")
        self.assertEqual(normalize("SEA"), "sea")

    def test_normalize_type_error(self) -> None:
        for value in (None, 1, 1.5, b"sea"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    normalize(cast(str, value))

    def test_find_group_known_word(self) -> None:
        group = find_group("sea")
        self.assertEqual(group.words, ("sea", "see"))

    def test_find_group_case_insensitive(self) -> None:
        self.assertIs(find_group("  SEE "), find_group("see"))

    def test_find_group_unknown_word(self) -> None:
        with self.assertRaises(ValueError):
            find_group("zebra")

    def test_find_group_empty_word(self) -> None:
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    find_group(value)

    def test_find_group_type_error(self) -> None:
        with self.assertRaises(TypeError):
            find_group(cast(str, 123))

    def test_meaning_known_word(self) -> None:
        self.assertEqual(meaning("See"), "看见；明白")
        self.assertEqual(meaning("pear"), "梨")

    def test_meaning_unknown_word(self) -> None:
        with self.assertRaises(ValueError):
            meaning("zebra")


class QuizItemsTests(unittest.TestCase):
    """quiz_items 测试。"""

    def test_quiz_items_structure(self) -> None:
        items = quiz_items(10, seed=5)
        self.assertEqual(len(items), 10)
        numbers = []
        for item in items:
            self.assertIsInstance(item, dict)
            self.assertIsInstance(item["sentence"], str)
            self.assertIn("____", cast(str, item["sentence"]))
            self.assertIsInstance(item["hint"], str)
            self.assertTrue(cast(str, item["hint"]).strip())
            self.assertIsInstance(item["options"], tuple)
            self.assertIsInstance(item["meanings"], dict)
            numbers.append(item["number"])
        self.assertEqual(numbers, list(range(1, 11)))

    def test_quiz_items_options_contain_answer(self) -> None:
        for item in quiz_items(20, seed=7):
            options = cast(Tuple[str, ...], item["options"])
            answer = cast(str, item["answer"])
            self.assertIn(len(options), (2, 3))
            self.assertEqual(len(set(options)), len(options))
            self.assertIn(answer, options)
            group = find_group(answer)
            self.assertEqual(set(options), set(group.words))

    def test_quiz_items_reproducible(self) -> None:
        first = quiz_items(12, seed=42)
        second = quiz_items(12, seed=42)
        self.assertEqual(
            [item["sentence"] for item in first],
            [item["sentence"] for item in second],
        )
        self.assertEqual(
            [item["options"] for item in first],
            [item["options"] for item in second],
        )

    def test_quiz_items_different_seed(self) -> None:
        first = quiz_items(10, seed=1)
        second = quiz_items(10, seed=2)
        self.assertNotEqual(
            [item["sentence"] for item in first],
            [item["sentence"] for item in second],
        )

    def test_quiz_items_without_seed(self) -> None:
        items = quiz_items(5)
        self.assertEqual(len(items), 5)

    def test_quiz_items_count_bounds(self) -> None:
        self.assertEqual(len(quiz_items(1, seed=3)), 1)
        self.assertEqual(len(quiz_items(40, seed=3)), 40)
        for count in (0, -1, 41):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    quiz_items(count, seed=3)

    def test_quiz_items_count_type_errors(self) -> None:
        for count in (True, False, "5", 3.0, None):
            with self.subTest(count=count):
                with self.assertRaises(TypeError):
                    quiz_items(cast(int, count), seed=1)

    def test_quiz_items_seed_type_errors(self) -> None:
        for seed in (True, "5", 1.5):
            with self.subTest(seed=seed):
                with self.assertRaises(TypeError):
                    quiz_items(3, seed=cast(int, seed))


class MatchItemsTests(unittest.TestCase):
    """match_items 测试。"""

    def test_match_items_structure(self) -> None:
        pairs = match_items(8, seed=11)
        self.assertEqual(len(pairs), 8)
        for pair in pairs:
            self.assertIsInstance(pair, tuple)
            self.assertEqual(len(pair), 2)
            word, explanation = pair
            self.assertIsInstance(word, str)
            self.assertIsInstance(explanation, str)
            self.assertTrue(explanation.strip())
            self.assertEqual(meaning(word), explanation)

    def test_match_items_words_unique(self) -> None:
        words = [word for word, _ in match_items(20, seed=2)]
        self.assertEqual(len(words), len(set(words)))

    def test_match_items_reproducible(self) -> None:
        self.assertEqual(match_items(6, seed=9), match_items(6, seed=9))

    def test_match_items_count_bounds(self) -> None:
        self.assertEqual(len(match_items(1, seed=4)), 1)
        self.assertEqual(len(match_items(20, seed=4)), 20)
        for count in (0, 21):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    match_items(count, seed=4)

    def test_match_items_count_type_errors(self) -> None:
        for count in (True, "3", 2.5):
            with self.subTest(count=count):
                with self.assertRaises(TypeError):
                    match_items(cast(int, count))

    def test_match_items_seed_type_errors(self) -> None:
        with self.assertRaises(TypeError):
            match_items(3, seed=cast(int, "seed"))


if __name__ == "__main__":
    unittest.main()
