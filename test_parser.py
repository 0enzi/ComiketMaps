import pytest
from parser import EventConfig, DaySpec, parse_comiket_bio

C107_CONFIG = EventConfig(
    event_code="C107",
    day1=DaySpec(12, 30, "火"),
    day2=DaySpec(12, 31, "水"),
)

C108_CONFIG = EventConfig(
    event_code="C108",
    day1=DaySpec(8, 15, "土"),
    day2=DaySpec(8, 16, "日"),
)

SEED_FIXTURES = [
    ("ponika_illust", "ぽん🦢C107✦2日目東ユ-37ab", [(2, "East", "ユ", "37", "ab")]),
    ("kazukiadumi", "あづみ一樹🌸冬コミ1日目ア80ab/2日目ユ49a", [(1, "East", "ア", "80", "ab"), (2, "East", "ユ", "49", "a")]),
    ("chia_momochi_", "桃稚 ちあ🎀C107￤2日目東4〖メ-34a〗", [(2, "East", "メ", "34", "a")]),
    ("erisize", "なつめえり🍚冬コミ*1日目西め-46*2日目 東Ａ-40a", [(1, "West", "め", "46", "ab"), (2, "East", "Ａ", "40", "a")]),
    ("mikaze_oto", "緑風マルト🌿C107 2日目東メ-40a", [(2, "East", "メ", "40", "a")]),
    ("sn_hiyori", "茶乃ひより🐈‍⬛C107 2日目西へ-36a", [(2, "West", "へ", "36", "a")]),
    ("kurumi_lm", "双葉くるみ@一日目東ホ09ab/二日目東I48a", [(1, "East", "ホ", "09", "ab"), (2, "East", "I", "48", "a")]),
    ("ayamygarubinu", "あやみ🍎C107(火)東マ-18ab", [(1, "East", "マ", "18", "ab")]),
    ("momoshiki", "ももしき🍑1日目西は-41a", [(1, "West", "は", "41", "a")]),
    ("momoco_haru", "ももこ🍑C107/1日目南2ホールa-29ab", [(1, "South", "a", "29", "ab")]),
    ("KaguraMea_VoV", "🍥神楽めあ/KaguraMea🍥C107 火曜西め-47ab", [(1, "West", "め", "47", "ab")]),
    ("KitaIroha", "KiTA@C107(火)東メ36ab", [(1, "East", "メ", "36", "ab")]),
    ("mikeou_", "みけおう 1日目西2さ-20a/2日目東4ユ-52", [(1, "West", "さ", "20", "a"), (2, "East", "ユ", "52", "ab")]),
    ("nana_kaguraaa", "ななかぐら/カグラナナ🌶1日目西あ34ab", [(1, "West", "あ", "34", "ab")]),
    ("T1kosewad78", "Tikosewad!! C107 1日目 東4 ヨ49AB", [(1, "East", "ヨ", "49", "ab")]),
    ("tateha_MG", "立羽 🦊 C107冬コミ２日目 東ユ-40ab✨新作画集「しおり-SHIORI-」発売中！", [(2, "East", "ユ", "40", "ab")]),
    ("kabedoru", "Kabedoru / 壁どる/C107(火)東\"メ\"-16b", [(1, "East", "メ", "16", "b")]),
    ("shirorokitsune", "しろきつね 🌸 東７-Ａ34ab／2日目【12/31(水)】", [(2, "East", "Ａ", "34", "ab")]),
    ("hisagi_02", "ひさぎ️️️⛅️冬ｺﾐ水曜日-東ノ30a", [(2, "East", "ノ", "30", "a")]),
    ("yuukamiya68", "榎宮祐♟️ 1日目南a-30ab", [(1, "South", "a", "30", "ab")]),
    ("0725akaba", "アカババァ@C107 1日目 西2す21b", [(1, "West", "す", "21", "b")]),
    ("sakurapion", "みわべさくら＠C107【1日目ア-85b】【2日目ア-84a】", [(1, "East", "ア", "85", "b"), (2, "East", "ア", "84", "a")]),
    ("ogipote", "荻pote@1日目東ア-64ab", [(1, "East", "ア", "64", "ab")]),
    ("koyubita", "こゆびた▷2日目 西ひ50b", [(2, "West", "ひ", "50", "b")]),
    ("mishima_kurone", "三嶋くろね■C107_水曜西2/あ53ab", [(2, "West", "あ", "53", "ab")]),
    ("hiiragiryo", "柊椋@C107/1日目東ノ-09b", [(1, "East", "ノ", "09", "b")]),
    ("hidulme", "ひづるめ / Hidzz @C107 (1日目東ヒ09ab)", [(1, "East", "ヒ", "09", "ab")]),
    ("Klee_0303", "Klee-on┊C107 2日目 西1 と-15a", [(2, "West", "と", "15", "a")]),
    ("kagachi_SK", "かがちさく☕C107 2日目西へ10a", [(2, "West", "へ", "10", "a")]),
    ("tenmu_nagomi", "天夢 森流彩🦊2日目 西め28ab 和 ⛩", [(2, "West", "め", "28", "ab")]),
    ("izuminanase", "いずみななせ🐰2日目東メ38a", [(2, "East", "メ", "38", "a")]),
    ("oguraponti", "小倉ぽんち❄️C107(火曜日)東7 D-01a", [(1, "East", "D", "01", "a")]),
    ("horioo", "師走ほりお🐱 C107２日目東メ42a", [(2, "East", "メ", "42", "a")]),
    ("konpe0217", "こんぺ伊藤@C107-2日目 西1へ-09b", [(2, "West", "へ", "09", "b")]),
    ("yuyucocco_", "ゆゆこ🎀🤍2日目東メ39b", [(2, "East", "メ", "39", "b")]),
    ("Ri0177", "Riri🌧2日目東メ 44b", [(2, "East", "メ", "44", "b")]),
    ("karory", "karory🌃C107-2日目東ア64ab", [(2, "East", "ア", "64", "ab")]),
    ("szcb911", "鬼针草", []),
    ("C10H14N2pome", "ﾆｺﾁﾝ+ﾎﾟﾒ@C1071日目あ38ab", [(1, "West", "あ", "38", "ab")]),
    ("yuimisu_", "ゆいみす🎀C107 2日目東ユ43ab", [(2, "East", "ユ", "43", "ab")]),
    ("1JO_0", "一条レイ@【C107】火曜西は33a/水曜西ほ36b", [(1, "West", "は", "33", "a"), (2, "West", "ほ", "36", "b")]),
    ("Parsley_F", "パセリ@火曜日東ア84ab", [(1, "East", "ア", "84", "ab")]),
    ("40hara", "しま原@2日目西 \"め\"32ab🐈", [(2, "West", "め", "32", "ab")]),
    ("tiv_", "Tiv@２日目西2あ-57b", [(2, "West", "あ", "57", "b")]),
    ("nimono_", "にもし🕊 C107 2日目 西め24ab", [(2, "West", "め", "24", "ab")]),
]

@pytest.mark.parametrize("username,name_text,expected", SEED_FIXTURES, ids=[f[0] for f in SEED_FIXTURES])
def test_seed_fixtures(username, name_text, expected):
    result = parse_comiket_bio(name_text, C107_CONFIG, username=username)
    actual = [(loc.day, loc.direction, loc.section, loc.table, loc.half) for loc in result.locations]
    assert sorted(actual, key=lambda x: (x[0] or 0, x[2] or "")) == sorted(expected, key=lambda x: (x[0] or 0, x[2] or "")), f"Failed for {username}: expected {expected}, got {actual}"
    if not expected:
        assert not result.is_exhibitor

# ---------------------------------------------------------------------------
# Regression Tests for Known Bugs
# ---------------------------------------------------------------------------

def test_bug1_self_collision_with_event_code():
    text = "立羽 🦊 C107冬コミ２日目 東ユ-40ab✨新作画集「しおり-SHIORI-」発売中！"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    assert len(r.locations) == 1
    loc = r.locations[0]
    assert loc.section == "ユ"
    assert loc.table == "40"
    assert loc.half == "ab"

def test_bug2_only_first_match_used():
    text = "1日目ア80ab/2日目ユ49a"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert len(r.locations) == 2
    by_day = {loc.day: loc for loc in r.locations}
    assert by_day[1].section == "ア"
    assert by_day[2].section == "ユ"

def test_bug3_day_keyword_kanji_numerals():
    text = "一日目東ホ09ab/二日目東I48a"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert len(r.locations) == 2
    assert r.locations[0].day == 1
    assert r.locations[1].day == 2

def test_bug4_word_boundary_safety_on_bare_weekday():
    # "日" in 1日目 should NOT trigger C108 day 2 match
    text = "C108 1日目東メ40ab"
    r = parse_comiket_bio(text, C108_CONFIG)
    assert len(r.locations) == 1
    assert r.locations[0].day == 1

def test_bug5_section_char_too_narrow():
    # Full-width Latin and half-width katakana
    text1 = "C107 2日目 東Ａ40ab"
    r1 = parse_comiket_bio(text1, C107_CONFIG)
    assert r1.locations[0].section == "Ａ"

    text2 = "C107 2日目 東ﾒ40ab"
    r2 = parse_comiket_bio(text2, C107_CONFIG)
    assert r2.locations[0].section == "ﾒ"

def test_bug6_whitespace_tolerance():
    text = "Riri🌧2日目東メ 44b"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.section == "メ"
    assert loc.table == "44"
    assert loc.half == "b"

def test_bug7_no_hard_gate_on_event_keyword():
    cases = [
        "天夢 森流彩🦊2日目 西め28ab 和 ⛩",
        "いずみななせ🐰2日目東メ38a",
        "パセリ@火曜日東ア84ab",
    ]
    for text in cases:
        r = parse_comiket_bio(text, C107_CONFIG)
        assert r.is_exhibitor, f"Should be exhibitor: {text}"
        assert len(r.locations) == 1

def test_bug8_no_section_character_hallucination():
    text = "ももしき🍑1日目西は-41a"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.section == "は"
    assert loc.section != "是"
    assert loc.table == "41"
    assert loc.half == "a"

@pytest.mark.parametrize("text,expected", [
    (
        "ほし💛8/16C108 東1【ア18ab】 (@hoshi_u3) on X",
        [(2, "East", "ア", "18", "ab")],
    ),
    (
        "イチリ⓲二日目東７Ａ04ab (@itiri234r) on X",
        [(2, "East", "Ａ", "04", "ab")],
    ),
    (
        "HoR / 1 Art 2 Days / C108 1日目(土) 東1イ19b (@horuhara) on X",
        [(1, "East", "イ", "19", "b")],
    ),
])
def test_profile_text_does_not_turn_handles_or_words_into_booths(text, expected):
    result = parse_comiket_bio(text, C108_CONFIG)
    actual = [
        (loc.day, loc.direction, loc.section, loc.table, loc.half)
        for loc in result.locations
    ]
    assert actual == expected

def test_url_path_fragment_is_not_a_booth():
    result = parse_comiket_bio(
        "C108 1日目東ア21ab https://t.co/X36zrg4Rwe",
        C108_CONFIG,
    )
    assert [
        (loc.day, loc.direction, loc.section, loc.table, loc.half)
        for loc in result.locations
    ] == [(1, "East", "ア", "21", "ab")]

def test_half_after_separator_is_captured():
    result = parse_comiket_bio(
        "C108 2日目(日)東7ホールA23-ab",
        C108_CONFIG,
    )
    assert result.locations[0].half == "ab"

# ---------------------------------------------------------------------------
# Happy Path / Specific Feature Tests
# ---------------------------------------------------------------------------

def test_happy_path_explicit_direction_overrides_inference():
    # Explicit 東 with hiragana section (which would normally infer West).
    r = parse_comiket_bio("C107 2日目東め40ab", C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.direction == "East"  # explicit wins over inference
    assert loc.section == "め"

def test_happy_path_half_width_katakana_inference():
    r = parse_comiket_bio("C107 2日目 ﾒ40ab", C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.direction == "East"
    assert loc.section == "ﾒ"

def test_multi_location_three_locations_same_day():
    text = "C107 1日目東メ40ab 1日目東ア50a"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert len(r.locations) == 2
    assert all(loc.day == 1 for loc in r.locations)

NON_EXHIBITOR_BIOS = [
    "Building a transparent defi dashboard for the next decade.",
    "Founder @castle_labs 🏰",
    "BTC maximalist. HODL since 2013. ⚡",
    "Just a guy who likes pizza and crypto. NFA.",
    "VTuber / illustrator. Commissions closed. 🎨",
    "Check my new track at https://example.com/A1/best-track",
    "AAPL hits $200 today, what's next?",
    "ETH2.0 merge was a historic moment for crypto.",
    "I love photography 📷 and traveling ✈️",
    "鬼针草",
]

@pytest.mark.parametrize("text", NON_EXHIBITOR_BIOS)
def test_non_exhibitor_no_false_positives(text):
    r = parse_comiket_bio(text, C107_CONFIG)
    assert not r.is_exhibitor, f"False positive on: {text!r}"
    assert r.locations == []

def test_low_confidence_day_only():
    text = "C107 1日目"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.confidence == "low"
    assert loc.day == 1
    assert loc.table is None

def test_low_confidence_direction_section_no_table():
    text = "C107 1日目東メ"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.confidence == "low"
    assert loc.day == 1
    assert loc.section == "メ"
    assert loc.table is None

@pytest.mark.parametrize("half_str,expected", [
    ("a", "a"), ("b", "b"), ("ab", "ab"),
    ("A", "a"), ("B", "b"), ("AB", "ab"),
    ("", "ab"),  # missing defaults to ab
])
def test_half_letter_variants(half_str, expected):
    text = f"C107 1日目東メ40{half_str}".strip()
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    assert r.locations[0].half == expected

def test_stray_punctuation_around_section():
    text = 'しま原@2日目西 "め"32ab🐈'
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.section == "め"
    assert loc.table == "32"

def test_hall_number_noise():
    text = "小倉ぽんち❄️C107(火曜日)東7 D-01a"
    r = parse_comiket_bio(text, C107_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.section == "D"
    assert loc.table == "01"
    assert loc.direction == "East"

@pytest.mark.parametrize("text", [
    "C108 土曜日 東7-E44b",
    "C108 東７・Ａ19ab",
])
def test_hall_separator_variants(text):
    r = parse_comiket_bio(text, C108_CONFIG)
    assert r.is_exhibitor
    assert len(r.locations) == 1
    loc = r.locations[0]
    assert loc.hall == "7"
    assert loc.table in {"44", "19"}

def test_c108_config_swap():
    text = "C108 1日目(土)東メ40ab"
    r = parse_comiket_bio(text, C108_CONFIG)
    assert r.is_exhibitor
    loc = r.locations[0]
    assert loc.day == 1
    assert loc.section == "メ"
    assert loc.confidence == "high"

def test_c108_day2_sunday_boundary():
    # Ensure "日" in 日曜 is caught, but bare "日" in 1日目 is not
    text = "C108 1日目東メ40a / 2日目日曜東ア50b"
    r = parse_comiket_bio(text, C108_CONFIG)
    assert len(r.locations) == 2
    assert r.locations[0].day == 1
    assert r.locations[1].day == 2


def test_unrelated_calendar_weekday_does_not_create_comiket_location():
    text = "2026/2/14(土) live event — tickets available"
    r = parse_comiket_bio(text, C108_CONFIG)
    assert not r.is_exhibitor
    assert r.locations == []
