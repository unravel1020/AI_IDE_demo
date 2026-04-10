# AGENTS.md

## 项目信息

- **项目**: AI C++ IDE
- **仓库**: https://github.com/unravel1020/AI_IDE_demo
- **当前版本**: v2.2.0
- **技术栈**: Python 3.14, PyQt6 6.11.0, PyQt6-ElaWidgetTools 0.9.1, qtawesome 1.4.1

## 架构

### 页面布局 (v2.2.0)

主窗口继承 `ElaWindow`，但**不使用 `addPageNode`** 管理页面。

采用自定义页面管理方案：
- `QStackedWidget` 作为页面容器
- 左侧自定义导航栏 (`QWidget + QVBoxLayout + QPushButton`)
- 页面切换通过 `_switch_page()` 方法实现

**为什么不用 `addPageNode`**:
ElaWindow 的 `addPageNode` 内部使用 QStackedWidget，在添加多个页面时会触发 Qt 垃圾回收，
导致非活动页面的子组件（如 `CodeEditor`）被删除，产生 `wrapped C/C++ object has been deleted` 错误。

### 组件生命周期

所有核心组件在 `init_ui()` 开头创建并保存为实例属性：
```python
self.code_input = CodeEditor()      # 代码编辑器
self.file_tree = FileTree()          # 文件树
self.tabs = QTabWidget()             # 底部标签页
self.chat_panel = ChatPanel()        # AI聊天
...
```

这些组件之后被添加到各页面的布局中，但**生命周期由 MainWindow 直接管理**，
不会因为页面切换而被删除。

## 已知问题

### QFileDialog 原生对话框

ElaWindow 使用无边框窗口，与 Windows 原生文件对话框存在冲突。
**所有 `QFileDialog` 调用必须添加 `DontUseNativeDialog` 选项**:
```python
QFileDialog.getOpenFileName(
    None, "打开文件", "",
    options=QFileDialog.Option.DontUseNativeDialog
)
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开文件 |
| Ctrl+S | 保存结果 |
| Ctrl+R | 分析代码 |
| Ctrl+Shift+H | 修复代码 |
| Ctrl+Shift+G | 格式化代码 |
| Ctrl+E | 解释代码 |
| Ctrl+B | 批量分析 |
| Ctrl+F | 查找 |
| Ctrl+H | 替换 |
