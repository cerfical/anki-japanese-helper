from PyQt6.QtCore import Qt, pyqtProperty, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QWidget)

CHIP_BG_COLOR = "#3A3A3A"
CHIP_BORDER_COLOR = "#555555"
CHIP_HOVER_COLOR = "#808080"
CHIP_TEXT_COLOR = "#FFFFFF"


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
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
