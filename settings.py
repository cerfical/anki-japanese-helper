from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                             QGroupBox, QLayout, QLineEdit, QTabWidget,
                             QVBoxLayout, QWidget)

import anki_japanese_helper.anki as anki


class Settings:
    def __init__(self, group: str):
        self._settings = QSettings(anki.ADDON_ID)
        self._settings.beginGroup(group)

    def _set_raw_value(self, key: str, value: str):
        self._settings.setValue(key, value)

    def _get_raw_value(self, key: str, default: str) -> str:
        return self._settings.value(key, default)

    def get_raw_settings(self) -> QSettings:
        return self._settings

    def get_setting(self, key: str) -> str:
        key = key.lower().replace(" ", "_")
        return getattr(self, key)

    def set_setting(self, key: str, value: str):
        key = key.lower().replace(" ", "_")
        setattr(self, key, value)


class GeneralSettings(Settings):
    value_delimiter = property(
        lambda self: self._get_raw_value("value_delimiter", ";"),
        lambda self, v: self._set_raw_value("value_delimiter", v)
    )

    line_delimiter = property(
        lambda self: self._get_raw_value("line_delimiter", "<br>"),
        lambda self, v: self._set_raw_value("line_delimiter", v)
    )


class NoteSettings(Settings):
    deck = property(
        lambda self: self._get_raw_value("deck", "Default"),
        lambda self, v: self._set_raw_value("deck", v)
    )

    note_type = property(
        lambda self: self._get_raw_value("note", "Basic"),
        lambda self, v: self._set_raw_value("note", v)
    )


class KanjiNoteSettings(NoteSettings):
    class FieldSettings(Settings):
        kanji = property(
            lambda self: self._get_raw_value("kanji", "Kanji"),
            lambda self, v: self._set_raw_value("kanji", v)
        )

        meaning = property(
            lambda self: self._get_raw_value("meaning", "Meaning"),
            lambda self, v: self._set_raw_value("meaning", v)
        )

        components = property(
            lambda self: self._get_raw_value("components", "Components"),
            lambda self, v: self._set_raw_value("components", v)
        )

        strokes = property(
            lambda self: self._get_raw_value("strokes", "Strokes"),
            lambda self, v: self._set_raw_value("strokes", v)
        )

    def __init__(self, group: str):
        super().__init__(group)

        self.fields = KanjiNoteSettings.FieldSettings(f"{group}/fields")

    image_url = property(
        lambda self: self._get_raw_value("image_url", ""),
        lambda self, v: self._set_raw_value("image_url", v.strip().rstrip("/") + "/")
    )


class VocabNoteSettings(NoteSettings):
    class FieldSettings(Settings):
        word = property(
            lambda self: self._get_raw_value("word", "Word"),
            lambda self, v: self._set_raw_value("word", v)
        )

        reading = property(
            lambda self: self._get_raw_value("reading", "Reading"),
            lambda self, v: self._set_raw_value("reading", v)
        )

        furigana = property(
            lambda self: self._get_raw_value("furigana", "Furigana"),
            lambda self, v: self._set_raw_value("furigana", v)
        )

        meaning = property(
            lambda self: self._get_raw_value("meaning", "Meaning"),
            lambda self, v: self._set_raw_value("meaning", v)
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

        general_layout = self._createGeneralSettings()
        tabs.addTab(self._wrapLayout(general_layout), "General")

        kanji_notes_layout = self._createNoteSettings(
            ["Kanji", "Meaning", "Components", "Strokes"],
            kanji_notes
        )

        form = QFormLayout()
        self._createTextSetting("Image URL", kanji_notes, form)
        kanji_notes_layout.addLayout(form)

        tabs.addTab(self._wrapLayout(kanji_notes_layout), "Kanji Notes")

        vocab_notes_layout = self._createNoteSettings(
            ["Word", "Meaning", "Reading", "Furigana"],
            vocab_notes
        )
        tabs.addTab(self._wrapLayout(vocab_notes_layout), "Vocab Notes")

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)
        self._saveLayout(general.get_raw_settings())

    def _saveLayout(self, settings: QSettings):
        layout = settings.value("layout")
        if layout:
            self.restoreGeometry(layout)

        def save_layout():
            geometry = self.saveGeometry()
            settings.setValue("layout", geometry)
        self.finished.connect(save_layout)

    def _wrapLayout(self, layout: QLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _createGeneralSettings(self) -> QLayout:
        form = QFormLayout()

        self._createTextSetting("Value Delimiter",  general, form)
        self._createTextSetting("Line Delimiter", general, form)

        return form

    def _createNoteSettings(self, fields: list[str], settings: NoteSettings) -> QLayout:
        note_layout = QVBoxLayout()

        form = QFormLayout()
        note_layout.addLayout(form)

        self._createComboSetting("Deck", self._decks, settings, form)

        note_combo = self._createComboSetting("Note Type", self._note_types, settings, form)
        note_fields = anki.findFields(settings.note_type)

        grp = QGroupBox("Fields")
        fields_form = QFormLayout(grp)
        note_layout.addWidget(grp)

        for field in fields:
            field_combo = self._createComboSetting(field, note_fields, settings.fields, fields_form)

            def reload_fields(note_type, f=field, c=field_combo):
                c.clear()
                c.addItems(anki.findFields(note_type))
                c.setCurrentText(settings.fields.get_setting(f))
            note_combo.currentTextChanged.connect(reload_fields)

        note_layout.addStretch()
        return note_layout

    def _createComboSetting(self, name: str, values: list[str], settings: Settings, form: QFormLayout) -> QComboBox:
        field_combo = QComboBox()
        form.addRow(name, field_combo)

        field_combo.addItems(values)
        field_combo.setCurrentText(settings.get_setting(name))
        self.accepted.connect(lambda: settings.set_setting(name, field_combo.currentText()))

        return field_combo

    def _createTextSetting(self, name: str, settings: Settings, form: QFormLayout) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setText(settings.get_setting(name))
        form.addRow(name, line_edit)

        self.accepted.connect(lambda: settings.set_setting(name, line_edit.text()))

        return line_edit


def openDialog():
    dlg = SettingsDialog("Settings")
    if dlg.exec():
        anki.notify("Settings updated")
