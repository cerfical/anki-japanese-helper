import anki_japanese_helper.anki as anki
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLabel, QLayout, QLineEdit,
                             QScrollArea, QVBoxLayout, QWidget)


class Settings:
    def __init__(self, group: str):
        self._settings = QSettings(anki.ADDON_ID)
        self._settings.beginGroup(group)

    def set_value(self, key: str, value: str):
        self._settings.setValue(key, value)

    def get_value(self, key: str, default: str = "") -> str:
        return self._settings.value(key, default)


class GeneralSettings(Settings):
    def __init__(self, group: str):
        super().__init__(group)

    def set_value_sep(self, delim: str):
        self.set_value("value_sep", delim)

    def get_value_sep(self) -> str:
        return self.get_value("value_sep", "; ")

    value_sep = property(get_value_sep, set_value_sep)


class NoteSettings(Settings):
    def __init__(self, group: str):
        super().__init__(group)

    def set_deck(self, deck: str):
        self.set_value("deck", deck)

    def get_deck(self) -> str:
        return self.get_value("deck", "Default")

    def set_note_type(self, note: str):
        self.set_value("note", note)

    def get_note_type(self) -> str:
        return self.get_value("note", "Basic")

    deck = property(get_deck, set_deck)
    note_type = property(get_note_type, set_note_type)


class KanjiNoteSettings(NoteSettings):
    class FieldSettings(Settings):
        def __init__(self, group: str):
            super().__init__(group)

        kanji = property(
            lambda self: self.get_value("kanji", "Kanji"),
            lambda self, v: self.set_value("kanji", v)
        )

        meanings = property(
            lambda self: self.get_value("meanings", "Meanings"),
            lambda self, v: self.set_value("meanings", v)
        )

        components = property(
            lambda self: self.get_value("components", "Components"),
            lambda self, v: self.set_value("components", v)
        )

        strokes = property(
            lambda self: self.get_value("strokes", "Strokes"),
            lambda self, v: self.set_value("strokes", v)
        )

    def __init__(self, group: str):
        super().__init__(group)

        self.fields = KanjiNoteSettings.FieldSettings(f"{group}/fields")

    def set_kanji_url(self, url: str):
        kanji_url = url.strip().rstrip("/") + "/"
        self.set_value("kanji_url", kanji_url)

    def get_kanji_url(self) -> str:
        return self.get_value("kanji_url")

    kanji_url = property(get_kanji_url, set_kanji_url)


class KeywordNoteSettings(NoteSettings):
    class FieldSettings(Settings):
        def __init__(self, group: str):
            super().__init__(group)

        kanji = property(
            lambda self: self.get_value("kanji", "Kanji"),
            lambda self, v: self.set_value("kanji", v)
        )

        reading = property(
            lambda self: self.get_value("reading", "Reading"),
            lambda self, v: self.set_value("reading", v)
        )

        keyword = property(
            lambda self: self.get_value("keyword", "Keyword"),
            lambda self, v: self.set_value("keyword", v)
        )

        meaning = property(
            lambda self: self.get_value("meaning", "Meaning"),
            lambda self, v: self.set_value("meaning", v)
        )

    def __init__(self, group: str):
        super().__init__(group)

        self.fields = KeywordNoteSettings.FieldSettings(f"{group}/fields")


class VocabNoteSettings(NoteSettings):
    class FieldSettings(Settings):
        def __init__(self, group: str):
            super().__init__(group)

        word = property(
            lambda self: self.get_value("word", "Word"),
            lambda self, v: self.set_value("word", v)
        )

        reading = property(
            lambda self: self.get_value("reading", "Reading"),
            lambda self, v: self.set_value("reading", v)
        )

        meanings = property(
            lambda self: self.get_value("meanings", "Meanings"),
            lambda self, v: self.set_value("meanings", v)
        )

    def __init__(self, group: str):
        super().__init__(group)

        self.fields = VocabNoteSettings.FieldSettings(f"{group}/fields")


general = GeneralSettings("general")

kanji_notes = KanjiNoteSettings("kanji_notes")
keyword_notes = KeywordNoteSettings("keyword_notes")
vocab_notes = VocabNoteSettings("vocab_notes")


class SettingsDialog(QDialog):
    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle(title)
        layout = QVBoxLayout()
        scroll_layout = self._createScroll(layout)

        self._decks = anki.decks()
        self._note_types = anki.noteTypes()

        gnrl_box = self._createGroup("General", scroll_layout)
        self._createLabeledEdit("Value Separator", gnrl_box, general, "value_sep")

        kanji_note_layout = self._createNoteSettings(
            "Kanji Notes",
            ["Kanji", "Meanings", "Components", "Strokes"],
            scroll_layout,
            kanji_notes
        )
        self._createLabeledEdit("Kanji SVG URL", kanji_note_layout, kanji_notes, "kanji_url")

        self._createNoteSettings(
            "Keyword Notes",
            ["Kanji", "Reading", "Keyword", "Meaning"],
            scroll_layout,
            keyword_notes
        )

        self._createNoteSettings(
            "Vocab Notes",
            ["Word", "Meanings", "Reading"],
            scroll_layout,
            vocab_notes
        )

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)

    def _createNoteSettings(self, grp: str, fields: list[str], layout: QLayout, settings: NoteSettings) -> QLayout:
        note_layout = self._createGroup(grp, layout)

        hbox = QHBoxLayout()
        note_layout.addLayout(hbox)

        self._createLabeledCombo("Deck", self._decks, hbox, settings, "deck")

        note_combo = self._createLabeledCombo("Note Type", self._note_types, hbox, settings, "note_type")
        note_fields = anki.findFields(settings.note_type)

        field_layout = self._createGroup("Fields", note_layout)
        for field in fields:
            field_settings = getattr(settings, "fields")
            field_name = field.strip().lower().replace(" ", "_")

            field_combo = self._createLabeledCombo(field, note_fields, field_layout, field_settings, field_name)

            def reload_fields(note_type, fn=field_name, c=field_combo):
                c.clear()
                c.addItems(anki.findFields(note_type))
                c.setCurrentText(getattr(field_settings, fn))
            note_combo.currentTextChanged.connect(reload_fields)

        return note_layout

    def _createGroup(self, name: str, layout: QLayout) -> QLayout:
        grp = QGroupBox(name)
        vbox = QVBoxLayout(grp)
        layout.addWidget(grp)
        return vbox

    def _createLabeledCombo(self, label: str, values: list[str], layout: QLayout, settings: Settings, setting_name: str) -> QComboBox:
        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        hbox.addWidget(QLabel(label))

        field_combo = QComboBox()
        hbox.addWidget(field_combo)

        field_combo.addItems(values)
        field_combo.setCurrentText(getattr(settings, setting_name))
        self.accepted.connect(lambda: setattr(settings, setting_name, field_combo.currentText()))

        return field_combo

    def _createLabeledEdit(self, label: str, layout: QLayout, settings: Settings, setting_name: str) -> QLineEdit:
        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        hbox.addWidget(QLabel(label))

        line_edit = QLineEdit()
        hbox.addWidget(line_edit)

        line_edit.setText(getattr(settings, setting_name))
        self.accepted.connect(lambda: setattr(settings, setting_name, line_edit.text()))

        return line_edit

    def _createScroll(self, layout: QLayout) -> QLayout:
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        scroll_container = QWidget()
        scroll.setWidget(scroll_container)

        scroll_layout = QVBoxLayout()
        scroll_container.setLayout(scroll_layout)
        return scroll_layout


def openDialog():
    dlg = SettingsDialog("Settings")
    if dlg.exec():
        anki.notify("Settings updated")
