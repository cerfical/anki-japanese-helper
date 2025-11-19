import re

from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLineEdit,
                             QVBoxLayout, QWidget)

import anki_japanese_helper.anki as anki
import anki_japanese_helper.settings as settings


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
    return re.findall(r"(.)(?:\[([^\]]+)\])?", word)


def openDialog(keyword: Keyword | None = None):
    dlg = KeywordDialog(keyword)
    if not dlg.exec():
        return

    # Load settings
    s = settings.get()
    s.beginGroup("keyword_notes")
    dst_deck = s.value("dst_deck", "Default")
    note_type = s.value("note_type", "Basic")

    s.beginGroup("field_names")
    kanji_field_name = s.value("kanji", "Kanji")
    reading_field_name = s.value("reading", "Reading")
    keyword_field_name = s.value("keyword", "Keyword")
    meaning_field_name = s.value("meaning", "Meaning")

    keyword = dlg.getKeyword()
    kanji = parse(keyword.vocab)

    # For each unique kanji reading, create a card
    note_count = 0
    for char, reading in filter(lambda k: k[1], kanji):
        # Check for duplicate kanji readings
        if anki.anyNotes(dst_deck, note_type, (kanji_field_name, char), (reading_field_name, reading)):
            continue

        note = {}
        note[kanji_field_name] = char
        note[reading_field_name] = reading
        note[keyword_field_name] = keyword.vocab
        note[meaning_field_name] = keyword.meaning

        if anki.uploadNote(note, dst_deck, note_type):
            note_count += 1

    anki.notify(f"Added {note_count} note(s)")
