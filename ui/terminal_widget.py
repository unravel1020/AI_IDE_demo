"""
内置终端组件
基于 QProcess 执行编译和运行命令
"""

from PyQt6.QtWidgets import (
    QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QWidget, QFileDialog
)
from PyQt6.QtCore import QProcess, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import os
import tempfile


class TerminalWidget(QWidget):
    """内置终端 - 编译运行 C++ 代码"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)

        # 临时文件路径
        self.temp_dir = tempfile.gettempdir()
        self.current_cpp_file = None
        self.output_executable = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 命令输入栏
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入命令或点击编译/运行按钮...")
        self.cmd_input.returnPressed.connect(self.run_command)
        cmd_layout.addWidget(self.cmd_input)

        self.btn_compile = QPushButton("🔨 编译")
        self.btn_compile.clicked.connect(self.compile_current)
        cmd_layout.addWidget(self.btn_compile)

        self.btn_run = QPushButton("▶️ 运行")
        self.btn_run.clicked.connect(self.run_executable)
        cmd_layout.addWidget(self.btn_run)

        self.btn_clear = QPushButton("🧹 清空")
        self.btn_clear.clicked.connect(self.clear_output)
        cmd_layout.addWidget(self.btn_clear)

        layout.addLayout(cmd_layout)

        # 终端输出区
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("JetBrains Mono", 11))
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0D0D0D;
                color: #E0E0E0;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.output)
        self.setLayout(layout)

        self.append_output("🖥️ 终端已就绪\n", "#03DAC6")
        self.append_output("支持命令: g++, gcc, python, dir, ls 等\n", "#757575")

    def set_current_file(self, file_path: str):
        """设置当前 C++ 文件路径"""
        self.current_cpp_file = file_path
        if file_path:
            base = os.path.splitext(os.path.basename(file_path))[0]
            self.output_executable = os.path.join(self.temp_dir, base + ".exe")

    def compile_current(self):
        """编译当前 C++ 文件"""
        if not self.current_cpp_file or not os.path.exists(self.current_cpp_file):
            self.append_output("❌ 请先打开一个 C++ 文件\n", "#CF6679")
            return

        # 生成输出文件名
        base = os.path.splitext(os.path.basename(self.current_cpp_file))[0]
        self.output_executable = os.path.join(self.temp_dir, base + ".exe")

        self.append_output(f"🔨 编译: {self.current_cpp_file}\n", "#BB86FC")
        self.append_output(f"   输出: {self.output_executable}\n", "#757575")

        cmd = f"g++"
        args = ["-std=c++17", "-Wall", "-g", self.current_cpp_file, "-o", self.output_executable]

        self.process.start(cmd, args)
        self.btn_compile.setEnabled(False)
        self.btn_run.setEnabled(False)

    def run_executable(self):
        """运行编译后的可执行文件"""
        if not self.output_executable or not os.path.exists(self.output_executable):
            self.append_output("❌ 请先编译代码\n", "#CF6679")
            return

        self.append_output(f"▶️ 运行: {self.output_executable}\n", "#03DAC6")
        self.append_output("─" * 40 + "\n", "#494949")

        self.process.start(self.output_executable, [])
        self.btn_compile.setEnabled(False)
        self.btn_run.setEnabled(False)

    def run_command(self):
        """运行自定义命令"""
        cmd_text = self.cmd_input.text().strip()
        if not cmd_text:
            return

        parts = cmd_text.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        self.append_output(f"$ {cmd_text}\n", "#BB86FC")
        self.process.start(cmd, args)
        self.cmd_input.clear()
        self.btn_compile.setEnabled(False)
        self.btn_run.setEnabled(False)

    def on_stdout(self):
        """标准输出"""
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.append_output(data, "#E0E0E0")

    def on_stderr(self):
        """标准错误"""
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        # 错误信息标红
        self.append_output(data, "#FF8A80")

    def on_finished(self, exit_code, exit_status):
        """进程结束"""
        self.btn_compile.setEnabled(True)
        self.btn_run.setEnabled(True)

        if exit_code == 0:
            self.append_output(f"\n✅ 完成 (退出码: {exit_code})\n", "#69F0AE")
        else:
            self.append_output(f"\n⚠️ 退出码: {exit_code}\n", "#FFD54F")

        self.append_output("─" * 40 + "\n", "#494949")

    def append_output(self, text: str, color: str = "#E0E0E0"):
        """追加带颜色的输出"""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 设置颜色
        fmt = cursor.charFormat()
        fmt.setForeground(Qt.GlobalColor.white)  # 默认白色

        self.output.setTextCursor(cursor)
        self.output.insertPlainText(text)

        # 滚动到底部
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    def clear_output(self):
        """清空输出"""
        self.output.clear()
        self.append_output("🖥️ 终端已清空\n", "#03DAC6")

    def is_running(self) -> bool:
        """检查是否有进程在运行"""
        return self.process.state() != QProcess.ProcessState.NotRunning

    def stop(self):
        """停止当前进程"""
        if self.is_running():
            self.process.terminate()
            self.process.waitForFinished(1000)
            if self.is_running():
                self.process.kill()
            self.append_output("\n🛑 进程已终止\n", "#CF6679")
