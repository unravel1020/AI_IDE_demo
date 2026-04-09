"""
Material Design 3 (Material You) 主题系统
提供深色主题和浅色主题支持
"""

# =========================
# Material Design 3 配色
# =========================

# 深色主题 (Dark Theme)
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
    "error_container": "#8B0000",
    "on_surface": "#E0E0E0",
    "on_surface_variant": "#A0A0A0",
    "outline": "#494949",
    "outline_variant": "#333333",
    "divider": "#1FFFFFFF",
    "shadow": "#000000",
    "scrim": "#000000",
    "inverse_surface": "#E0E0E0",
    "inverse_on_surface": "#121212",
    "code_bg": "#1E1E1E",
    "code_line_number_bg": "#1A1A1A",
    "code_line_number_fg": "#606060",
    "tab_selected": "#BB86FC",
    "tab_unselected": "#808080",
}

# 浅色主题 (Light Theme)
LIGHT = {
    "background": "#F5F5F5",
    "surface": "#FFFFFF",
    "surface_variant": "#F0F0F0",
    "surface_highlight": "#E8E8E8",
    "primary": "#6750A4",
    "primary_container": "#EADDFF",
    "on_primary": "#FFFFFF",
    "secondary": "#625B71",
    "secondary_container": "#E8DEF8",
    "on_secondary": "#FFFFFF",
    "error": "#B3261E",
    "error_container": "#F9DEDC",
    "on_surface": "#1C1B1F",
    "on_surface_variant": "#49454F",
    "outline": "#79747E",
    "outline_variant": "#CAC4D0",
    "divider": "#1F000000",
    "shadow": "#000000",
    "scrim": "#000000",
    "inverse_surface": "#313033",
    "inverse_on_surface": "#F4EFF4",
    "code_bg": "#FAFAFA",
    "code_line_number_bg": "#F0F0F0",
    "code_line_number_fg": "#999999",
    "tab_selected": "#6750A4",
    "tab_unselected": "#666666",
}


def generate_qss(colors: dict) -> str:
    """
    根据颜色配置生成 QSS 样式表
    """
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

    /* ========================= */
    /* QMenuBar */
    /* ========================= */
    QMenuBar {{
        background-color: {c['surface']};
        color: {c['on_surface']};
        padding: 4px 8px;
        border-bottom: 1px solid {c['outline_variant']};
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {c['surface_highlight']};
    }}
    QMenuBar::item:pressed {{
        background-color: {c['surface_variant']};
    }}

    /* ========================= */
    /* QMenu */
    /* ========================= */
    QMenu {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c['surface_highlight']};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c['outline_variant']};
        margin: 6px 12px;
    }}

    /* ========================= */
    /* QPushButton - Material Button */
    /* ========================= */
    QPushButton {{
        background-color: {c['primary_container']};
        color: {c['primary']};
        border: none;
        border-radius: 20px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 12px;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{
        background-color: {c['primary']};
        color: {c['on_primary']};
    }}
    QPushButton:pressed {{
        background-color: {c['primary']};
        opacity: 0.8;
    }}
    QPushButton:disabled {{
        background-color: {c['surface_variant']};
        color: {c['on_surface_variant']};
    }}

    /* ========================= */
    /* QTabWidget - Material Tabs */
    /* ========================= */
    QTabWidget::pane {{
        border: none;
        background-color: {c['surface']};
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c['on_surface_variant']};
        padding: 10px 16px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 12px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        color: {c['tab_selected']};
        border-bottom: 2px solid {c['tab_selected']};
    }}
    QTabBar::tab:hover:!selected {{
        color: {c['on_surface']};
        background-color: {c['surface_highlight']};
    }}

    /* ========================= */
    /* QLineEdit */
    /* ========================= */
    QLineEdit {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 2px solid {c['primary']};
    }}
    QLineEdit::placeholder {{
        color: {c['on_surface_variant']};
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
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    QSplitter::handle:hover {{
        background-color: {c['primary']};
    }}

    /* ========================= */
    /* QScrollBar */
    /* ========================= */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['outline_variant']};
        border-radius: 4px;
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
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['outline_variant']};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['outline']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ========================= */
    /* QTreeWidget (File Tree) */
    /* ========================= */
    QTreeWidget {{
        background-color: {c['surface']};
        color: {c['on_surface_variant']};
        border: none;
        outline: none;
        padding: 4px;
    }}
    QTreeWidget::item {{
        padding: 6px 8px;
        border-radius: 6px;
        margin: 2px 4px;
    }}
    QTreeWidget::item:selected {{
        background-color: {c['primary_container']};
        color: {c['primary']};
    }}
    QTreeWidget::item:hover {{
        background-color: {c['surface_highlight']};
    }}
    QHeaderView::section {{
        background-color: {c['surface_variant']};
        color: {c['on_surface_variant']};
        padding: 8px;
        border: none;
        font-weight: 500;
    }}

    /* ========================= */
    /* QListWidget (Snippet Panel) */
    /* ========================= */
    QListWidget {{
        background-color: {c['surface']};
        color: {c['on_surface_variant']};
        border: none;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 8px;
        margin: 2px 6px;
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
    /* QGroupBox */
    /* ========================= */
    QGroupBox {{
        border: 1px solid {c['outline_variant']};
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: 500;
        color: {c['on_surface']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        color: {c['primary']};
    }}

    /* ========================= */
    /* QComboBox */
    /* ========================= */
    QComboBox {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 8px 12px;
        min-width: 100px;
    }}
    QComboBox:hover {{
        border-color: {c['outline']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {c['on_surface_variant']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        selection-background-color: {c['primary_container']};
    }}

    /* ========================= */
    /* QDoubleSpinBox */
    /* ========================= */
    QDoubleSpinBox {{
        background-color: {c['surface_variant']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 8px 12px;
    }}
    QDoubleSpinBox:focus {{
        border: 2px solid {c['primary']};
    }}

    /* ========================= */
    /* QCheckBox */
    /* ========================= */
    QCheckBox {{
        color: {c['on_surface']};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {c['outline']};
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['primary']};
        border-color: {c['primary']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c['primary']};
    }}

    /* ========================= */
    /* QTextBrowser */
    /* ========================= */
    QTextBrowser {{
        background-color: {c['code_bg']};
        color: {c['on_surface']};
        border: 1px solid {c['outline_variant']};
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        line-height: 1.6;
    }}
    QTextBrowser QScrollBar:vertical {{
        width: 6px;
    }}

    /* ========================= */
    /* 状态栏 */
    /* ========================= */
    QLabel#status_label {{
        color: {c['on_surface_variant']};
        font-size: 12px;
        padding: 4px 12px;
    }}
"""


def apply_theme(app, theme: str = "dark"):
    """
    应用 Material Design 主题到 QApplication

    Args:
        app: QApplication 实例
        theme: "dark" 或 "light"
    """
    colors = DARK if theme == "dark" else LIGHT
    qss = generate_qss(colors)
    app.setStyleSheet(qss)
    return colors


def get_colors(theme: str = "dark") -> dict:
    """获取主题颜色配置"""
    return DARK if theme == "dark" else LIGHT
