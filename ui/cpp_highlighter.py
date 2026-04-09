from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ===== 关键字 =====
        keywords = [
            # 基础类型
            "int", "float", "double", "char", "void", "bool",
            "short", "long", "unsigned", "signed", "auto",
            "wchar_t",
            # 复合类型/声明
            "class", "struct", "enum", "union", "typename",
            "template", "typedef", "using", "namespace",
            # 访问控制与修饰符
            "public", "private", "protected", "friend",
            "explicit", "inline", "static", "extern", "mutable",
            "virtual", "override", "const", "volatile", "register",
            # 控制流
            "return", "if", "else", "for", "while", "do",
            "switch", "case", "break", "continue", "goto",
            "try", "catch", "throw",
            # 内存/指针/操作符
            "new", "delete", "nullptr", "this", "sizeof",
            "operator", "dynamic_cast", "static_cast",
            "reinterpret_cast", "const_cast",
            # C++11及以后
            "constexpr", "noexcept", "decltype", "export", "asm",
            # 布尔常量
            "true", "false"
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
