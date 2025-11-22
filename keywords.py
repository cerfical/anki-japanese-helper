import re

import anki_japanese_helper.anki as anki
import anki_japanese_helper.settings as settings
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLineEdit,
                             QVBoxLayout, QWidget)


class Keyword:
    def __init__(self, vocab: str, meaning: str):
        self.vocab = vocab
        self.meaning = meaning


class KeywordDialog(QDialog):
    def __init__(self, keyword: Keyword | None = None, parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle("Add Keyword")
        layout = QVBoxLayout()

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._keyword_edit = QLineEdit()
        self._keyword_edit.setPlaceholderText("Vocab, e.g., 折[お]り紙[がみ]")
        hbox.addWidget(self._keyword_edit)

        self._meaning_edit = QLineEdit()
        self._meaning_edit.setPlaceholderText("Meaning")
        hbox.addWidget(self._meaning_edit)

        if keyword:
            self._keyword_edit.setText(keyword.vocab)
            self._meaning_edit.setText(keyword.meaning)

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)
        self._keyword_edit.setFocus()

    def getKeyword(self) -> Keyword:
        return Keyword(self._keyword_edit.text().strip(), self._meaning_edit.text().strip())


def parse(word: str) -> list[tuple[str, str]]:
    return re.findall(r"(.)(?:[\[(「]([^\]」)]+)[\]」)])?", word)


def normalize(word: str) -> str:
    return re.sub(r"[\[(「]([^\]」)]+)[\]」)]", r"「\g<1>」", word)


def openDialog(keyword: Keyword | None = None):
    dlg = KeywordDialog(keyword)
    if not dlg.exec():
        return
    s = settings.keyword_notes

    keyword = dlg.getKeyword()
    kanji = parse(keyword.vocab)

    # For each unique kanji reading, create a card
    note_count, total_count, failed_count = 0, 0, 0
    for char, reading in filter(lambda k: k[1], kanji):
        total_count += 1

        # Check for duplicate kanji readings
        if anki.anyNotes(s.deck, s.note_type, (s.fields.kanji, char), (s.fields.reading, reading)):
            continue

        note = {}
        note[s.fields.kanji] = char
        note[s.fields.reading] = reading
        note[s.fields.keyword] = normalize(keyword.vocab)
        note[s.fields.meaning] = keyword.meaning

        if anki.uploadNote(note, s.deck, s.note_type):
            note_count += 1
        else:
            failed_count += 1

    anki.notify(
        f"Added {note_count} note(s), {total_count - note_count - failed_count} duplicate(s), {failed_count} failed"
    )
