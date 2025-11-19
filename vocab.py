from PyQt6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLineEdit, QTextEdit, QVBoxLayout, QWidget)

import anki_japanese_helper.anki as anki
import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.keywords as keywords
import anki_japanese_helper.settings as settings


class Vocab:
    def __init__(self, keyword: str, meaning: list[str], create_kanji: bool, create_keyword: bool):
        self.keyword = keyword
        self.meaning = meaning
        self.create_kanji = create_kanji
        self.create_keyword = create_keyword


class AddVocabDialog(QDialog):
    def __init__(self, vocab: Vocab | None = None, parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle("Add Vocab")
        layout = QVBoxLayout()

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._word_edit = QLineEdit()
        self._word_edit.setPlaceholderText("Vocab, e.g., 折[お]り紙[がみ]")
        hbox.addWidget(self._word_edit)

        self._meaning_edit = QTextEdit()
        self._meaning_edit.setPlaceholderText("Meaning")
        self._meaning_edit.setFixedHeight(self._meaning_edit.fontMetrics().lineSpacing() * 4)
        layout.addWidget(self._meaning_edit)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._create_kanji_check = QCheckBox()
        self._create_kanji_check.setText("Kanji Notes")
        self._create_kanji_check.setChecked(True)
        hbox.addWidget(self._create_kanji_check)

        self._create_keyword_check = QCheckBox()
        self._create_keyword_check.setText("Keyword Notes")
        self._create_keyword_check.setChecked(True)
        hbox.addWidget(self._create_keyword_check)

        if vocab:
            self._create_kanji_check.setChecked(vocab.create_kanji)
            self._create_keyword_check.setChecked(vocab.create_keyword)
            self._word_edit.setText(vocab.keyword)
            self._meaning_edit.setText(vocab.meaning)

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)
        self._word_edit.setFocus()

    def getVocab(self) -> Vocab:
        word = self._word_edit.text().strip()
        meaning = list(filter(None, map(lambda t: t.strip(), self._meaning_edit.toPlainText().split("\n"))))

        create_kanji = self._create_kanji_check.isChecked()
        create_keyword = self._create_keyword_check.isChecked()

        return Vocab(word, meaning, create_kanji, create_keyword)


def openDialog(vocab: Vocab | None = None):
    dlg = AddVocabDialog(vocab)
    if not dlg.exec():
        return

    vocab = dlg.getVocab()
    if len(vocab.meaning) == 0:
        anki.notify("No meaning specified")
        return
    if not vocab.keyword:
        anki.notify("No vocab specified")
        return

    # Load settings
    s = settings.get()
    s.beginGroup("vocab_notes")
    dst_deck = s.value("dst_deck", "Default")
    note_type = s.value("note_type", "Basic")

    s.beginGroup("field_names")
    word_field = s.value("word", "Word")
    reading_field = s.value("reading", "Reading")
    meaning_field = s.value("meaning", "Meaning")

    word, reading = "", ""
    letters = keywords.parse(vocab.keyword)
    for c, r in letters:
        if r:
            reading += r
        else:
            reading += c
        word += c

    # Check for duplicate vocabs
    if not anki.anyNotes(dst_deck, note_type, (word_field, word), (reading_field, reading)):
        note = {}
        note[word_field] = word
        note[reading_field] = reading
        note[meaning_field] = "<br>".join(vocab.meaning)

        if anki.uploadNote(note, dst_deck, note_type):
            anki.notify("Note added")
        else:
            anki.notify("Failed to add note")
    else:
        anki.notify("Duplicate note")

    if vocab.create_keyword:
        keywords.openDialog(keywords.Keyword(vocab.keyword, vocab.meaning[0]))

    if vocab.create_kanji:
        s = settings.get()
        s.beginGroup("kanji_notes")
        dst_deck = s.value("dst_deck", "Default")
        note_type = s.value("note_type", "Basic")
        kanji_field = s.value("field_names/kanji", "Kanji")

        all_kanji = set(map(lambda n: n[kanji_field], anki.findNotes(dst_deck, note_type)))
        kanji_set = set(map(lambda k: k[0], filter(lambda k: k[1], letters)))

        for k in kanji_set - all_kanji:
            kanji.openDialog(kanji.Kanji(k, ",".join(all_kanji)))
