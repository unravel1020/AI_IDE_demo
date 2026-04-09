from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from themes.material_theme import apply_theme
import sys


def main():
    app = QApplication(sys.argv)
    # 应用 Material Design 深色主题
    apply_theme(app, theme="dark")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()