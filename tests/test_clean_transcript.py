from clean_transcript import clean

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
Merhaba <c>arkadaşlar</c>.

2
00:00:03.000 --> 00:00:05.000
Merhaba <c>arkadaşlar</c>.

3
00:00:05.000 --> 00:00:07.000
Bugün 42 tane örnek yapacağız.
"""


def test_drops_cue_numbers_timings_tags_and_repeated_lines():
    assert clean(VTT) == "Merhaba arkadaşlar. Bugün 42 tane örnek yapacağız."


def test_keeps_a_spoken_number_that_is_not_a_cue_index():
    text = "00:00:01.000 --> 00:00:02.000\nCevap\n\n00:00:02.000 --> 00:00:03.000\n42\n"
    assert clean(text) == "Cevap 42"


def test_strips_inline_timestamps():
    assert clean("[00:01:05] Merhaba\n00:01:09 Dünya\n") == "Merhaba Dünya"


def test_splits_long_text_into_paragraphs():
    out = clean(" ".join(["Bu bir cümledir."] * 60))
    assert out.count("\n\n") == 1
