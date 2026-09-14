import re

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QVBoxLayout, QWidget

import anki_japanese_helper.anki as anki
import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.settings as settings
import anki_japanese_helper.strutil as strutil
from anki_japanese_helper.ui import NoteDialog


class Vocab:
    def __init__(self, furigana: str, meaning: str):
        self.furigana = furigana

        value_delim = settings.general.value_delimiter
        meanings = strutil.parse_list(meaning, value_delim)
        self.meaning = (value_delim + " ").join(meanings)


class VocabNote:
    def __init__(self, vocab: Vocab, add_kanji: bool, tags: list[str]):
        self.vocab = vocab
        self.add_kanji = add_kanji
        self.tags = tags


class VocabDialog(NoteDialog):
    def __init__(self, vocab: Vocab | None = None, parent: QWidget = None):
        super().__init__("Add Vocab", anki.tags(), parent)

        vbox_widget = QWidget()
        vbox = QVBoxLayout(vbox_widget)
        self.contents().insertWidget(0, vbox_widget)

        self._furigana_edit = QLineEdit()
        self._furigana_edit.setPlaceholderText("Vocab, e.g., 折「お」り紙「がみ」")
        self._furigana_edit.setFocus()
        vbox.addWidget(self._furigana_edit)

        self._meaning_edit = QLineEdit()
        self._meaning_edit.setPlaceholderText("Meaning")
        vbox.addWidget(self._meaning_edit)

        self._add_kanji_check = QCheckBox()
        self._add_kanji_check.setText("Add Kanji")
        self._add_kanji_check.setChecked(True)
        vbox.addWidget(self._add_kanji_check)

        if vocab:
            self._furigana_edit.setText(vocab.furigana)
            self._meaning_edit.setText(vocab.meaning)

        self.saveLayout(settings.vocab_notes.get_raw_settings())

    def getVocabNote(self) -> VocabNote:
        furigana = self._furigana_edit.text()
        add_kanji = self._add_kanji_check.isChecked()
        vocab = Vocab(furigana, self._meaning_edit.text())

        return VocabNote(vocab, add_kanji, self.getNoteTags())


def parse_furigana(furigana: str) -> list[tuple[str, str]]:
    return re.findall(r"(.)(?:[\[(「]([^\]」)]+)[\]」)])?", furigana)


def normalize_furigana(furigana: str) -> str:
    return re.sub(r"[\[(「]([^\]」)]+)[\]」)]", r"[\g<1>]", furigana)


def openDialog(vocab: Vocab | None = None):
    dlg = VocabDialog(vocab)
    if not dlg.exec():
        return

    note = dlg.getVocabNote()
    if not note.vocab.meaning:
        anki.notify("No meaning specified")
        return

    furigana = normalize_furigana(note.vocab.furigana.strip())
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

    # Check for duplicate vocabs
    s = settings.vocab_notes
    if not anki.anyNotes(s.deck, s.note_type, (s.fields.word, word), (s.fields.reading, reading)):
        n = {}
        n[s.fields.word] = word
        n[s.fields.reading] = reading
        n[s.fields.furigana] = furigana
        n[s.fields.meaning] = note.vocab.meaning

        if anki.uploadNote(n, s.deck, s.note_type, note.tags):
            anki.notify("Note added")
        else:
            anki.notify("Failed to add a note")
    else:
        anki.notify("Duplicate note")

    if note.add_kanji:
        s = settings.kanji_notes

        all_kanji = set(map(lambda n: n[s.fields.kanji], anki.findNotes(s.deck, s.note_type)))
        kanji_set = set(map(lambda k: k[0], filter(lambda k: k[1], letters)))

        for k in kanji_set - all_kanji:
            kanji.openDialog(kanji.Kanji(k, ""))
