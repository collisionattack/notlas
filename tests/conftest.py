import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# Synthetic note: never put real course material in the tests.
NOTE = """---
course: "Test Kursu"
section: "Bölüm 1 - Giriş"
lecture: "Ders 1 - İlk Ders"
---

# İlk Ders

## Özet
Bu ders testtir. İkinci cümle.

## Konu Bir
Metin.

```python
## kod bloğundaki bu satır başlık değildir
```

## Önemli Kavramlar
| Kavram | Açıklama |
|---|---|
| Alfa (alpha) | Birinci |
| `Beta` | İkinci |

## Dikkat Edilmesi Gerekenler
> ⚠️ Dikkat edilecek bir şey.

## Tekrar Soruları
1. Soru?
"""


@pytest.fixture
def note_text():
    return NOTE


@pytest.fixture
def write_note(tmp_path):
    def _write(text, name="note.md"):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write
