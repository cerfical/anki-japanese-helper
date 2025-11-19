from aqt import mw
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

import anki_japanese_helper.kanji as kanji
import anki_japanese_helper.keywords as keywords
import anki_japanese_helper.settings as settings
import anki_japanese_helper.vocab as vocab

# Register the actions in Tools
menu = QMenu("Japanese")
mw.form.menuTools.addMenu(menu)

action = QAction("Add Kanji Note...", mw)
action.triggered.connect(lambda _: kanji.openDialog())
menu.addAction(action)

action = QAction("Add Keyword Note...", mw)
action.triggered.connect(lambda _: keywords.openDialog())
menu.addAction(action)

action = QAction("Add Vocab Note...", mw)
action.triggered.connect(lambda _: vocab.openDialog())
menu.addAction(action)

action = QAction("Settings...", mw)
action.triggered.connect(lambda _: settings.openDialog())
menu.addAction(action)
