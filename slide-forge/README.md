# slide-forge

> 把一份 Markdown 大纲「锻造」成可直接放映的 HTML 幻灯片 + 逐页演讲词。
> 输入一个主题或大纲 → 输出能直接放映、可打印成 PDF 的幻灯片。

---

## 一句话

**输入** Markdown 大纲 → **输出** 单文件 HTML 幻灯片（键盘翻页 / S 键看演讲词 / F 全屏）。

## 快速开始（零安装，10 秒）

本技能脚本只用 Python 标准库，**无需 pip install**：

```bash
python scripts/build_slides.py examples/sample-outline.md -o slides.html
```

双击 `slides.html` 即可放映。

## 如何安装为 Skill（可选）

- **方式 A — 直接跑脚本（推荐）**：解压后运行上面的命令，不依赖任何 AI 环境。
- **方式 B — Claude 环境**：把 `lsa_C4_slide-forge.skill` 导入 Claude 的技能库（拖入文件或通过技能管理导入），之后说"帮我把这个大纲做成幻灯片"即可触发。
- **方式 C — WorkBuddy 环境**：将解压出的 `slide-forge` 目录放入技能目录（`~/.workbuddy/skills/`），或通过技能管理导入 `.skill` 包。

> `.skill` 文件本质是一个 ZIP 压缩包（内含 `slide-forge/` 目录），解压即得源文件。

## 目录结构

```
slide-forge/
├── SKILL.md                     # 主指令：3 步工作流 + 边界情况 + 示例
├── README.md                    # 本文件
├── scripts/
│   └── build_slides.py          # 零依赖：Markdown 大纲 → HTML 幻灯片
├── references/
│   ├── slide-design-guide.md    # 设计规范（结论式标题、7 页叙事骨架）
│   └── prompt-templates.md      # 5 个可复用 prompt 模板
└── examples/
    └── sample-outline.md        # 可直接运行的示例大纲
```

## 依赖

- Python 3.8+（Windows / macOS / Linux 均可）
- **零第三方库**

## 大纲格式约定

```markdown
# 演示总标题            ← 封面
## 结论式页标题          ← 每一页
- 要点（一句话）
    - 子要点（缩进两格）
> 演讲词：这一页你想说的话
```

更多用法、常见坑与优化技巧见外层《教学说明》，完整 prompt 模板见 `references/prompt-templates.md`。
