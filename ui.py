from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout, QLayoutItem,
                             QPushButton, QWidget)

CHIP_BG_COLOR = "#3A3A3A"
CHIP_BORDER_COLOR = "#555555"
CHIP_HOVER_COLOR = "#808080"
CHIP_TEXT_COLOR = "#FFFFFF"


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._items = []

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, idx: int) -> QLayoutItem:
        return self._items[idx] if 0 <= idx < len(self._items) else None

    def takeAt(self, idx: int) -> QLayoutItem:
        return self._items.pop(idx) if 0 <= idx < len(self._items) else None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect: QRect, testOnly: bool) -> int:
        x, y, lineHeight = rect.x(), rect.y(), 0
        for item in self._items:
            widget = item.widget()
            spaceX, spaceY = self.spacing(), self.spacing()
            nextX = x + widget.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y += lineHeight + spaceY
                nextX = x + widget.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), widget.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, widget.sizeHint().height())
        return y + lineHeight - rect.y()


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
        hbox.setContentsMargins(6, 2, 6, 2)
        hbox.setSpacing(4)

        self._label = QLabel(text)
        hbox.addWidget(self._label)

        plus_btn = QPushButton("+")
        plus_btn.clicked.connect(self._onIncrement)
        hbox.addWidget(plus_btn)

        minus_btn = QPushButton("-")
        minus_btn.clicked.connect(self._onDecrement)
        hbox.addWidget(minus_btn)

        del_button = QPushButton("×")
        del_button.clicked.connect(self._onRemove)
        hbox.addWidget(del_button)

        hbox.addStretch()
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
