import re

import anki_japanese_helper.anki as anki
import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.settings as settings
import anki_japanese_helper.strutil as strutil
from PyQt6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget)


class Vocab:
    def __init__(self, furigana: str, meanings: list[str], create_kanji: bool):
        self.furigana = furigana
        self.meanings = meanings
        self.create_kanji = create_kanji


class VocabDialog(QDialog):
    def __init__(self, vocab: Vocab | None = None, parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle("Add Vocab")
        layout = QVBoxLayout()

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._furigana_edit = QLineEdit()
        self._furigana_edit.setPlaceholderText("Vocab, e.g., 折「お」り紙「がみ」")
        hbox.addWidget(self._furigana_edit)

        self._meanings_edit = QPlainTextEdit()
        self._meanings_edit.setPlaceholderText("Meanings")
        self._meanings_edit.setFixedHeight(self._meanings_edit.fontMetrics().lineSpacing() * 4)
        self._meanings_edit.setTabChangesFocus(True)
        layout.addWidget(self._meanings_edit)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._create_kanji_check = QCheckBox()
        self._create_kanji_check.setText("Kanji Notes")
        self._create_kanji_check.setChecked(True)
        hbox.addWidget(self._create_kanji_check)

        if vocab:
            self._create_kanji_check.setChecked(vocab.create_kanji)
            self._furigana_edit.setText(vocab.furigana)
            self._meanings_edit.setPlainText("\n".join(vocab.meanings))

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)
        self._furigana_edit.setFocus()

    def getVocab(self) -> Vocab:
        furigana = self._furigana_edit.text()
        meanings = strutil.parseList(self._meanings_edit.toPlainText(), "\n")
        create_kanji = self._create_kanji_check.isChecked()

        return Vocab(furigana, meanings, create_kanji)


def parse_furigana(furigana: str) -> list[tuple[str, str]]:
    return re.findall(r"(.)(?:[\[(「]([^\]」)]+)[\]」)])?", furigana)


def normalize_furigana(furigana: str) -> str:
    return re.sub(r"[\[(「]([^\]」)]+)[\]」)]", r"[\g<1>]", furigana)


def openDialog(vocab: Vocab | None = None):
    dlg = VocabDialog(vocab)
    if not dlg.exec():
        return

    vocab = dlg.getVocab()
    if not vocab.meanings:
        anki.notify("No meanings specified")
        return

    furigana = normalize_furigana(vocab.furigana.strip())
    if not furigana:
        anki.notify("No vocab specified")
        return

    word, reading = "", ""
    letters = parse_furigana(furigana)
    for c, r in letters:
        if r:
            reading += r
        else:
            reading += c
        word += c

    value_sep = settings.general.value_sep
    s = settings.vocab_notes

    # Check for duplicate vocabs
    if not anki.anyNotes(s.deck, s.note_type, (s.fields.word, word), (s.fields.reading, reading)):
        note = {}
        note[s.fields.word] = word
        note[s.fields.reading] = reading
        note[s.fields.furigana] = furigana
        note[s.fields.meanings] = value_sep.join(vocab.meanings)

        if anki.uploadNote(note, s.deck, s.note_type):
            anki.notify("Note added")
        else:
            anki.notify("Failed to add a note")
    else:
        anki.notify("Duplicate note")

    if vocab.create_kanji:
        s = settings.kanji_notes

        all_kanji = set(map(lambda n: n[s.fields.kanji], anki.findNotes(s.deck, s.note_type)))
        kanji_set = set(map(lambda k: k[0], filter(lambda k: k[1], letters)))

        for k in kanji_set - all_kanji:
            kanji.openDialog(kanji.Kanji(k, ""))
