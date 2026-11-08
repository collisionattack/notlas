import build_pdf
import pytest


def test_split_front_matter_reads_quotes_and_legacy_keys():
    text = r'''---
kurs: "Kurs A"
bolum: "Bölüm 1 - X"
ders: "Ders 1 - Say \"merhaba\""
---
# T
'''
    meta, body = build_pdf.split_front_matter(text)

    assert meta == {"course": "Kurs A", "section": "Bölüm 1 - X", "lecture": 'Ders 1 - Say "merhaba"'}
    assert body == "# T\n"


def test_callout_becomes_an_alert_with_its_own_title():
    out = build_pdf.build_alerts("<blockquote>\n<p>💡 Ek not: Bu önemli.</p>\n</blockquote>")

    assert 'class="alert tip"' in out and "Ek not" in out and "Bu önemli." in out
    assert "<blockquote" not in out


def test_plain_blockquote_is_left_alone():
    html = "<blockquote>\n<p>Sıradan alıntı</p>\n</blockquote>"
    assert build_pdf.build_alerts(html) == html


def test_render_html_has_cover_toc_and_escapes_metadata(note_text):
    meta, body = build_pdf.split_front_matter(note_text)
    meta["course"] = "<script>x</script>"
    html = build_pdf.render_html(body, meta, toc=True)

    assert '<section class="cover">' in html and '<section class="toc">' in html
    assert "<script>x</script>" not in html


def test_pdf_is_rendered(tmp_path, note_text):
    pytest.importorskip("weasyprint")
    meta, body = build_pdf.split_front_matter(note_text)
    out = tmp_path / "note.pdf"
    engine, err = build_pdf.render_pdf(build_pdf.render_html(body, meta, toc=True), out)

    if not engine:
        pytest.skip(f"no PDF engine available: {err}")
    assert out.read_bytes().startswith(b"%PDF")
