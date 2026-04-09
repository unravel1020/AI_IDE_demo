from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QToolTip
from PyQt6.QtGui import QPainter, QColor, QTextCursor, QCursor
from PyQt6.QtCore import QRect, QSize
from themes.material_theme import get_colors


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

        # 开启鼠标跟踪
        self.setMouseTracking(True)

        # 错误映射（行号 -> 描述）
        self.error_map = {}

        self._last_line = -1

        # 获取主题颜色
        self.colors = get_colors("light")

    # =========================
    # 行号宽度
    # =========================
    def line_number_area_width(self):
        digits = len(str(self.blockCount()))
        return 10 + digits * 7

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                         self.line_number_area.width(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(),
                  self.line_number_area_width(), cr.height())
        )

    # =========================
    # 绘制行号
    # =========================
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.colors["code_line_number_bg"]))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(
            self.contentOffset()).top())

        while block.isValid():
            if top > event.rect().bottom():
                break

            line_number = block_number + 1

            # 画行号
            painter.setPen(QColor(self.colors["on_surface_variant"]))
            painter.drawText(
                0,
                top,
                self.line_number_area.width() - 10,
                15,
                0,
                str(line_number)
            )

            # 画红点
            if line_number in self.error_map:
                radius = 4

                x = self.line_number_area.width() - 8
                y = top + 5

                painter.setBrush(QColor(200, 80, 80))
                painter.setPen(QColor(200, 80, 80))
                painter.drawEllipse(x, y, radius, radius)

            block = block.next()
            top += int(self.blockBoundingRect(block).height())
            block_number += 1

    # =========================
    # Hover提示
    # =========================
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        cursor = self.cursorForPosition(event.pos())
        line_number = cursor.block().blockNumber() + 1

        # 防抖（避免频繁刷新）
        if self._last_line == line_number:
            return

        self._last_line = line_number

        if line_number in self.error_map:
            QToolTip.showText(
                QCursor.pos(),
                self.error_map[line_number],
                self
            )
        else:
            QToolTip.hideText()
