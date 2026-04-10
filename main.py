import sys
from PyQt6.QtWidgets import QApplication
from PyQt6ElaWidgetTools import ElaApplication, ElaTheme, ElaThemeType
from ui.main_window import MainWindow
import os

# 确保能导入 utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.config import load_config


def main():
    # 先创建 QApplication
    app = QApplication(sys.argv)

    # ElaApplication 初始化（加载 Fluent 全局样式）
    ela_app = ElaApplication.getInstance()
    if ela_app:
        ela_app.init()

    # 从配置读取主题，默认浅色
    config = load_config()
    theme_name = config.get("theme", "light")
    theme_mode = ElaThemeType.ThemeMode.Dark if theme_name == "dark" else ElaThemeType.ThemeMode.Light
    ElaTheme.getInstance().setThemeMode(theme_mode)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
