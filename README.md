# homophones

[![CI](https://github.com/eastyou/homophones/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/homophones/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

英语同音词工具：查询同音组、辨析词义、生成可打印的 A4 练习页。内置 **66 组**同音词，仅使用 Python 标准库，零第三方依赖，兼容 Python 3.9 及以上版本。

## 特性

- **同音组查询**：`sea / see`、`right / write`、`their / there` 等 66 组同音词，每组 2~3 个单词。
- **中文释义与例句**：每个单词都有中文释义，每组都配有挖空例句、中文提示与唯一答案。
- **题库生成**：填空题（1~40 题）与词义配对题（1~20 题），支持随机种子复现。
- **可打印页面**：内置 `@page { size: A4 }` 与 `@media print` 样式，浏览器直接打印即可作为课堂练习。
- **严格输入校验**：类型错误抛 `TypeError`，取值错误抛 `ValueError`，错误消息为中文。
- **数据自检**：模块导入时校验全部数据（同组重复单词、缺失释义、答案不在组内等），问题数据会立即报错。

## 安装

```bash
git clone https://github.com/eastyou/homophones.git
cd homophones
python3 -m pip install -e .
```

不安装也可以直接以模块方式运行：

```bash
python3 -m homophones --help
```

要求 Python >= 3.9，无第三方依赖。

## 命令行用法

```bash
homophones find <单词>                                  # 查询单词所在同音组
homophones meaning <单词>                               # 查看单词中文释义
homophones quiz --count N --seed S [-o 文件]            # 生成填空题
homophones match --count N --seed S [-o 文件]           # 生成词义配对题
homophones groups [-o 文件]                             # 输出同音组速查表
```

示例：

```console
$ homophones find see
同音组：sea / see
  sea：大海；海洋
  see：看见；明白
例句：We went to the ____ for a swim.
答案：sea
提示：指大海（名词）

$ homophones meaning PEAR
pear：梨

$ homophones quiz --count 3 --seed 5
1. Please ____ for me at the school gate.
   候选：weight / wait
   提示：动词，表示“等待”
2. This gift is ____ you.
   候选：fore / for / four
   提示：介词，表示“为了”
3. Can you ____ me clearly on the phone?
   候选：hear / here
   提示：动词，表示“听见”

$ homophones quiz --count 10 --seed 5 -o examples/quiz.html
已生成：examples/quiz.html
```

说明：

- `--count` 超出范围时返回退出码 `2`，并在标准错误输出中文提示。
- `-o` 指定的目录不存在时会自动创建；写入失败时同样返回退出码 `2`。
- 生成的练习题页面包含答案（答案以红色显示），便于教师核对。

## 库用法

```python
from homophones import find_group, meaning, quiz_items, quiz_html

group = find_group("  SEE ")          # 大小写与首尾空白不敏感
print(group.words)                    # ('sea', 'see')
print(group.meanings["sea"])          # 大海；海洋
print(meaning("see"))                 # 看见；明白

items = quiz_items(3, seed=5)         # 固定种子，结果可复现
page = quiz_html(items, "课堂练习", with_answers=True)
with open("quiz.html", "w", encoding="utf-8") as handle:
    handle.write(page)
```

配对题与速查表：

```python
from homophones import all_groups, group_html, match_html, match_items

pairs = match_items(8, seed=3)        # 例如 [('sea', '大海；海洋'), ...]
with open("match.html", "w", encoding="utf-8") as handle:
    handle.write(match_html(pairs, "同音词配对练习"))

with open("groups.html", "w", encoding="utf-8") as handle:
    handle.write(group_html(all_groups(), "同音词速查表"))
```

公共 API：

| 名称 | 说明 |
| --- | --- |
| `HomophoneGroup` | 不可变数据类：`words`、`meanings`、`sentence`、`answer`、`hint` |
| `all_groups()` | 返回全部 66 组同音词（新列表） |
| `normalize(word)` | 去除首尾空白并转小写 |
| `find_group(word)` | 查询单词所在同音组，未知单词抛 `ValueError` |
| `meaning(word)` | 查询单词中文释义 |
| `quiz_items(count, seed=None)` | 生成 1~40 道填空题 |
| `match_items(count, seed=None)` | 生成 1~20 个词义配对 |
| `quiz_html(items, title, with_answers=False)` | 渲染 A4 填空题页面 |
| `match_html(pairs, title)` | 渲染 A4 配对练习页面 |
| `group_html(groups, title)` | 渲染 A4 同音组速查表 |
| `main(argv=None)` | 命令行入口，返回退出码 |

## 示例页面

仓库内 `examples/` 目录提供了由命令行实际生成的页面：

- `examples/quiz.html`：10 道填空题（含答案）
- `examples/match.html`：10 个词义配对
- `examples/groups.html`：66 组同音词速查表

用浏览器打开后即可预览，使用“打印”功能会按 A4 纸张排版。

## 项目结构

```
homophones/
├── homophones/
│   ├── __init__.py      # 公共 API 与 __version__
│   ├── __main__.py      # python -m homophones 入口
│   ├── model.py         # 同音词数据、校验、查询与出题
│   ├── render.py        # A4 可打印 HTML 渲染
│   └── cli.py           # 命令行接口
├── tests/
│   ├── __init__.py
│   ├── test_model.py
│   ├── test_render.py
│   └── test_cli.py
├── examples/
│   ├── quiz.html
│   ├── match.html
│   └── groups.html
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
└── .github/workflows/ci.yml
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```

共 **123** 个单元测试，覆盖数据完整性、参数校验、边界条件、HTML 转义、文件写入与 CLI 退出码；在 Python 3.9.6 与 Python 3.15.2 上均全部通过。

## 许可证

MIT © 2026 eastyou
