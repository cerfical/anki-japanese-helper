import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLineEdit, QListWidget,
                             QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget)

import anki_japanese_helper.anki as anki
import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.settings as settings
import anki_japanese_helper.strutil as strutil
from anki_japanese_helper.ui import ButtonChip, TextChip


class Vocab:
    def __init__(self, furigana: str, meanings: list[str]):
        self.furigana = furigana
        self.meanings = meanings


class VocabNote:
    def __init__(self, vocab: Vocab, tags: list[str], add_kanji: bool):
        self.vocab = vocab
        self.tags = tags
        self.add_kanji = add_kanji


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

        if vocab:
            self._furigana_edit.setText(vocab.furigana)
            self._meanings_edit.setPlainText("\n".join(vocab.meanings))

        tags_grp = QGroupBox("Tags")
        tags_box = QVBoxLayout(tags_grp)
        layout.addWidget(tags_grp)

        # Tag chips
        tags_widget = QWidget()
        self._tags_box = QVBoxLayout(tags_widget)
        self._tags_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tags_widget)
        tags_box.addWidget(scroll)

        # "Add tag" chip
        btn = ButtonChip("+")
        btn.clicked.connect(self._showTagsPopup)
        tags_box.addWidget(btn)

        self._add_kanji_check = QCheckBox()
        self._add_kanji_check.setText("Add Kanji")
        self._add_kanji_check.setChecked(True)
        layout.addWidget(self._add_kanji_check)

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._all_tags = anki.tags()
        self._tags = []

        self.setLayout(layout)
        self._furigana_edit.setFocus()

    def getVocabNote(self) -> VocabNote:
        furigana = self._furigana_edit.text()
        meanings = strutil.parseList(self._meanings_edit.toPlainText(), "\n")

        add_kanji = self._add_kanji_check.isChecked()
        vocab = Vocab(furigana, meanings)

        return VocabNote(vocab, self._tags, add_kanji)

    def _showTagsPopup(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Tag")
        dlg.setWindowFlags(Qt.WindowType.Popup)

        layout = QVBoxLayout(dlg)

        search = QLineEdit()
        search.setPlaceholderText("Search for...")
        layout.addWidget(search)

        list_widget = QListWidget()
        list_widget.addItems(self._all_tags)
        layout.addWidget(list_widget)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search.textChanged.connect(filter_items)
        search.setFocus()

        def item_selected(item):
            t = self._all_tags[list_widget.row(item)]
            self._createTagChip(t)
            dlg.close()

        list_widget.itemClicked.connect(item_selected)
        dlg.exec()

    def _createTagChip(self, tag: str):
        chip = TextChip(tag)

        self._tags_box.addWidget(chip)
        self._tags.append(tag)

        def delete_chip(t=tag, c=chip):
            self._tags_box.removeWidget(c)
            c.deleteLater()
            self._tags.remove(t)

        chip.remove.connect(delete_chip)


def parse_furigana(furigana: str) -> list[tuple[str, str]]:
    return re.findall(r"(.)(?:[\[(「]([^\]」)]+)[\]」)])?", furigana)


def normalize_furigana(furigana: str) -> str:
    return re.sub(r"[\[(「]([^\]」)]+)[\]」)]", r"[\g<1>]", furigana)


def openDialog(vocab: Vocab | None = None):
    dlg = VocabDialog(vocab)
    if not dlg.exec():
        return

    note = dlg.getVocabNote()
    if not note.vocab.meanings:
        anki.notify("No meanings specified")
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

    value_sep = settings.general.value_sep
    s = settings.vocab_notes

    # Check for duplicate vocabs
    if not anki.anyNotes(s.deck, s.note_type, (s.fields.word, word), (s.fields.reading, reading)):
        n = {}
        n[s.fields.word] = word
        n[s.fields.reading] = reading
        n[s.fields.furigana] = furigana
        n[s.fields.meanings] = value_sep.join(note.vocab.meanings)

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
