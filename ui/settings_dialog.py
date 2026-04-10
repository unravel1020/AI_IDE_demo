"""
设置对话框
支持配置 API 参数、主题切换等
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

import json
import os
import sys

# 确保能导入 utils
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.config import load_config, save_config, get_default_config


class SettingsDialog(QDialog):
    """设置对话框"""

    # 主题映射
    THEME_MAP = {"dark": "深色", "light": "浅色"}
    THEME_MAP_REVERSE = {v: k for k, v in THEME_MAP.items()}

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("设置")
        self.resize(450, 300)

        self.init_ui()
        self._load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # ===== 表单区 =====
        form_layout = QFormLayout()

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("输入 Moonshot API Key")
        form_layout.addRow("API Key:", self.api_key_input)

        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.moonshot.cn/v1")
        form_layout.addRow("Base URL:", self.base_url_input)

        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.addItems(["kimi-k2.5", "kimi-k1.5", "kimi-k1"])
        form_layout.addRow("模型:", self.model_combo)

        # 温度
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setDecimals(1)
        self.temp_spin.setValue(1.0)
        form_layout.addRow("Temperature:", self.temp_spin)

        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["深色", "浅色"])
        form_layout.addRow("主题:", self.theme_combo)

        layout.addLayout(form_layout)

        # ===== 按钮区 =====
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("保存")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_settings(self):
        """加载已有设置"""
        config = load_config()

        self.api_key_input.setText(config.get("api_key", ""))
        self.base_url_input.setText(config.get("base_url", ""))

        model = config.get("model", "kimi-k2.5")
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        self.temp_spin.setValue(config.get("temperature", 1.0))

        theme = config.get("theme", "dark")
        theme_display = self.THEME_MAP.get(theme, "深色")
        index = self.theme_combo.findText(theme_display)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def _on_save(self):
        """保存设置"""
        current_theme_text = self.theme_combo.currentText()
        theme_value = self.THEME_MAP_REVERSE.get(current_theme_text, "dark")
        print(f"[DEBUG] Combo currentText: '{current_theme_text}' -> theme: '{theme_value}'")

        config = {
            "api_key": self.api_key_input.text().strip(),
            "base_url": self.base_url_input.text().strip() or "https://api.moonshot.cn/v1",
            "model": self.model_combo.currentText(),
            "temperature": self.temp_spin.value(),
            "theme": theme_value
        }

        import os
        from utils.config import CONFIG_PATH, save_config
        print(f"[DEBUG] Saving config to: {CONFIG_PATH}")
        save_config(config)
        # 验证保存结果
        import json
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"[DEBUG] Saved config: {saved}")
        QMessageBox.information(self, "保存成功", "设置已保存")
        self.accept()

    def get_settings(self) -> dict:
        """获取当前对话框内的配置"""
        return {
            "api_key": self.api_key_input.text().strip(),
            "base_url": self.base_url_input.text().strip(),
            "model": self.model_combo.currentText(),
            "temperature": self.temp_spin.value(),
            "theme": self.THEME_MAP_REVERSE.get(self.theme_combo.currentText(), "dark")
        }


# =========================
# 自测入口
# =========================
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("设置已保存:", dialog.get_settings())
    else:
        print("用户取消")
