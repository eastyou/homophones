"""同音词数据模型：数据加载、校验、查询与出题。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

MAX_QUIZ_COUNT = 40
MAX_MATCH_COUNT = 20
BLANK_MARK = "____"


@dataclass(frozen=True)
class HomophoneGroup:
    """一组同音词。

    属性：
        words: 同组单词（2~3 个，均为小写）。
        meanings: 单词到中文释义的映射，键与 ``words`` 一一对应。
        sentence: 含一个 ``____`` 挖空标记的英文例句。
        answer: 例句空格处的正确单词，必须属于 ``words``。
        hint: 中文提示，保证答案唯一。
    """

    words: Tuple[str, ...]
    meanings: Dict[str, str]
    sentence: str
    answer: str
    hint: str


def normalize(word: str) -> str:
    """把单词规整为小写并去除首尾空白。

    参数：
        word: 待规整的单词。

    返回：
        规整后的字符串。

    异常：
        TypeError: ``word`` 不是字符串。
    """
    if not isinstance(word, str):
        raise TypeError("单词必须是字符串")
    return word.strip().casefold()


def _validate_group(group: HomophoneGroup) -> None:
    """校验单个同音组数据的完整性，数据不合法时抛出 ``ValueError``。"""
    if not isinstance(group, HomophoneGroup):
        raise TypeError("同音组必须是 HomophoneGroup 实例")
    if not isinstance(group.words, tuple) or not 2 <= len(group.words) <= 3:
        raise ValueError("同音组必须包含 2 到 3 个单词")
    if not isinstance(group.meanings, dict):
        raise ValueError("同音组释义必须是字典")

    normalized: List[str] = []
    for word in group.words:
        if not isinstance(word, str) or not word.strip():
            raise ValueError("同音组中的单词必须是非空字符串")
        key = normalize(word)
        if key in normalized:
            raise ValueError("同音组中单词重复：%s" % word)
        normalized.append(key)
        if key not in group.meanings:
            raise ValueError("缺少单词释义：%s" % word)
        value = group.meanings[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("单词释义必须是非空字符串：%s" % word)

    if set(group.meanings.keys()) != set(normalized):
        raise ValueError("释义与同音组单词不一致：%s" % " / ".join(group.words))

    if not isinstance(group.sentence, str) or group.sentence.count(BLANK_MARK) != 1:
        raise ValueError("例句必须包含且只包含一个空格标记 ____")

    if not isinstance(group.answer, str) or normalize(group.answer) not in normalized:
        raise ValueError("答案不在同音组中：%s" % str(group.answer))

    if not isinstance(group.hint, str) or not group.hint.strip():
        raise ValueError("提示必须是非空字符串")


_RawGroup = Tuple[Tuple[str, ...], Dict[str, str], str, str, str]

_RAW_GROUPS: Tuple[_RawGroup, ...] = (
    (("sea", "see"), {"sea": "大海；海洋", "see": "看见；明白"},
     "We went to the ____ for a swim.", "sea", "指大海（名词）"),
    (("right", "write"), {"right": "右边；正确的", "write": "书写"},
     "Please ____ your name on the paper.", "write", "动词，意思是书写"),
    (("their", "there"), {"their": "他们的", "there": "那里"},
     "The students left ____ books on the desks.", "their", "形容词性物主代词，表示“他们的”"),
    (("pair", "pear"), {"pair": "一双；一对", "pear": "梨"},
     "She bought a ____ of new shoes.", "pair", "量词，表示“一双”"),
    (("flower", "flour"), {"flower": "花", "flour": "面粉"},
     "We need some ____ to bake the cake.", "flour", "做蛋糕用的面粉"),
    (("peace", "piece"), {"peace": "和平", "piece": "一块；一片"},
     "He ate a ____ of chocolate.", "piece", "量词，表示“一块”"),
    (("break", "brake"), {"break": "打破；休息", "brake": "刹车"},
     "The bike's ____ does not work, so be careful.", "brake", "自行车上用来减速的刹车"),
    (("weather", "whether"), {"weather": "天气", "whether": "是否"},
     "I don't know ____ he will come tonight.", "whether", "连词，表示“是否”"),
    (("son", "sun"), {"son": "儿子", "sun": "太阳"},
     "The ____ rises in the east every morning.", "sun", "天上的太阳"),
    (("meat", "meet"), {"meat": "肉", "meet": "见面"},
     "Nice to ____ you, Mr. Green.", "meet", "动词，表示“见面”"),
    (("be", "bee"), {"be": "是；存在", "bee": "蜜蜂"},
     "A ____ is flying around the flowers.", "bee", "会采蜜的昆虫"),
    (("bear", "bare"), {"bear": "熊", "bare": "赤裸的"},
     "A brown ____ is sleeping in the cave.", "bear", "会冬眠的动物"),
    (("buy", "by", "bye"), {"buy": "购买", "by": "通过；在……旁边", "bye": "再见"},
     "I want to ____ a new notebook.", "buy", "动词，表示“购买”"),
    (("dear", "deer"), {"dear": "亲爱的", "deer": "鹿"},
     "____ friend, thank you for your help.", "dear", "信件开头称呼“亲爱的”"),
    (("knight", "night"), {"knight": "骑士", "night": "夜晚"},
     "The ____ rode a white horse into the castle.", "knight", "穿盔甲、骑马的骑士"),
    (("knew", "new"), {"knew": "知道（know 的过去式）", "new": "新的"},
     "I ____ the answer before the teacher asked.", "knew", "know 的过去式"),
    (("know", "no"), {"know": "知道", "no": "不；没有"},
     "I ____ the answer, so please ask me.", "know", "动词，表示“知道”"),
    (("here", "hear"), {"here": "这里", "hear": "听见"},
     "Can you ____ me clearly on the phone?", "hear", "动词，表示“听见”"),
    (("hole", "whole"), {"hole": "洞；破洞", "whole": "整个的"},
     "There is a ____ in my sock.", "hole", "袜子上的破洞"),
    (("hour", "our"), {"hour": "小时", "our": "我们的"},
     "We waited for an ____ at the station.", "hour", "时间单位“小时”"),
    (("its", "it's"), {"its": "它的", "it's": "它是（it is 的缩写）"},
     "The cat licked ____ paws after dinner.", "its", "形容词性物主代词，表示“它的”"),
    (("made", "maid"), {"made": "制作（make 的过去式）", "maid": "女仆"},
     "The cake was ____ by my mother.", "made", "make 的过去分词"),
    (("mail", "male"), {"mail": "邮件；邮寄", "male": "男性的"},
     "I sent the letter by ____ yesterday.", "mail", "通过邮局寄送的邮件"),
    (("one", "won"), {"one": "一", "won": "赢（win 的过去式）"},
     "Our team ____ the game last night.", "won", "win 的过去式"),
    (("plain", "plane"), {"plain": "简单的；平原", "plane": "飞机"},
     "The ____ landed safely on the runway.", "plane", "在天上飞的飞机"),
    (("road", "rode"), {"road": "道路", "rode": "骑（ride 的过去式）"},
     "He ____ his bike to school this morning.", "rode", "ride 的过去式"),
    (("sail", "sale"), {"sail": "航行", "sale": "出售；促销"},
     "The boat will ____ across the lake.", "sail", "动词，表示“航行”"),
    (("some", "sum"), {"some": "一些", "sum": "总数；金额"},
     "He paid the ____ of ten dollars.", "sum", "数学中指“总和”"),
    (("stair", "stare"), {"stair": "楼梯", "stare": "盯着看"},
     "Please don't ____ at strangers.", "stare", "动词，表示“盯着看”"),
    (("tail", "tale"), {"tail": "尾巴", "tale": "故事"},
     "The dog wagged its ____ happily.", "tail", "动物的尾巴"),
    (("threw", "through"), {"threw": "扔（throw 的过去式）", "through": "穿过"},
     "He ____ the ball over the fence.", "threw", "throw 的过去式"),
    (("two", "too", "to"), {"two": "二", "too": "也；太", "to": "到；向"},
     "I have ____ brothers and one sister.", "two", "数字 2"),
    (("wait", "weight"), {"wait": "等待", "weight": "重量"},
     "Please ____ for me at the school gate.", "wait", "动词，表示“等待”"),
    (("weak", "week"), {"weak": "虚弱的", "week": "星期"},
     "She was ill and felt very ____.", "weak", "形容词，表示“虚弱的”"),
    (("wear", "where"), {"wear": "穿；戴", "where": "哪里"},
     "____ are my glasses?", "where", "疑问词，表示“在哪里”"),
    (("wood", "would"), {"wood": "木头", "would": "将会（情态动词）"},
     "I ____ like a cup of tea, please.", "would", "would like 中的情态动词"),
    (("aloud", "allowed"), {"aloud": "大声地", "allowed": "被允许的"},
     "Smoking is not ____ in this building.", "allowed", "动词 allow 的过去分词"),
    (("ate", "eight"), {"ate": "吃（eat 的过去式）", "eight": "八"},
     "She ____ an apple after lunch.", "ate", "eat 的过去式"),
    (("blue", "blew"), {"blue": "蓝色的", "blew": "吹（blow 的过去式）"},
     "The wind ____ hard last night.", "blew", "blow 的过去式"),
    (("board", "bored"), {"board": "木板；董事会", "bored": "感到无聊的"},
     "I am ____ with this game.", "bored", "形容词，表示“感到无聊的”"),
    (("cell", "sell"), {"cell": "细胞；牢房", "sell": "卖"},
     "He wants to ____ his old car.", "sell", "动词，表示“出售”"),
    (("cent", "sent", "scent"), {"cent": "分（货币）", "sent": "寄；发送（send 的过去式）", "scent": "气味"},
     "I ____ a message to him yesterday.", "sent", "send 的过去式"),
    (("die", "dye"), {"die": "死亡", "dye": "染色"},
     "The old tree may ____ soon.", "die", "动词，表示“死亡”"),
    (("fair", "fare"), {"fair": "公平的；集市", "fare": "车费"},
     "The bus ____ is two dollars.", "fare", "乘坐交通工具的费用"),
    (("flew", "flu"), {"flew": "飞（fly 的过去式）", "flu": "流感"},
     "She ____ to Beijing yesterday.", "flew", "fly 的过去式"),
    (("for", "four", "fore"), {"for": "为了", "four": "四", "fore": "前部"},
     "This gift is ____ you.", "for", "介词，表示“为了”"),
    (("grown", "groan"), {"grown": "生长（grow 的过去分词）", "groan": "呻吟"},
     "The plants have ____ much taller this year.", "grown", "grow 的过去分词"),
    (("hair", "hare"), {"hair": "头发", "hare": "野兔"},
     "A ____ ran across the field quickly.", "hare", "像兔子一样的野兔"),
    (("heal", "heel"), {"heal": "治愈；愈合", "heel": "脚后跟"},
     "The wound will ____ in a few days.", "heal", "动词，表示“愈合”"),
    (("high", "hi"), {"high": "高的", "hi": "嗨"},
     "The wall is too ____ to climb.", "high", "形容词，表示“高的”"),
    (("in", "inn"), {"in": "在……里面", "inn": "小旅馆"},
     "We stayed at a small ____ near the station.", "inn", "供旅客住宿的小旅馆"),
    (("missed", "mist"), {"missed": "错过（miss 的过去式）", "mist": "薄雾"},
     "I ____ the bus this morning.", "missed", "miss 的过去式"),
    (("passed", "past"), {"passed": "通过（pass 的过去式）", "past": "过去"},
     "He ____ the English exam easily.", "passed", "pass 的过去式"),
    (("patience", "patients"), {"patience": "耐心", "patients": "病人（复数）"},
     "The doctor has many ____ every day.", "patients", "医生照顾的病人（复数）"),
    (("rain", "reign", "rein"), {"rain": "雨", "reign": "统治", "rein": "缰绳"},
     "The ____ is very heavy today.", "rain", "天上落下的雨"),
    (("raise", "rays", "raze"), {"raise": "举起；提高", "rays": "光线（复数）", "raze": "摧毁"},
     "Please ____ your hand if you know the answer.", "raise", "动词，表示“举起”"),
    (("rap", "wrap"), {"rap": "敲击；说唱", "wrap": "包裹"},
     "Let me ____ the gift for you.", "wrap", "动词，表示“包装”"),
    (("ring", "wring"), {"ring": "铃响；戒指", "wring": "拧"},
     "The phone will ____ at eight o'clock.", "ring", "电话铃响"),
    (("role", "roll"), {"role": "角色", "roll": "卷；滚动"},
     "She plays an important ____ in the play.", "role", "戏剧中的角色"),
    (("scene", "seen"), {"scene": "场景", "seen": "看见（see 的过去分词）"},
     "I have never ____ such a beautiful lake.", "seen", "see 的过去分词"),
    (("steal", "steel"), {"steal": "偷", "steel": "钢"},
     "Don't ____ other people's things.", "steal", "动词，表示“偷窃”"),
    (("throne", "thrown"), {"throne": "王座", "thrown": "扔（throw 的过去分词）"},
     "The king sat on his ____.", "throne", "国王坐的王座"),
    (("tide", "tied"), {"tide": "潮水", "tied": "系（tie 的过去式）"},
     "The ____ comes in every evening.", "tide", "海边的潮水"),
    (("time", "thyme"), {"time": "时间", "thyme": "百里香"},
     "What ____ is it now?", "time", "名词，表示“时间”"),
    (("which", "witch"), {"which": "哪一个", "witch": "女巫"},
     "____ book do you want to borrow?", "which", "疑问词，表示“哪一个”"),
    (("yolk", "yoke"), {"yolk": "蛋黄", "yoke": "轭"},
     "The egg has a yellow ____.", "yolk", "鸡蛋中间的蛋黄"),
)


def _build_groups(raw: Iterable[_RawGroup]) -> Tuple[HomophoneGroup, ...]:
    """把原始元组数据转换为 ``HomophoneGroup`` 元组。"""
    groups: List[HomophoneGroup] = []
    for words, meanings, sentence, answer, hint in raw:
        groups.append(
            HomophoneGroup(
                words=tuple(words),
                meanings=dict(meanings),
                sentence=sentence,
                answer=answer,
                hint=hint,
            )
        )
    return tuple(groups)


def _build_index(groups: Iterable[HomophoneGroup]) -> Dict[str, HomophoneGroup]:
    """建立“单词 → 同音组”索引，单词跨组重复时抛出 ``ValueError``。"""
    index: Dict[str, HomophoneGroup] = {}
    for group in groups:
        for word in group.words:
            key = normalize(word)
            if key in index:
                raise ValueError("单词 %s 出现在多个同音组中" % word)
            index[key] = group
    return index


_GROUPS: Tuple[HomophoneGroup, ...] = _build_groups(_RAW_GROUPS)
for _group in _GROUPS:
    _validate_group(_group)
_WORD_INDEX: Dict[str, HomophoneGroup] = _build_index(_GROUPS)


def all_groups() -> List[HomophoneGroup]:
    """返回全部同音组（新列表，避免调用方修改内部数据）。"""
    return list(_GROUPS)


def find_group(word: str) -> HomophoneGroup:
    """查找单词所在的同音组。

    参数：
        word: 英文单词，大小写与首尾空白不敏感。

    返回：
        包含该单词的同音组。

    异常：
        TypeError: ``word`` 不是字符串。
        ValueError: 单词为空或不在词库中。
    """
    key = normalize(word)
    if not key:
        raise ValueError("单词不能为空")
    try:
        return _WORD_INDEX[key]
    except KeyError:
        raise ValueError("未知单词：%s" % word.strip()) from None


def meaning(word: str) -> str:
    """返回单词的中文释义。

    异常：
        TypeError: ``word`` 不是字符串。
        ValueError: 单词为空或不在词库中。
    """
    group = find_group(word)
    return group.meanings[normalize(word)]


def _validate_count(count: int, minimum: int, maximum: int, label: str) -> int:
    """校验数量参数，返回原值。"""
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("%s必须是整数" % label)
    if count < minimum or count > maximum:
        raise ValueError("%s必须在 %d 到 %d 之间" % (label, minimum, maximum))
    return count


def _validate_seed(seed: Optional[int]) -> None:
    """校验随机种子类型。"""
    if seed is None:
        return
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("随机种子必须是整数")


def quiz_items(count: int, seed: Optional[int] = None) -> List[Dict[str, object]]:
    """随机生成填空题。

    参数：
        count: 题目数量，取值 1~40。
        seed: 随机种子，相同种子得到相同题目。

    返回：
        题目字典列表，每项包含 ``number``、``sentence``、``hint``、
        ``options``（候选词元组）、``answer`` 与 ``meanings``。

    异常：
        TypeError: ``count`` 不是整数（排除布尔值）或 ``seed`` 不是整数。
        ValueError: ``count`` 超出 1~40。
    """
    _validate_count(count, 1, MAX_QUIZ_COUNT, "题目数量")
    _validate_seed(seed)

    rng = random.Random(seed)
    chosen = rng.sample(_GROUPS, count)
    items: List[Dict[str, object]] = []
    for number, group in enumerate(chosen, start=1):
        options = list(group.words)
        rng.shuffle(options)
        items.append(
            {
                "number": number,
                "sentence": group.sentence,
                "hint": group.hint,
                "options": tuple(options),
                "answer": group.answer,
                "meanings": dict(group.meanings),
            }
        )
    return items


def match_items(count: int, seed: Optional[int] = None) -> List[Tuple[str, str]]:
    """随机生成“单词—释义”配对题。

    参数：
        count: 配对数量，取值 1~20。
        seed: 随机种子，相同种子得到相同配对。

    返回：
        ``(单词, 释义)`` 元组列表，单词互不重复。

    异常：
        TypeError: ``count`` 不是整数（排除布尔值）或 ``seed`` 不是整数。
        ValueError: ``count`` 超出 1~20。
    """
    _validate_count(count, 1, MAX_MATCH_COUNT, "配对数量")
    _validate_seed(seed)

    rng = random.Random(seed)
    pairs: List[Tuple[str, str]] = []
    for group in rng.sample(_GROUPS, count):
        word = rng.choice(group.words)
        pairs.append((word, group.meanings[word]))
    return pairs
