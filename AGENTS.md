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

### 深色主题

所有自定义组件实现 `apply_theme()` 方法，响应 `ElaTheme.themeModeChanged` 信号。

已适配的组件：
- `CodeEditor` - 编辑器背景和行号
- `FileTree` - 文件树背景
- `QTabWidget` - 标签页
- `QTextBrowser` - 分析结果/历史记录
- `QPushButton` (导航栏/工具栏) - 按钮样式
- `PluginPanel` - 插件面板

## 插件系统

### 架构

```
plugins/
├── plugin_base.py          # 插件基类 (PluginBase)
├── plugin_manager.py       # 插件管理器 (PluginManager)
├── todo_highlighter.py     # 官方插件：TODO 高亮器
└── examples/
    ├── hello_plugin.py     # 示例：问候插件
    └── stats_plugin.py     # 示例：代码统计插件
```

### 插件基类钩子

| 钩子 | 说明 |
|------|------|
| `on_load(main_window)` | 插件加载时调用 |
| `on_unload()` | 插件卸载时调用 |
| `before_analyze(code)` | 分析前，可修改代码 |
| `after_analyze(code, result)` | 分析后，可修改结果 |
| `get_menu_items()` | 返回菜单项列表 |
| `get_toolbar_buttons()` | 返回工具栏按钮列表 |
| `get_sidebar_widget()` | 返回侧边栏自定义 Widget |

### 工具方法

| 方法 | 说明 |
|------|------|
| `get_editor_text()` | 获取编辑器当前文本 |
| `set_editor_text(text)` | 设置编辑器文本 |
| `show_message(html)` | 在主窗口分析面板显示 HTML 消息 |
| `get_main_window()` | 获取主窗口实例 |

### 官方插件：TODO Highlighter

**功能**：扫描代码中的 TODO / FIXME / HACK / XXX / NOTE / WARNING 标记，在分析结果中汇总展示。

**支持的注释格式**：
```cpp
// TODO: 优化这里的算法
/* FIXME: 内存泄漏 */
/** NOTE: 重要提示 */
# WARNING: 注意
```

**菜单项**：
- `插件 > TODO 扫描 - 扫描当前文件` (Ctrl+Shift+T)
- `插件 > TODO 列表 - 显示上次扫描结果`

**演示特性**：
- `after_analyze` 钩子：向分析结果注入 TODO 列表
- `get_menu_items`：添加菜单项和快捷键
- `get_toolbar_buttons`：添加工具栏按钮
- 与编辑器交互：获取文本、显示结果、行号跳转

### 开发新插件

```python
from plugins.plugin_base import PluginBase

class MyPlugin(PluginBase):
    name = "My Plugin"
    version = "1.0.0"
    description = "插件描述"
    author = "Your Name"

    def after_analyze(self, code: str, result: dict) -> dict:
        # 修改分析结果
        result["_plugin_my_data"] = "..."
        return result

    def get_menu_items(self):
        return [{
            "name": "我的插件 - 执行",
            "callback": self.on_action,
            "shortcut": "Ctrl+Shift+M"
        }]

    def on_action(self):
        text = self.get_editor_text()
        self.show_message(f"<p>代码行数: {len(text.splitlines())}</p>")
```

将插件文件放在 `plugins/` 目录下即可自动加载。

## 已知问题

### QFileDialog 原生对话框

ElaWindow 使用无边框窗口，与 Windows 原生文件对话框存在冲突。
**所有 `QFileDialog` 调用必须添加 `DontUseNativeDialog` 选项**：
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
| Ctrl+Shift+T | TODO 扫描 (插件) |
| Ctrl+F | 查找 |
| Ctrl+H | 替换 |
