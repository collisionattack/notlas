import json
from pathlib import Path

import pytest

import save_note


def test_h2_headings_skip_code_fences(note_text):
    assert save_note.h2_headings(note_text) == [
        "Özet", "Konu Bir", "Önemli Kavramlar", "Dikkat Edilmesi Gerekenler", "Tekrar Soruları"]


def test_extracts_summary_topics_and_concepts(note_text):
    assert save_note.extract_summary(note_text) == "Bu ders testtir. İkinci cümle."
    assert save_note.extract_topics(note_text) == ["Konu Bir"]
    assert save_note.extract_concepts(note_text) == ["Alfa (alpha)", "Beta"]


def test_validate_accepts_a_well_formed_note(note_text):
    assert save_note.validate(note_text, Path("note.md")) == []


def test_validate_flags_a_misspelled_fixed_heading(note_text):
    problems = save_note.validate(note_text.replace("## Özet", "## Ders Özeti"), Path("note.md"))
    assert any("must be spelled exactly '## Özet'" in p for p in problems)


def test_validate_requires_a_concept_table():
    md = "# T\n\n## Özet\nx\n\n## Önemli Kavramlar\nTablo yok.\n"
    assert any("Önemli Kavramlar" in p for p in save_note.validate(md, Path("note.md")))


def test_save_writes_note_and_indexes(tmp_path, write_note, note_text):
    root = tmp_path / "courses"
    md, pdf, total = save_note.save(write_note(note_text), root, pdf=False)

    assert md == root / "test-kursu" / "notes" / "01-giris" / "001-ilk-ders.md"
    assert pdf is None and total == 1
    index = (root / "test-kursu" / "INDEX.md").read_text(encoding="utf-8")
    assert "Bu ders testtir" in index and "Konu Bir" in index and "Alfa (alpha)" in index
    data = json.loads((root / "test-kursu" / "course.json").read_text(encoding="utf-8"))
    assert [d["lecture"] for d in data["lectures"]] == ["İlk Ders"]
    assert "test-kursu/INDEX.md" in (root / "README.md").read_text(encoding="utf-8")
    assert save_note.course_overview(root) == [
        "test-kursu | Test Kursu | 1 ders | son: Bölüm 1 - Giriş / Ders 1 - İlk Ders"]


def test_saving_the_same_lecture_again_updates_it_in_place(tmp_path, write_note, note_text):
    root = tmp_path / "courses"
    save_note.save(write_note(note_text), root, pdf=False)
    md, _, total = save_note.save(write_note(note_text + "\nEk satır.\n", "again.md"), root, pdf=False)

    assert total == 1
    assert "Ek satır." in md.read_text(encoding="utf-8")


def test_refuses_to_replace_a_different_lecture_at_the_same_path(tmp_path, write_note, note_text):
    root = tmp_path / "courses"
    save_note.save(write_note(note_text), root, pdf=False)
    other_section = note_text.replace("Bölüm 1 - Giriş", "Bölüm 1 - Giris")  # same folder slug

    with pytest.raises(SystemExit, match="different lecture"):
        save_note.save(write_note(other_section, "other.md"), root, pdf=False)
    save_note.save(write_note(other_section, "other.md"), root, pdf=False, overwrite=True)


def test_refuses_a_new_course_that_looks_like_an_existing_one(tmp_path, write_note, note_text):
    root = tmp_path / "courses"
    save_note.save(write_note(note_text.replace("Test Kursu", "Docker ve Kubernetes")), root, pdf=False)
    similar = note_text.replace("Test Kursu", "Docker Kubernetes Egitimi")

    with pytest.raises(SystemExit, match="similar courses"):
        save_note.save(write_note(similar, "similar.md"), root, pdf=False)
    save_note.save(write_note(similar, "similar.md"), root, pdf=False, new_course=True)
    assert len(save_note.list_courses(root)) == 2


def test_reindex_keeps_missing_entries_unless_pruned(tmp_path, write_note, note_text):
    root = tmp_path / "courses"
    md, _, _ = save_note.save(write_note(note_text), root, pdf=False)
    md.unlink()
    course_dir = root / "test-kursu"

    assert len(save_note.rebuild_course(course_dir)["lectures"]) == 1  # a partial copy must not shrink the index
    assert len(save_note.rebuild_course(course_dir, prune=True)["lectures"]) == 0
