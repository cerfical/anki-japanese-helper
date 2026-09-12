from PyQt6.QtCore import Qt, pyqtProperty, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFrame, QGroupBox,
                             QHBoxLayout, QLabel, QLayout, QLineEdit,
                             QListWidget, QPushButton, QScrollArea,
                             QSizePolicy, QVBoxLayout, QWidget)

CHIP_BG_COLOR = "#3A3A3A"
CHIP_BORDER_COLOR = "#555555"
CHIP_HOVER_COLOR = "#808080"
CHIP_TEXT_COLOR = "#FFFFFF"


class NoteDialog(QDialog):
    def __init__(self, title: str, tags: list[str], parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle(title)
        main_layout = QVBoxLayout()

        self._content = QWidget()
        main_layout.addWidget(self._content)

        tags_grp = QGroupBox("Tags")
        tags_box = QVBoxLayout(tags_grp)
        main_layout.addWidget(tags_grp)

        # Get rid of the excessive space at the bottom
        margins = tags_box.contentsMargins()
        margins.setTop(0)
        margins.setBottom(0)
        tags_box.setContentsMargins(margins)

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

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

        self.setLayout(main_layout)

        self._all_tags = tags
        self._tags = []

    def _showTagsPopup(self):
        dlg = SelectionDialog("Add Tag", self._all_tags, self)
        selected_idx = dlg.exec()

        t = self._all_tags[selected_idx]
        self._createTagChip(t)

    def _createTagChip(self, tag: str):
        chip = TextChip(tag)

        self._tags_box.addWidget(chip)
        self._tags.append(tag)

        def delete_chip(t=tag, c=chip):
            self._tags_box.removeWidget(c)
            c.deleteLater()
            self._tags.remove(t)

        chip.remove.connect(delete_chip)

    def setContentLayout(self, layout: QLayout):
        layout.setContentsMargins(0, 0, 0, 0)
        self._content.setLayout(layout)

    def getNoteTags(self) -> list[str]:
        return self._tags


class SelectionDialog(QDialog):
    def __init__(self, title: str, items: list[str], parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Popup)

        layout = QVBoxLayout(self)

        search = QLineEdit()
        search.setPlaceholderText("Search for...")
        layout.addWidget(search)

        list_widget = QListWidget()
        list_widget.addItems(items)
        layout.addWidget(list_widget)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search.textChanged.connect(filter_items)
        search.setFocus()

        def item_selected(item):
            selected_idx = list_widget.row(item)
            self.done(selected_idx)
        list_widget.itemClicked.connect(item_selected)


class ButtonChip(QPushButton):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)

        self.setStyleSheet(f"""
            QPushButton {{
                padding: 3px 5px 3px 5px;
                border: 1px solid {CHIP_BORDER_COLOR};
                border-radius: 8px;
                background-color: {CHIP_BG_COLOR};
            }}
            QPushButton:hover {{
                border: 1px solid {CHIP_HOVER_COLOR};
            }}
        """)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)


class CounterChip(QFrame):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        self._count = 1
        self._text = text

        hbox = QHBoxLayout()
        hbox.setContentsMargins(2, 2, 2, 2)
        hbox.setSpacing(4)

        self._label = QLabel(text)
        self._label.setMargin(2)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox.addWidget(self._label)

        minus_btn = QPushButton("-")
        minus_btn.clicked.connect(self._onDecrement)
        hbox.addWidget(minus_btn)

        plus_btn = QPushButton("+")
        plus_btn.clicked.connect(self._onIncrement)
        hbox.addWidget(plus_btn)

        del_button = QPushButton("×")
        del_button.clicked.connect(self._onRemove)
        hbox.addWidget(del_button)

        self.setLayout(hbox)

        self.setStyleSheet(f"""
            QWidget {{
                border: 1px solid {CHIP_BORDER_COLOR};
                border-radius: 8px;
                background-color: {CHIP_BG_COLOR};
            }}

            QLabel {{
                padding: 1px 3px 1px 3px;
            }}

            QPushButton {{
                background: transparent;
                border: none;
                padding: 0px;
            }}

            QPushButton:hover {{
                color: {CHIP_HOVER_COLOR};
            }}
        """)

    def getText(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text

        fmt_text = f"{text} ×{self._count}" if self._count > 1 else text
        self._label.setText(fmt_text)

    def getCount(self) -> int:
        return self._count

    def setCount(self, count: int):
        if count == self._count:
            return

        self._count = count
        self.setText(self._text)
        if count < 1:
            self._onRemove()

    def _onIncrement(self):
        self.count += 1

    def _onDecrement(self):
        self.count -= 1

    def _onRemove(self):
        self.remove.emit()

    text = pyqtProperty(str, fget=getText, fset=setText)
    count = pyqtProperty(int, fget=getCount, fset=setCount)

    remove = pyqtSignal()


class TextChip(QFrame):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        self._text = text

        hbox = QHBoxLayout()
        hbox.setContentsMargins(2, 2, 2, 2)
        hbox.setSpacing(4)

        self._label = QLabel(text)
        self._label.setMargin(2)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox.addWidget(self._label)

        del_button = QPushButton("×")
        del_button.clicked.connect(self._onRemove)
        hbox.addWidget(del_button)

        self.setLayout(hbox)

        self.setStyleSheet(f"""
            QWidget {{
                border: 1px solid {CHIP_BORDER_COLOR};
                border-radius: 8px;
                background-color: {CHIP_BG_COLOR};
            }}

            QLabel {{
                padding: 1px 3px 1px 3px;
            }}

            QPushButton {{
                background: transparent;
                border: none;
                padding: 0px;
            }}

            QPushButton:hover {{
                color: {CHIP_HOVER_COLOR};
            }}
        """)

    def getText(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self._label.setText(text)

    def _onRemove(self):
        self.remove.emit()

    text = pyqtProperty(str, fget=getText, fset=setText)
    remove = pyqtSignal()
