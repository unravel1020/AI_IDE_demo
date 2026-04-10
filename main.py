import sys
from PyQt6.QtWidgets import QApplication
from PyQt6ElaWidgetTools import ElaApplication, ElaTheme, ElaThemeType
from ui.main_window import MainWindow


def main():
    # 先创建 QApplication
    app = QApplication(sys.argv)

    # ElaApplication 初始化（加载 Fluent 全局样式）
    ela_app = ElaApplication.getInstance()
    if ela_app:
        ela_app.init()

    # 设置浅色主题
    ElaTheme.getInstance().setThemeMode(ElaThemeType.ThemeMode.Light)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
