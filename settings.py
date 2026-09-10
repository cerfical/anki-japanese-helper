import anki_japanese_helper.anki as anki
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLabel, QLayout, QLineEdit,
                             QTabWidget, QVBoxLayout, QWidget)


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

        furigana = property(
            lambda self: self.get_value("furigana", "Furigana"),
            lambda self, v: self.set_value("furigana", v)
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
vocab_notes = VocabNoteSettings("vocab_notes")


class SettingsDialog(QDialog):
    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(parent)

        self._decks = anki.decks()
        self._note_types = anki.noteTypes()
        self.setWindowTitle(title)
        layout = QVBoxLayout()

        tabs = QTabWidget()
        layout.addWidget(tabs)

        gnrl_layout = self._createGeneralSettings()
        tabs.addTab(self._wrapLayout(gnrl_layout), "General")

        kanji_notes_layout = self._createNoteSettings(
            ["Kanji", "Meanings", "Components", "Strokes"],
            kanji_notes
        )
        self._createLabeledEdit("Kanji SVG URL", kanji_notes_layout, kanji_notes, "kanji_url")
        tabs.addTab(self._wrapLayout(kanji_notes_layout), "Kanji Notes")

        vocab_notes_layout = self._createNoteSettings(
            ["Word", "Reading", "Furigana", "Meanings"],
            vocab_notes
        )
        tabs.addTab(self._wrapLayout(vocab_notes_layout), "Vocab Notes")

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)

    def _createGeneralSettings(self) -> QLayout:
        layout = QVBoxLayout()
        self._createLabeledEdit("Value Separator", layout, general, "value_sep")

        layout.addStretch()
        return layout

    def _createNoteSettings(self, fields: list[str], settings: NoteSettings) -> QLayout:
        note_layout = QVBoxLayout()

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

        note_layout.addStretch()
        return note_layout

    def _wrapLayout(self, layout: QLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

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


def openDialog():
    dlg = SettingsDialog("Settings")
    if dlg.exec():
        anki.notify("Settings updated")
