from PyQt6.QtCore import QByteArray, QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                             QNetworkRequest)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QLineEdit,
                             QScrollArea, QSizePolicy, QStyle, QVBoxLayout,
                             QWidget)

import anki_japanese_helper.anki as anki
import anki_japanese_helper.settings as settings
import anki_japanese_helper.strutil as strutil
from anki_japanese_helper.ui import (ButtonChip, CounterChip, NoteDialog,
                                     SelectionDialog)

NO_IMAGE_SVG = b"""
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <text x="60%" y="60%" fill="#bbb" font-size="20%"
        text-anchor="middle" alignment-baseline="middle">
    No Image
  </text>
</svg>
"""


class Kanji:
    def __init__(self, char: str, meaning: str):
        self.char = char

        value_delim = settings.general.value_delimiter
        self._meanings = strutil.parse_list(meaning, value_delim)
        self.meaning = (value_delim + " ").join(self._meanings)

    def __str__(self):
        # Only show the first meaning if there are multiple
        return f"{self._meanings[0]} {self.char}"

    def __eq__(self, other):
        return self.char == other.char

    def __lt__(self, other):
        return self.char < other.char


class KanjiComponent:
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
    def __init__(self, kanji: Kanji, components: list[KanjiComponent], strokes: bytes, tags: list[str]):
        self.kanji = kanji
        self.components = components
        self.strokes = strokes
        self.tags = tags


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


class KanjiDialog(NoteDialog):
    def __init__(self, kanji: Kanji | None = None, parent: QWidget = None):
        super().__init__("Add Kanji", anki.tags(), parent)

        self._component_chips = []
        self._kanji = self._loadKanji()
        self._kanji_url = settings.kanji_notes.image_url

        components_grp = QGroupBox("Components")
        components_box = QVBoxLayout(components_grp)
        self.contents().insertWidget(0, components_grp)

        # Get rid of the excessive space at the bottom
        margins = components_box.contentsMargins()
        margins.setTop(0)
        margins.setBottom(0)
        components_box.setContentsMargins(margins)

        # Kanji chips
        components_widget = QWidget()
        self._components_box = QVBoxLayout(components_widget)
        self._components_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(components_widget)
        components_box.addWidget(scroll)

        # "Add component" chip
        btn = ButtonChip("+")
        btn.clicked.connect(self._showComponentsPopup)
        components_box.addWidget(btn)

        # New kanji info
        vbox_widget = QWidget()
        vbox = QVBoxLayout(vbox_widget)
        self.contents().insertWidget(0, vbox_widget)

        self._kanji_edit = QLineEdit()
        self._kanji_edit.textChanged.connect(self._loadKanjiSvg)
        self._kanji_edit.setPlaceholderText("Kanji")
        self._kanji_edit.setFocus()
        vbox.addWidget(self._kanji_edit)

        self._meaning_edit = QLineEdit()
        self._meaning_edit.setPlaceholderText("Meaning")
        vbox.addWidget(self._meaning_edit)

        # Kanji image
        hbox_widget = QWidget()
        hbox = QHBoxLayout(hbox_widget)
        self.contents().insertWidget(0, hbox_widget)

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

        if kanji:
            self._kanji_edit.setText(kanji.char)
            self._meaning_edit.setText(kanji.meaning)

        self.saveLayout(settings.kanji_notes.get_raw_settings())

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

    def _showComponentsPopup(self):
        if not self._kanji:
            anki.notify("No kanji found")
            return

        dlg = SelectionDialog("Add Component", map(str, self._kanji), self)
        selected_idx = dlg.exec()

        k = self._kanji[selected_idx]
        self._createKanjiChip(k)

    def _loadKanji(self) -> list[Kanji]:
        s = settings.kanji_notes

        def read_note(n):
            return Kanji(n[s.fields.kanji], n[s.fields.meaning])
        return sorted(map(read_note, anki.findNotes(s.deck, s.note_type)))

    def _createKanjiChip(self, kanji: Kanji):
        chip = CounterChip(f"{kanji}")

        self._components_box.addWidget(chip)
        self._component_chips.append((kanji, chip))

        def delete_chip(k=kanji, c=chip):
            self._components_box.removeWidget(c)
            c.deleteLater()
            self._component_chips.remove((k, c))

        chip.remove.connect(delete_chip)

    def getKanjiNote(self) -> KanjiNote:
        components = []
        for kanji, counter in self._component_chips:
            components.append(KanjiComponent(kanji, counter.count))

        kanji_char = self._kanji_edit.text()
        kanji = Kanji(kanji_char, self._meaning_edit.text())

        return KanjiNote(kanji, components, self._kanji_svg, self.getNoteTags())


def openDialog(kanji: Kanji | None = None):
    dlg = KanjiDialog(kanji)
    if not dlg.exec():
        return

    note = dlg.getKanjiNote()
    if not note.kanji.char:
        anki.notify("No kanji specified")
        return

    if not note.kanji.meaning:
        anki.notify("No meaning specified")
        return

    strokes_svg = anki.uploadMedia(f"{note.kanji.char}.svg", note.strokes)

    s = settings.kanji_notes
    line_delim = settings.general.line_delimiter

    n = {}
    n[s.fields.kanji] = note.kanji.char.strip()
    n[s.fields.meaning] = note.kanji.meaning
    n[s.fields.components] = line_delim.join(map(str, note.components))
    n[s.fields.strokes] = f"<img src='{strokes_svg}'>"

    if anki.uploadNote(n, s.deck, s.note_type, note.tags):
        anki.notify("Note added")
    else:
        anki.notify("Failed to add a note")
