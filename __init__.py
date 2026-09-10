import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.settings as settings
import anki_japanese_helper.vocab as vocab
from aqt import mw
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

# Register the actions in Tools
menu = QMenu("Japanese")
mw.form.menuTools.addMenu(menu)

action = QAction("Add Kanji...", mw)
action.triggered.connect(lambda _: kanji.openDialog())
menu.addAction(action)

action = QAction("Add Vocab...", mw)
action.triggered.connect(lambda _: vocab.openDialog())
menu.addAction(action)

action = QAction("Settings...", mw)
action.triggered.connect(lambda _: settings.openDialog())
menu.addAction(action)
