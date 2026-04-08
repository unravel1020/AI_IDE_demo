# AI C++ IDE（Agent版）

> 基于 PyQt6 和 Moonshot AI (Kimi) 构建的智能 C++ 代码分析与修复 IDE。

---

## 📖 项目概述

本项目是一个 **AI 驱动的 C++ 集成开发环境（IDE）**，通过调用大语言模型（LLM）为 C++ 开发者提供实时的代码分析、Bug 检测、自动修复等功能。项目采用 **模块化架构** 设计，支持多轮对话上下文、JSON 结构化输出、以及智能 Agent 自主决策等高级特性。

### 核心设计理念
- **AI 赋能**：利用大模型深度理解 C++ 代码语义，发现传统静态分析工具难以察觉的逻辑缺陷
- **Agent 智能**：系统可自主判断代码问题的严重程度，自动决策是仅输出分析报告，还是直接提供修复代码
- **工程化封装**：SDK 层封装了重试机制、JSON 清洗、上下文管理等复杂逻辑，上层业务只需关注 Prompt 设计

---

## ✨ 主要功能

| 功能模块 | 描述 | 输出格式 |
|---------|------|---------|
| 🔍 **代码分析** | 检测 Bugs、线程问题、内存泄漏、性能优化建议 | JSON 结构化报告 |
| 🛠 **代码修复** | 自动修复代码中的潜在问题，保持原有逻辑不变 | 完整修复后的代码 |
| 🧠 **智能 Agent** | 自主判断问题严重程度：严重则修复，轻微则仅分析 | 修复代码 / JSON 分析 |
| 📝 **代码编辑器** | 支持行号显示、C++ 语法高亮、深色主题 | - |
| 📂 **文件操作** | 打开 `.cpp` / `.h` 文件、保存分析结果 | - |

---

## 🏗 项目架构

```
AI_IDE_demo/
├── main.py                    # 程序入口
├── requirements.txt           # 依赖清单
│
├── core/                      # 🔧 核心 SDK 层
│   └── API_Call_SDK_v1.py     # AI 客户端封装（重试、上下文、JSON清洗）
│
├── analyzer/                  # 🧠 分析器层
│   ├── cpp_analyzer.py        # C++ 代码分析器
│   ├── code_fixer.py          # 代码修复器
│   └── code_agent.py          # 智能 Agent（自主决策）
│
├── ui/                        # 🖥 UI 层
│   ├── main_window.py         # 主窗口（Tab布局、Worker线程）
│   ├── code_editor.py         # 自定义代码编辑器（行号）
│   └── cpp_highlighter.py     # C++ 语法高亮器
│
├── .vscode/                   # VSCode 配置
├── .idea/                     # PyCharm 配置
│
└── test.cpp                   # 测试用 C++ 代码
```

### 架构亮点

#### 1. SDK 层（`core/API_Call_SDK_v1.py`）
- **多轮对话上下文管理**：自动维护对话历史，支持上下文裁剪（保留最近 20 轮）
- **JSON 模式隔离**：结构化输出使用独立上下文，防止污染对话历史
- **智能重试机制**：遇到模型繁忙（429/overloaded）自动重试，最多 3 次
- **JSON 清洗与容错**：自动去除 Markdown 代码块标记，解析失败时尝试让 AI 自我修复

#### 2. 分析器层（`analyzer/`）
- **职责分离**：分析、修复、Agent 三个模块独立，便于扩展和维护
- **Prompt 工程**：每个模块有精心设计的 Prompt，指导 AI 按预期格式输出
- **CodeAgent 自主决策**：根据问题严重程度动态选择输出修复代码或 JSON 分析报告

#### 3. UI 层（`ui/`）
- **Worker 线程**：所有 AI 操作均在独立线程执行，避免阻塞 UI
- **Tab 布局**：分析结果、修复代码、Agent 输出三栏分离，清晰直观
- **自定义编辑器**：基于 `QPlainTextEdit` 实现，支持行号和 C++ 语法高亮

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Moonshot AI API Key（[获取地址](https://platform.moonshot.cn/)）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API Key

```bash
# Windows PowerShell
$env:MOONSHOT_API_KEY = "your-api-key-here"

# Windows CMD
set MOONSHOT_API_KEY=your-api-key-here

# Linux / macOS
export MOONSHOT_API_KEY="your-api-key-here"
```

### 运行程序

```bash
python main.py
```

---

## 📸 使用指南

1. **打开代码文件**：点击菜单栏 `文件 → 打开.cpp文件`，或直接粘贴代码到左侧编辑器
2. **代码分析**：点击 `分析` 按钮，AI 将检测 Bugs、线程问题、内存问题等，结果以 JSON 格式显示在"分析结果"标签页
3. **代码修复**：点击 `修复` 按钮，AI 将返回完整修复后的代码，显示在"修复代码"标签页
4. **智能 Agent**：点击 `🧠 智能` 按钮，Agent 将自主判断代码问题的严重程度：
   - 若存在严重问题（内存泄漏、崩溃风险、未定义行为）→ 输出修复后的完整代码
   - 若问题轻微 → 输出 JSON 格式的分析报告
5. **保存结果**：点击 `文件 → 保存分析结果`，将分析报告导出为文本文件

---

## 🛠 技术栈

| 技术 | 用途 |
|-----|------|
| **PyQt6** | 跨平台 GUI 框架，构建 IDE 界面 |
| **OpenAI SDK** | 调用 Moonshot AI API（兼容 OpenAI 接口） |
| **Kimi-k2.5** | 大语言模型，提供代码分析与修复能力 |

---

## 📂 文件说明

| 文件 | 说明 |
|-----|------|
| `main.py` | 程序入口，初始化 QApplication 和主窗口 |
| `core/API_Call_SDK_v1.py` | AI 客户端 SDK，封装了完整的 LLM 调用逻辑 |
| `analyzer/cpp_analyzer.py` | C++ 代码分析器，输出 JSON 格式的分析报告 |
| `analyzer/code_fixer.py` | 代码修复器，返回修复后的完整代码 |
| `analyzer/code_agent.py` | 智能 Agent，根据问题严重程度自主决策 |
| `ui/main_window.py` | 主窗口，包含菜单栏、编辑器、Tab结果区、按钮区 |
| `ui/code_editor.py` | 自定义代码编辑器组件，支持行号显示 |
| `ui/cpp_highlighter.py` | C++ 语法高亮器，基于 QSyntaxHighlighter |
| `test.cpp` | 测试用 C++ 代码文件 |

---

## 🔮 未来展望

- [ ] 支持更多编程语言（Python、JavaScript 等）
- [ ] 集成静态分析工具（如 Clang-Tidy、Cppcheck）作为 AI 的辅助输入
- [ ] 支持代码 diff 可视化对比
- [ ] 添加项目文件树，支持多文件管理
- [ ] 引入本地模型支持，降低 API 调用成本

---

## 📄 License

MIT License

---

> 本项目为 AI IDE 技术演示项目，展示了如何将大语言模型能力封装为实用的开发工具。
