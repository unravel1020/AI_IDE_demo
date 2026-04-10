"""
Material Design 3 (Material You) 主题系统
提供深色主题和浅色主题支持
"""

# =========================
# Material Design 3 配色 - 柔和浅色主题
# =========================

DARK = {
    "background": "#121212",
    "surface": "#1E1E1E",
    "surface_variant": "#2D2D2D",
    "surface_highlight": "#3D3D3D",
    "primary": "#BB86FC",
    "primary_container": "#4A4458",
    "on_primary": "#000000",
    "secondary": "#03DAC6",
    "secondary_container": "#004D40",
    "on_secondary": "#000000",
    "error": "#CF6679",
    "on_surface": "#E0E0E0",
    "on_surface_variant": "#A0A0A0",
    "outline": "#494949",
    "outline_variant": "#333333",
    "code_bg": "#1E1E1E",
    "code_line_number_bg": "#1A1A1A",
    "tab_selected": "#BB86FC",
    "tab_unselected": "#808080",
}

# 浅色主题 - 柔和护眼配色
LIGHT = {
    "background": "#F7F5F0",
    "surface": "#FFFFFF",
    "surface_variant": "#F0EDE8",
    "surface_highlight": "#E8E4DD",
    "primary": "#5B6BB8",
    "primary_container": "#E8EBF7",
    "on_primary": "#FFFFFF",
    "secondary": "#4A9B9B",
    "secondary_container": "#E0F0F0",
    "on_secondary": "#FFFFFF",
    "error": "#C45B5B",
    "error_container": "#F9E5E5",
    "on_surface": "#3D3D3D",
    "on_surface_variant": "#6B6B6B",
    "outline": "#D0CCC5",
    "outline_variant": "#E5E1DA",
    "code_bg": "#FDFCF8",
    "code_line_number_bg": "#F0EDE8",
    "tab_selected": "#5B6BB8",
    "tab_unselected": "#8A8A8A",
}


def generate_qss(colors: dict) -> str:
    """根据颜色配置生成 QSS 样式表"""
    c = colors

    return f"""
    /* ========================= */
    /* 全局样式 */
    /* ========================= */
    QWidget {{
        background-color: {c['background']};
        color: {c['on_surface']};
        font-family: "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QWidget {{
        background-color: {c['background']};
    }}

    /* ========================= */
    /* QMenuBar */
    /* ========================= */
    QMenuBar {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        padding: 2px 8px;
        border-bottom: 1px solid {c['outline_variant']};
        min-height: 28px;
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {c['surface_highlight']};
    }}

    /* ========================= */
    /* QMenu */
    /* ========================= */
    QMenu {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
        font-size: 12px;
    }}
    QMenu::item:selected {{
        background-color: {c['primary_container']};
        color: {c['primary']};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c['outline_variant']};
        margin: 4px 8px;
    }}

    /* ========================= */
    /* QPushButton */
    /* ========================= */
    QPushButton {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        padding: 5px 14px;
        font-weight: 500;
        font-size: 12px;
        min-height: 22px;
    }}
    QPushButton:hover {{
        background-color: {c['primary_container']};
        color: {c['primary']};
        border-color: {c['primary']};
    }}
    QPushButton:pressed {{
        background-color: {c['primary']};
        color: {c['on_primary']};
    }}
    QPushButton:disabled {{
        background-color: {c['surface_variant']};
        color: {c['on_surface_variant']};
        border-color: {c['outline_variant']};
    }}

    /* ========================= */
    /* QTabWidget */
    /* ========================= */
    QTabWidget::pane {{
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        background-color: {c['surface']};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c['on_surface_variant']};
        padding: 7px 14px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 12px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        color: {c['tab_selected']};
        border-bottom: 2px solid {c['tab_selected']};
        background-color: {c['primary_container']};
        border-radius: 4px 4px 0 0;
    }}
    QTabBar::tab:hover:!selected {{
        color: {c['on_surface']};
        background-color: {c['surface_highlight']};
        border-radius: 4px 4px 0 0;
    }}

    /* ========================= */
    /* QLineEdit */
    /* ========================= */
    QLineEdit {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 13px;
        min-height: 22px;
    }}
    QLineEdit:focus {{
        border: 2px solid {c['primary']};
    }}

    /* ========================= */
    /* QTextEdit / QPlainTextEdit */
    /* ========================= */
    QTextEdit, QPlainTextEdit {{
        background-color: {c['code_bg']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 8px;
        font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
        font-size: 13px;
        line-height: 1.5;
        selection-background-color: {c['primary_container']};
        selection-color: {c['primary']};
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {c['outline']};
    }}

    /* ========================= */
    /* QSplitter */
    /* ========================= */
    QSplitter::handle {{
        background-color: {c['outline_variant']};
    }}
    QSplitter::handle:horizontal {{
        width: 3px;
    }}
    QSplitter::handle:vertical {{
        height: 3px;
    }}
    QSplitter::handle:hover {{
        background-color: {c['primary']};
    }}

    /* ========================= */
    /* QScrollBar */
    /* ========================= */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['outline_variant']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['outline']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background-color: transparent;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['outline_variant']};
        border-radius: 5px;
        min-width: 30px;
    }}

    /* ========================= */
    /* QTreeWidget (File Tree) */
    /* ========================= */
    QTreeWidget {{
        background-color: {c['surface']};
        color: {c['on_surface_variant']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QTreeWidget::item {{
        padding: 5px 8px;
        border-radius: 4px;
        margin: 1px 4px;
        min-height: 18px;
    }}
    QTreeWidget::item:selected {{
        background-color: {c['primary_container']};
        color: {c['primary']};
    }}
    QTreeWidget::item:hover {{
        background-color: {c['surface_highlight']};
    }}
    QTreeWidget QHeaderView::section {{
        background-color: {c['surface_variant']};
        color: {c['on_surface_variant']};
        padding: 6px 8px;
        border: none;
        border-radius: 4px;
        font-weight: 500;
    }}

    /* ========================= */
    /* QListWidget */
    /* ========================= */
    QListWidget {{
        background-color: {c['surface']};
        color: {c['on_surface_variant']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 6px 10px;
        border-radius: 6px;
        margin: 2px 4px;
        min-height: 18px;
    }}
    QListWidget::item:selected {{
        background-color: {c['primary_container']};
        color: {c['primary']};
    }}
    QListWidget::item:hover {{
        background-color: {c['surface_highlight']};
    }}

    /* ========================= */
    /* QDialog */
    /* ========================= */
    QDialog {{
        background-color: {c['surface']};
        color: {c['on_surface']};
    }}

    /* ========================= */
    /* QLabel */
    /* ========================= */
    QLabel {{
        color: {c['on_surface']};
        font-size: 13px;
    }}

    /* ========================= */
    /* QComboBox */
    /* ========================= */
    QComboBox {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 22px;
    }}
    QComboBox:hover {{
        border-color: {c['outline']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        selection-background-color: {c['primary_container']};
    }}

    /* ========================= */
    /* QTextBrowser */
    /* ========================= */
    QTextBrowser {{
        background-color: {c['code_bg']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        line-height: 1.6;
    }}

    /* ========================= */
    /* QCheckBox */
    /* ========================= */
    QCheckBox {{
        color: {c['on_surface']};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 2px solid {c['outline']};
        background-color: {c['surface']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['primary']};
        border-color: {c['primary']};
    }}

    /* ========================= */
    /* QFrame */
    /* ========================= */
    QFrame {{
        background-color: {c['surface']};
        border-radius: 8px;
    }}

    /* ========================= */
    /* QGroupBox */
    /* ========================= */
    QGroupBox {{
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 14px;
        font-weight: 500;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {c['primary']};
    }}

    /* ========================= */
    /* QSpinBox / QDoubleSpinBox */
    /* ========================= */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 22px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c['primary']};
    }}
"""


def apply_theme(app, theme: str = "light"):
    """应用 Material Design 主题到 QApplication"""
    colors = DARK if theme == "dark" else LIGHT
    qss = generate_qss(colors)
    app.setStyleSheet(qss)
    return colors


def get_colors(theme: str = "light") -> dict:
    """获取主题颜色配置"""
    return DARK if theme == "dark" else LIGHT
