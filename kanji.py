import anki_japanese_helper.anki as anki
import anki_japanese_helper.settings as settings
import anki_japanese_helper.strutil as strutil
from anki_japanese_helper.ui import ButtonChip, CounterChip, FlowLayout
from PyQt6.QtCore import QByteArray, QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                             QNetworkRequest)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QGroupBox,
                             QHBoxLayout, QLineEdit, QListWidget,
                             QPlainTextEdit, QScrollArea, QSizePolicy, QStyle,
                             QVBoxLayout, QWidget)

NO_IMAGE_SVG = b"""
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <text x="60%" y="60%" fill="#bbb" font-size="20%"
        text-anchor="middle" alignment-baseline="middle">
    No Image
  </text>
</svg>
"""


class Kanji:
    def __init__(self, char: str, meanings: list[str]):
        self.char = char
        self.meanings = meanings

    def __str__(self):
        # Only show the first meaning if there are multiple
        return f"{self.meanings[0]} {self.char}"

    def __eq__(self, other):
        return self.char == other.char

    def __lt__(self, other):
        return self.char < other.char


class KanjiPart:
    def __init__(self, kanji: Kanji, count: int):
        self.kanji = kanji
        self.count = count

    def __str__(self):
        return f'{self.kanji}{"" if self.count == 1 else f" ×{self.count}"}'

    def __eq__(self, other):
        return (self.kanji, self.count) == (other.kanji, other.count)

    def __lt__(self, other):
        return (self.kanji, self.count) < (other.kanji, other.count)


class KanjiNote:
    def __init__(self, kanji: Kanji, parts: list[KanjiPart], strokes: bytes):
        self.kanji = kanji
        self.parts = parts
        self.strokes = strokes


class SvgLoader(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._reply = None
        self._manager = QNetworkAccessManager(self)
        self._manager.finished.connect(self._onFinished)

    def load(self, url: QUrl):
        # Cancel any pending requests
        if self._reply:
            self._reply.abort()
            self._reply.deleteLater()
        request = QNetworkRequest(url)
        self._reply = self._manager.get(request)

    def _onFinished(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            anki.notify("Failed to load SVG")
            return
        data = reply.readAll()
        self.finished.emit(bytes(data))

    finished = pyqtSignal(bytes)


class KanjiDialog(QDialog):
    def __init__(self, kanji: Kanji | None = None, parent: QWidget = None):
        super().__init__(parent)

        self._kanji_parts = []
        self._kanji = self._loadKanji()
        self._kanji_url = settings.kanji_notes.kanji_url

        self.setWindowTitle("Add Kanji")
        layout = QVBoxLayout()

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self._kanji_svg_widget = QSvgWidget()
        self._kanji_svg_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setKanjiSvg(NO_IMAGE_SVG)
        hbox.addWidget(self._kanji_svg_widget)

        self._svg_loader = SvgLoader(self)
        self._svg_loader.finished.connect(self._setKanjiSvg)

        vbox = QVBoxLayout()
        hbox.addLayout(vbox)

        reload_btn = ButtonChip()
        reload_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        reload_btn.clicked.connect(self._loadKanjiSvg)
        vbox.addWidget(reload_btn)

        open_btn = ButtonChip()
        open_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        open_btn.clicked.connect(self._chooseKanjiSvg)
        vbox.addWidget(open_btn)

        # New kanji info
        self._kanji_edit = QLineEdit()
        self._kanji_edit.textChanged.connect(self._loadKanjiSvg)
        self._kanji_edit.setPlaceholderText("Kanji")
        layout.addWidget(self._kanji_edit)

        self._meanings_edit = QPlainTextEdit()
        self._meanings_edit.setPlaceholderText("Meanings")
        self._meanings_edit.setFixedHeight(self._meanings_edit.fontMetrics().lineSpacing() * 4)
        self._meanings_edit.setTabChangesFocus(True)
        layout.addWidget(self._meanings_edit)

        if kanji:
            self._kanji_edit.setText(kanji.char)
            self._meanings_edit.setPlainText("\n".join(kanji.meanings))

        parts_grp = QGroupBox("Components")
        parts_box = QVBoxLayout(parts_grp)
        layout.addWidget(parts_grp)

        # Kanji chips
        parts_widget = QWidget()
        self._kanji_layout = FlowLayout(parts_widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(parts_widget)
        parts_box.addWidget(scroll)

        # "Add component" chip
        self._add_kanji_chip = ButtonChip("+")
        self._add_kanji_chip.clicked.connect(self._showComponentPopup)
        self._kanji_layout.addWidget(self._add_kanji_chip)

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)
        self._kanji_edit.setFocus()

    def _loadKanjiSvg(self):
        kanji = self._kanji_edit.text().strip()
        if len(kanji) == 1:
            kanji_url = QUrl(self._kanji_url).resolved(QUrl(f"0{ord(kanji):04x}.svg"))
            self._svg_loader.load(kanji_url)
        else:
            self._setKanjiSvg(NO_IMAGE_SVG)

    def _chooseKanjiSvg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose SVG Image", "", "SVG Files (*.svg)")
        if not path:
            anki.notify("Invalid filepath")
            return

        with open(path, "rb") as f:
            data = f.read()
            self._setKanjiSvg(data)

    def _setKanjiSvg(self, svg_bytes: bytes):
        self._kanji_svg_widget.load(QByteArray(svg_bytes))
        self._kanji_svg_widget.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self._kanji_svg = svg_bytes

    def _showComponentPopup(self):
        if not self._kanji:
            anki.notify("No kanji found")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Add Component")
        dlg.setWindowFlags(Qt.WindowType.Popup)

        layout = QVBoxLayout(dlg)

        search = QLineEdit()
        search.setPlaceholderText("Search for...")
        layout.addWidget(search)

        list_widget = QListWidget()
        list_widget.addItems(map(str, self._kanji))
        layout.addWidget(list_widget)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search.textChanged.connect(filter_items)
        search.setFocus()

        def item_selected(item):
            k = self._kanji[list_widget.row(item)]
            self._createKanjiChip(k)
            dlg.close()

        list_widget.itemClicked.connect(item_selected)
        dlg.exec()

    def _loadKanji(self) -> list[Kanji]:
        value_sep = settings.general.value_sep
        s = settings.kanji_notes

        def read_note(n):
            return Kanji(n[s.fields.kanji], strutil.parseList(n[s.fields.meanings], value_sep))

        return sorted(map(read_note, anki.findNotes(s.deck, s.note_type)))

    def _createKanjiChip(self, kanji: Kanji):
        chip = CounterChip(f"{kanji}")

        # Remove the "add component" chip and add it back later to the end of the list
        self._kanji_layout.takeAt(self._kanji_layout.count() - 1)
        self._kanji_layout.addWidget(chip)
        self._kanji_layout.addWidget(self._add_kanji_chip)
        self._kanji_parts.append((kanji, chip))

        def delete_chip(k=kanji, c=chip):
            self._kanji_layout.removeWidget(c)
            c.deleteLater()
            self._kanji_parts.remove((k, c))

        chip.remove.connect(delete_chip)

    def getKanjiNote(self) -> KanjiNote:
        parts = []
        for kanji, counter in self._kanji_parts:
            parts.append(KanjiPart(kanji, counter.count))

        kanji_char = self._kanji_edit.text()
        meanings = strutil.parseList(self._meanings_edit.toPlainText(), "\n")
        kanji = Kanji(kanji_char, meanings)

        return KanjiNote(kanji, parts, self._kanji_svg)


def openDialog(kanji: Kanji | None = None):
    dlg = KanjiDialog(kanji)
    if not dlg.exec():
        return

    note = dlg.getKanjiNote()
    if not note.kanji.char:
        anki.notify("No kanji specified")
        return

    if not note.kanji.meanings:
        anki.notify("No meanings specified")
        return

    strokes_svg = anki.uploadMedia(f"{note.kanji.char}.svg", note.strokes)

    value_sep = settings.general.value_sep
    s = settings.kanji_notes

    n = {}
    n[s.fields.kanji] = note.kanji.char.strip()
    n[s.fields.meanings] = value_sep.join(note.kanji.meanings)
    n[s.fields.components] = value_sep.join(map(str, note.parts))
    n[s.fields.strokes] = f"<img src='{strokes_svg}'>"

    if anki.uploadNote(n, s.deck, s.note_type):
        anki.notify("Note added")
    else:
        anki.notify("Failed to add a note")
