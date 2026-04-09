from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class CppHighlighter(QSyntaxHighlighter):
    """C++ 语法高亮器 - Material Design 配色"""

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ===== 颜色定义 =====
        colors = {
            "keyword": "#C792EA",      # 紫色 - 关键字
            "type": "#82AAFF",         # 蓝色 - 类型
            "function": "#82AAFF",     # 蓝色 - 函数
            "string": "#C3E88D",       # 绿色 - 字符串
            "comment": "#546E7A",      # 灰蓝 - 注释
            "number": "#F78C6C",       # 橙色 - 数字
            "preprocessor": "#C792EA", # 紫色 - 预处理器
            "operator": "#89DDFF",     # 青色 - 操作符
        }

        # ===== 关键字 =====
        keywords = [
            "int", "float", "double", "char", "void", "bool",
            "short", "long", "unsigned", "signed", "auto",
            "wchar_t", "size_t",
        ]

        types = [
            "class", "struct", "enum", "union", "typename",
            "template", "typedef", "using", "namespace",
            "public", "private", "protected", "friend",
            "explicit", "inline", "static", "extern", "mutable",
            "virtual", "override", "final", "const", "volatile", "register",
        ]

        control = [
            "return", "if", "else", "for", "while", "do",
            "switch", "case", "break", "continue", "goto",
            "try", "catch", "throw",
        ]

        memory = [
            "new", "delete", "nullptr", "this", "sizeof",
            "operator", "dynamic_cast", "static_cast",
            "reinterpret_cast", "const_cast",
        ]

        cpp11 = [
            "constexpr", "noexcept", "decltype", "export", "asm",
            "true", "false",
        ]

        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(colors["keyword"]))
        keyword_format.setFontWeight(600)

        for word in keywords + control + memory + cpp11:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, keyword_format))

        # 类型格式
        type_format = QTextCharFormat()
        type_format.setForeground(QColor(colors["type"]))
        type_format.setFontWeight(600)

        for word in types:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, type_format))

        # ===== 字符串 =====
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(colors["string"]))
        self.rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.rules.append((QRegularExpression(r"'[^']*'"), string_format))

        # ===== 注释 =====
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(colors["comment"]))
        comment_format.setFontItalic(True)
        self.rules.append((QRegularExpression(r"//[^\n]*"), comment_format))

        # ===== 数字 =====
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(colors["number"]))
        self.rules.append((QRegularExpression(r"\b\d+\b"), number_format))

        # ===== 预处理器 =====
        prep_format = QTextCharFormat()
        prep_format.setForeground(QColor(colors["preprocessor"]))
        self.rules.append((QRegularExpression(r"#\s*\w+"), prep_format))
        self.rules.append((QRegularExpression(r"#include\s*<[^>]+>"), prep_format))
        self.rules.append((QRegularExpression(r"#include\s*\"[^\"]+\""), prep_format))

        # ===== 函数调用 =====
        func_format = QTextCharFormat()
        func_format.setForeground(QColor(colors["function"]))
        self.rules.append((QRegularExpression(r"\b[A-Za-z_]\w*(?=\s*\()"), func_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
