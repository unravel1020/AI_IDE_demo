"""
内置终端组件
基于 QProcess 执行编译和运行命令
"""

from PyQt6.QtWidgets import (
    QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QWidget, QFileDialog
)
from PyQt6.QtCore import QProcess, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor
import os
import tempfile
import re


class TerminalWidget(QWidget):
    """内置终端 - 编译运行 C++ 代码"""

    # 信号：编译错误点击跳转
    goto_error = pyqtSignal(str, int)  # 文件路径, 行号

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

        self.btn_compile_run = QPushButton("▶️ 编译并运行")
        self.btn_compile_run.setToolTip("编译并运行当前文件 (F5)")
        self.btn_compile_run.clicked.connect(self.compile_and_run)
        cmd_layout.addWidget(self.btn_compile_run)

        self.btn_compile = QPushButton("🔨 编译")
        self.btn_compile.setToolTip("编译当前文件 (F6)")
        self.btn_compile.clicked.connect(self.compile_current)
        cmd_layout.addWidget(self.btn_compile)

        self.btn_run = QPushButton("🏃 运行")
        self.btn_run.setToolTip("运行编译后的程序 (F7)")
        self.btn_run.clicked.connect(self.run_executable)
        cmd_layout.addWidget(self.btn_run)

        self.btn_stop = QPushButton("⏹️ 停止")
        self.btn_stop.setToolTip("停止当前进程")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        cmd_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("🧹 清空")
        self.btn_clear.clicked.connect(self.clear_output)
        cmd_layout.addWidget(self.btn_clear)

        layout.addLayout(cmd_layout)

        # 终端输出区
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("JetBrains Mono", 11))
        # 样式由全局 QSS 主题控制
        layout.addWidget(self.output)
        self.setLayout(layout)

        self.append_output("🖥️ 终端已就绪\n")
        self.append_output("支持命令: g++, gcc, python, dir, ls 等\n")
        self.append_output("快捷键: F5=编译并运行, F6=编译, F7=运行\n\n")

    def set_current_file(self, file_path: str):
        """设置当前 C++ 文件路径"""
        self.current_cpp_file = file_path
        if file_path:
            base = os.path.splitext(os.path.basename(file_path))[0]
            self.output_executable = os.path.join(self.temp_dir, base + ".exe")

    def compile_and_run(self):
        """编译并运行（一键执行）"""
        if not self.current_cpp_file or not os.path.exists(self.current_cpp_file):
            self.append_output("❌ 请先打开一个 C++ 文件\n")
            return

        # 生成输出文件名
        base = os.path.splitext(os.path.basename(self.current_cpp_file))[0]
        self.output_executable = os.path.join(self.temp_dir, base + ".exe")

        self.append_output(f"🔨 编译: {self.current_cpp_file}\n")

        cmd = "g++"
        args = ["-std=c++17", "-Wall", "-g", self.current_cpp_file, "-o", self.output_executable]

        self._pending_run = True  # 标记编译后需要运行
        self.process.finished.disconnect(self.on_finished)
        self.process.finished.connect(self._on_compile_finished)
        self.process.start(cmd, args)
        self._set_buttons_running(True)

    def _on_compile_finished(self, exit_code, exit_status):
        """编译完成后的回调"""
        self._set_buttons_running(False)

        if exit_code == 0:
            self.append_output(f"✅ 编译成功\n")
            if self._pending_run and os.path.exists(self.output_executable):
                self.append_output(f"▶️ 运行: {self.output_executable}\n")
                self.append_output("─" * 40 + "\n")
                self.process.finished.disconnect(self._on_compile_finished)
                self.process.finished.connect(self.on_finished)
                self.process.start(self.output_executable, [])
                self._set_buttons_running(True)
            else:
                self.append_output("─" * 40 + "\n")
        else:
            self.append_output(f"❌ 编译失败 (退出码: {exit_code})\n")
            self.append_output("─" * 40 + "\n")
            self.process.finished.disconnect(self._on_compile_finished)
            self.process.finished.connect(self.on_finished)

        self._pending_run = False

    def compile_current(self):
        """编译当前 C++ 文件"""
        if not self.current_cpp_file or not os.path.exists(self.current_cpp_file):
            self.append_output("❌ 请先打开一个 C++ 文件\n")
            return

        # 生成输出文件名
        base = os.path.splitext(os.path.basename(self.current_cpp_file))[0]
        self.output_executable = os.path.join(self.temp_dir, base + ".exe")

        self.append_output(f"🔨 编译: {self.current_cpp_file}\n")
        self.append_output(f"   输出: {self.output_executable}\n")

        cmd = "g++"
        args = ["-std=c++17", "-Wall", "-g", self.current_cpp_file, "-o", self.output_executable]

        self.process.start(cmd, args)
        self._set_buttons_running(True)

    def run_executable(self):
        """运行编译后的可执行文件"""
        if not self.output_executable or not os.path.exists(self.output_executable):
            self.append_output("❌ 请先编译代码\n")
            return

        self.append_output(f"▶️ 运行: {self.output_executable}\n")
        self.append_output("─" * 40 + "\n")

        self.process.start(self.output_executable, [])
        self._set_buttons_running(True)

    def run_command(self):
        """运行自定义命令"""
        cmd_text = self.cmd_input.text().strip()
        if not cmd_text:
            return

        parts = cmd_text.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        self.append_output(f"$ {cmd_text}\n")
        self.process.start(cmd, args)
        self.cmd_input.clear()
        self._set_buttons_running(True)

    def on_stdout(self):
        """标准输出"""
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.append_output(data)

    def on_stderr(self):
        """标准错误"""
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        self.append_output(data, color="#ff6b6b")

        # 解析 g++ 错误信息，提取文件名和行号
        self._parse_errors(data)

    def _parse_errors(self, stderr_text: str):
        """解析编译错误信息"""
        # g++ 错误格式: file.cpp:123:5: error: message
        pattern = r'^(.+?):(\d+):(\d+):\s*(error|warning):\s*(.+)$'
        for line in stderr_text.splitlines():
            match = re.match(pattern, line.strip())
            if match:
                file_path = match.group(1)
                line_no = int(match.group(2))
                error_type = match.group(4)
                message = match.group(5)
                # 只发射当前打开文件的错误
                if self.current_cpp_file and os.path.basename(file_path) == os.path.basename(self.current_cpp_file):
                    self.goto_error.emit(self.current_cpp_file, line_no)

    def on_finished(self, exit_code, exit_status):
        """进程结束"""
        self._set_buttons_running(False)

        if exit_code == 0:
            self.append_output(f"\n✅ 完成 (退出码: {exit_code})\n")
        else:
            self.append_output(f"\n⚠️ 退出码: {exit_code}\n")

        self.append_output("─" * 40 + "\n")

    def _set_buttons_running(self, running: bool):
        """设置按钮状态"""
        self.btn_compile.setEnabled(not running)
        self.btn_run.setEnabled(not running)
        self.btn_compile_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def append_output(self, text: str, color: str = ""):
        """追加带颜色的输出"""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if color:
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(color))
            cursor.setCharFormat(fmt)

        self.output.setTextCursor(cursor)
        self.output.insertPlainText(text)

        # 恢复默认颜色
        if color:
            fmt = cursor.charFormat()
            fmt.setForeground(QColor())
            cursor.setCharFormat(fmt)
            self.output.setTextCursor(cursor)

        # 滚动到底部
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    def clear_output(self):
        """清空输出"""
        self.output.clear()
        self.append_output("🖥️ 终端已清空\n")

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
            self.append_output("\n🛑 进程已终止\n")
            self._set_buttons_running(False)
