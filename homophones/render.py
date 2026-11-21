"""把同音词数据渲染为可打印的 A4 HTML 页面。"""

from __future__ import annotations

import html
from typing import Dict, List, Sequence, Tuple

from .model import HomophoneGroup

_STYLE = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px;
      font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei",
                   "Helvetica Neue", Arial, sans-serif;
      color: #1f2933;
      background: #f5f7fa;
      line-height: 1.65;
      font-size: 15px;
    }
    .page {
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      padding: 32px 36px;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
    }
    header { border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 22px; }
    h1 { margin: 0 0 4px; font-size: 24px; color: #1d4ed8; }
    h2 { margin: 22px 0 10px; font-size: 17px; color: #1e3a8a; }
    .subtitle { margin: 0; color: #52606d; font-size: 13px; }
    .card {
      border: 1px solid #d9e2ec;
      border-radius: 6px;
      padding: 14px 16px;
      margin-bottom: 14px;
      page-break-inside: avoid;
    }
    .q-head { display: flex; gap: 10px; align-items: baseline; }
    .no { font-weight: 700; color: #2563eb; flex: 0 0 auto; }
    .sentence { font-size: 16px; }
    .blank {
      display: inline-block;
      min-width: 88px;
      border-bottom: 1px solid #334155;
      text-align: center;
      color: #334155;
    }
    .hint { margin: 8px 0 6px; color: #52606d; font-size: 13px; }
    .options { margin: 0; padding-left: 20px; }
    .options li { display: inline-block; margin-right: 18px; font-weight: 600; }
    .answer { margin: 8px 0 0; color: #b91c1c; font-size: 14px; }
    .empty { color: #7b8794; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }
    th { background: #eef2ff; color: #1e3a8a; }
    .columns { display: flex; gap: 28px; }
    .column { flex: 1; min-width: 0; }
    .column ol { margin: 0; padding-left: 22px; }
    .column li { margin-bottom: 8px; }
    .letters { list-style-type: upper-alpha; }
    .grid { display: flex; flex-wrap: wrap; gap: 12px 24px; margin-top: 16px; }
    .grid span {
      display: inline-block;
      min-width: 110px;
      border-bottom: 1px solid #334155;
      padding-bottom: 2px;
    }
    footer { margin-top: 24px; color: #7b8794; font-size: 12px; text-align: center; }
    @page { size: A4; margin: 16mm; }
    @media print {
      body { background: #ffffff; padding: 0; font-size: 12pt; }
      .page { max-width: none; padding: 0; box-shadow: none; border-radius: 0; }
      .card { border-color: #b8c4d0; }
      a { color: inherit; }
    }
"""


def _validate_title(title: str) -> None:
    """校验标题参数。"""
    if not isinstance(title, str):
        raise TypeError("标题必须是字符串")
    if not title.strip():
        raise ValueError("标题不能为空")


def _page(title: str, subtitle: str, body: str) -> str:
    """套用统一的 A4 页面模板。"""
    safe_title = html.escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "  <title>" + safe_title + "</title>\n"
        "  <style>" + _STYLE + "  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <main class="page">\n'
        "    <header>\n"
        "      <h1>" + safe_title + "</h1>\n"
        '      <p class="subtitle">' + html.escape(subtitle) + "</p>\n"
        "    </header>\n" + body + "\n"
        '    <footer>homophones · 英语同音词练习</footer>\n'
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def _quiz_card(
    number: int,
    sentence: str,
    hint: str,
    options: Sequence[str],
    answer: str,
    with_answers: bool,
) -> str:
    """渲染单道填空题卡片。"""
    sentence_html = html.escape(sentence).replace(
        "____", '<span class="blank">____</span>'
    )
    option_items = "\n".join(
        '        <li>%s</li>' % html.escape(option) for option in options
    )
    answer_html = (
        '\n      <p class="answer">答案：%s</p>' % html.escape(answer)
        if with_answers
        else ""
    )
    return (
        '    <section class="card">\n'
        '      <div class="q-head"><span class="no">%d.</span>'
        '<span class="sentence">%s</span></div>\n'
        '      <p class="hint">提示：%s</p>\n'
        '      <ul class="options">\n%s\n      </ul>%s\n'
        "    </section>"
    ) % (number, sentence_html, html.escape(hint), option_items, answer_html)


def quiz_html(
    items: Sequence[Dict[str, object]],
    title: str,
    with_answers: bool = False,
) -> str:
    """渲染填空题练习页。

    参数：
        items: ``quiz_items`` 返回的题目列表。
        title: 页面标题。
        with_answers: 是否在每道题后显示答案。

    返回：
        完整的 HTML 文本。

    异常：
        TypeError: 参数类型不正确。
        ValueError: 参数取值不合法或题目数据不完整。
    """
    _validate_title(title)
    if not isinstance(with_answers, bool):
        raise TypeError("with_answers 必须是布尔值")
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise TypeError("题目列表必须是序列")

    cards: List[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise TypeError("第 %d 道题必须是字典" % index)
        sentence = item.get("sentence")
        hint = item.get("hint")
        options = item.get("options")
        answer = item.get("answer")
        if not isinstance(sentence, str) or not sentence.strip():
            raise ValueError("第 %d 道题的题干无效" % index)
        if not isinstance(hint, str) or not hint.strip():
            raise ValueError("第 %d 道题的提示无效" % index)
        if isinstance(options, (str, bytes)) or not isinstance(options, Sequence):
            raise ValueError("第 %d 道题的候选词无效" % index)
        if len(options) < 2 or len(options) > 3:
            raise ValueError("第 %d 道题必须提供 2 到 3 个候选词" % index)
        for option in options:
            if not isinstance(option, str) or not option.strip():
                raise ValueError("第 %d 道题的候选词无效" % index)
        if not isinstance(answer, str) or answer not in options:
            raise ValueError("第 %d 道题的答案无效" % index)
        cards.append(_quiz_card(index, sentence, hint, options, answer, with_answers))

    body = "\n".join(cards) if cards else '    <p class="empty">暂无题目。</p>'
    return _page(title, "填空练习：根据中文提示选出正确的单词", body)


def match_html(pairs: Sequence[Tuple[str, str]], title: str) -> str:
    """渲染“单词—释义”配对练习页。

    参数：
        pairs: ``match_items`` 返回的 ``(单词, 释义)`` 列表。
        title: 页面标题。

    返回：
        完整的 HTML 文本。

    异常：
        TypeError: 参数类型不正确。
        ValueError: 参数取值不合法。
    """
    _validate_title(title)
    if isinstance(pairs, (str, bytes)) or not isinstance(pairs, Sequence):
        raise TypeError("配对列表必须是序列")

    cleaned: List[Tuple[str, str]] = []
    for index, pair in enumerate(pairs, start=1):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise TypeError("第 %d 个配对必须是 (单词, 释义) 二元组" % index)
        word, explanation = pair
        if not isinstance(word, str) or not word.strip():
            raise ValueError("第 %d 个配对的单词无效" % index)
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("第 %d 个配对的释义无效" % index)
        cleaned.append((word, explanation))

    if not cleaned:
        body = '    <p class="empty">暂无配对数据。</p>'
        return _page(title, "配对练习：把单词与释义连线", body)

    word_items = "\n".join(
        "        <li>%s</li>" % html.escape(word) for word, _ in cleaned
    )
    meaning_items = "\n".join(
        "        <li>%s</li>" % html.escape(explanation)
        for _, explanation in sorted(cleaned, key=lambda pair: pair[1])
    )
    answer_cells = "\n".join(
        "      <span>%d. ____</span>" % number
        for number in range(1, len(cleaned) + 1)
    )
    body = (
        '    <div class="columns">\n'
        '      <div class="column">\n'
        "        <h2>单词</h2>\n"
        "        <ol>\n%s\n        </ol>\n"
        "      </div>\n"
        '      <div class="column">\n'
        "        <h2>释义</h2>\n"
        '        <ol class="letters">\n%s\n        </ol>\n'
        "      </div>\n"
        "    </div>\n"
        "    <h2>作答区</h2>\n"
        '    <div class="grid">\n%s\n    </div>'
    ) % (word_items, meaning_items, answer_cells)
    return _page(title, "配对练习：写出每个单词对应的释义字母", body)


def group_html(groups: Sequence[HomophoneGroup], title: str) -> str:
    """渲染同音组速查表。

    参数：
        groups: ``HomophoneGroup`` 列表。
        title: 页面标题。

    返回：
        完整的 HTML 文本。

    异常：
        TypeError: 参数类型不正确。
        ValueError: 参数取值不合法。
    """
    _validate_title(title)
    if isinstance(groups, (str, bytes)) or not isinstance(groups, Sequence):
        raise TypeError("同音组列表必须是序列")

    rows: List[str] = []
    for index, group in enumerate(groups, start=1):
        if not isinstance(group, HomophoneGroup):
            raise TypeError("第 %d 项必须是 HomophoneGroup" % index)
        words_html = "<br>".join(
            "<strong>%s</strong>" % html.escape(word) for word in group.words
        )
        meanings_html = "<br>".join(
            "%s：%s" % (html.escape(word), html.escape(group.meanings[word]))
            for word in group.words
        )
        rows.append(
            "      <tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (index, words_html, meanings_html, html.escape(group.sentence))
        )

    if rows:
        body = (
            "    <table>\n"
            "      <thead><tr><th>序号</th><th>同音组</th><th>释义</th><th>例句</th></tr></thead>\n"
            "      <tbody>\n%s\n      </tbody>\n"
            "    </table>" % "\n".join(rows)
        )
    else:
        body = '    <p class="empty">暂无同音组数据。</p>'
    return _page(title, "速查表：同音词对照与例句", body)
