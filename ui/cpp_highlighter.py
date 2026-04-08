from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ===== 关键字 =====
        keywords = [
            "int", "float", "double", "char", "void",
            "class", "public", "private", "protected",
            "virtual", "override", "const", "return",
            "if", "else", "for", "while", "new", "delete"
        ]

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))

        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, keyword_format))

        # ===== 字符串 =====
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))
        self.rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # ===== 注释 =====
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))
        self.rules.append((QRegularExpression(r"//[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)