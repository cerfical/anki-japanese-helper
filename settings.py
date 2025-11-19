from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
                             QWidget)

import anki_japanese_helper.anki as anki


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
            "Kanji Notes": ["Kanji", "Meaning", "Components", "Strokes"],
            "Keyword Notes": ["Kanji", "Reading", "Keyword", "Meaning"],
            "Vocab Notes": ["Word", "Meaning", "Reading"],
        }

        self._groups = {}
        for group, fields in field_groups.items():
            group_name = group.lower().replace(" ", "_")

            dst_grp = QGroupBox(group)
            dst_box = QVBoxLayout(dst_grp)
            scroll_layout.addWidget(dst_grp)

            hbox = QHBoxLayout()
            dst_box.addLayout(hbox)

            # Destination deck
            vbox = QVBoxLayout()
            hbox.addLayout(vbox)
            vbox.addWidget(QLabel("Destination Deck"))
            deck_combo = QComboBox()
            vbox.addWidget(deck_combo)
            self._groups[group_name] = {}
            self._groups[group_name]["dst_deck"] = deck_combo

            # Note type
            vbox = QVBoxLayout()
            hbox.addLayout(vbox)
            vbox.addWidget(QLabel("Note Type"))
            note_combo = QComboBox()
            vbox.addWidget(note_combo)
            self._groups[group_name]["note_type"] = note_combo

            # Field names
            fields_grp = QGroupBox("Field Names")
            dst_box.addWidget(fields_grp)
            fields_box = QVBoxLayout(fields_grp)

            self._groups[group_name]["field_names"] = {}
            for field in fields:
                hbox = QHBoxLayout()
                fields_box.addLayout(hbox)
                hbox.addWidget(QLabel(field))

                field_combo = QComboBox()
                field_name = field.lower()

                def reload_fields(current_note, g=group_name, fn=field_name, f=field, c=field_combo):
                    c.clear()
                    c.addItems(anki.findFields(current_note))
                    c.setCurrentText(self._settings.value(f"{g}/field_names/{fn}", f))

                note_combo.currentTextChanged.connect(reload_fields)
                hbox.addWidget(field_combo)

                self._groups[group_name]["field_names"][field_name] = field_combo

            # Load previous settings
            deck_combo.addItems(all_decks)
            deck_combo.setCurrentText(self._settings.value(f"{group_name}/dst_deck", "Default"))
            note_combo.addItems(all_notes)
            note_combo.setCurrentText(self._settings.value(f"{group_name}/note_type", "Basic"))

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
            self._settings.setValue(f"dst_deck", group["dst_deck"].currentText())
            self._settings.setValue(f"note_type", group["note_type"].currentText())

            self._settings.beginGroup("field_names")
            for field, combo in group["field_names"].items():
                self._settings.setValue(field, combo.currentText())
            self._settings.endGroup()

            self._settings.endGroup()

        super().accept()


def get() -> QSettings:
    return QSettings(anki.ADDON_ID)


def openDialog():
    dlg = SettingsDialog()
    if dlg.exec():
        anki.notify("Settings saved")
