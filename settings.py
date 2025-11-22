import anki_japanese_helper.anki as anki
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QScrollArea,
                             QVBoxLayout, QWidget)


class SettingsDialog(QDialog):
    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(parent)

        self._settings = get()
        self.setWindowTitle(title)
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        scroll_container = QWidget()
        scroll.setWidget(scroll_container)

        scroll_layout = QVBoxLayout()
        scroll_container.setLayout(scroll_layout)

        all_decks = anki.decks()
        all_notes = anki.noteTypes()

        field_groups = {
            "Kanji Notes": ["Kanji", "Meanings", "Components", "Strokes"],
            "Keyword Notes": ["Kanji", "Reading", "Keyword", "Meaning"],
            "Vocab Notes": ["Word", "Meanings", "Reading"],
        }

        gnrl_grp = QGroupBox("General")
        gnrl_box = QVBoxLayout(gnrl_grp)
        scroll_layout.addWidget(gnrl_grp)

        hbox = QHBoxLayout()
        gnrl_box.addLayout(hbox)

        hbox.addWidget(QLabel("Value Delimiter"))
        self._value_delim_edit = QLineEdit()
        self._value_delim_edit.setText(self._settings.value("general/value_delim"))
        hbox.addWidget(self._value_delim_edit)

        self._groups = {}
        for group, fields in field_groups.items():
            group_name = group.lower().replace(" ", "_")
            self._groups[group_name] = {}

            dst_grp = QGroupBox(group)
            dst_box = QVBoxLayout(dst_grp)
            scroll_layout.addWidget(dst_grp)
            self._groups[group_name]["layout"] = dst_box

            hbox = QHBoxLayout()
            dst_box.addLayout(hbox)

            # Destination deck
            hbox.addWidget(QLabel("Deck"))
            deck_combo = QComboBox()
            hbox.addWidget(deck_combo)
            self._groups[group_name]["deck"] = deck_combo

            # Note type
            hbox.addWidget(QLabel("Note"))
            note_combo = QComboBox()
            hbox.addWidget(note_combo)
            self._groups[group_name]["note"] = note_combo

            # Field names
            fields_grp = QGroupBox("Fields")
            dst_box.addWidget(fields_grp)
            fields_box = QVBoxLayout(fields_grp)

            self._groups[group_name]["fields"] = {}
            for field in fields:
                hbox = QHBoxLayout()
                fields_box.addLayout(hbox)
                hbox.addWidget(QLabel(field))

                field_combo = QComboBox()
                field_name = field.lower()

                def reload_fields(current_note, g=group_name, fn=field_name, f=field, c=field_combo):
                    c.clear()
                    c.addItems(anki.findFields(current_note))
                    c.setCurrentText(self._settings.value(f"{g}/fields/{fn}", f))

                note_combo.currentTextChanged.connect(reload_fields)
                hbox.addWidget(field_combo)

                self._groups[group_name]["fields"][field_name] = field_combo

            # Load previous settings
            deck_combo.addItems(all_decks)
            deck_combo.setCurrentText(self._settings.value(f"{group_name}/deck", "Default"))
            note_combo.addItems(all_notes)
            note_combo.setCurrentText(self._settings.value(f"{group_name}/note", "Basic"))

        hbox = QHBoxLayout()
        self._groups["kanji_notes"]["layout"].addLayout(hbox)
        hbox.addWidget(QLabel("Kanji SVG URL"))
        self._kanji_url_edit = QLineEdit()
        self._kanji_url_edit.setText(self._settings.value("kanji_notes/kanji_url"))
        hbox.addWidget(self._kanji_url_edit)

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)

    def accept(self):
        # Preserve settings
        for group_name, group in self._groups.items():
            self._settings.beginGroup(group_name)
            self._settings.setValue("deck", group["deck"].currentText())
            self._settings.setValue("note", group["note"].currentText())

            self._settings.beginGroup("fields")
            for field, combo in group["fields"].items():
                self._settings.setValue(field, combo.currentText())
            self._settings.endGroup()

            self._settings.endGroup()

        kanji_url = self._kanji_url_edit.text().strip().rstrip("/") + "/"
        self._settings.setValue("kanji_notes/kanji_url", kanji_url)
        self._settings.setValue("general/value_delim", self._value_delim_edit.text())

        super().accept()


def get() -> QSettings:
    return QSettings(anki.ADDON_ID)


def openDialog():
    dlg = SettingsDialog("Settings")
    if dlg.exec():
        anki.notify("Settings saved")
