# C4 技能分享与传播 — slide-forge 交付物

> 挑战：Elite20 **C4 技能分享与传播** ｜ 作者：lsa ｜ 技能：**slide-forge**（AI 幻灯片锻造流水线）

## 一句话

**输入** 一个主题或 Markdown 大纲 → **输出** 可直接放映的 HTML 幻灯片 + 逐页演讲词。

## 交付物清单

| 文件 | 说明 |
| --- | --- |
| `lsa_C4_skill说明.md` | 技能说明（问题 / 场景 / IO / 步骤 / 案例 / 传播计划） |
| `lsa_C4_slide-forge.skill` | 可安装的技能包（ZIP） |
| `slide-forge/` | 技能源目录（SKILL.md + 脚本 + references + examples + README） |
| `lsa_C4_demo.html` / `lsa_C4_demo.png` | 演示（live demo + 输入→输出截图） |
| `lsa_C4_教学说明.md` | 教学说明（上手 / 常见坑 / 优化技巧） |
| `lsa_C4_AI日志.md` | AI 使用日志（7 轮迭代记录） |
| `lsa_C4_AAR.md` | 项目复盘 AAR |

## 快速上手（零依赖）

```bash
# 解压技能包（本质是 ZIP）
unzip lsa_C4_slide-forge.skill
# 直接运行示例大纲，生成幻灯片
python slide-forge/scripts/build_slides.py slide-forge/examples/sample-outline.md -o demo.html
```

双击 `demo.html` 即可放映：`→/空格` 翻页 · `S` 看演讲词 · `F` 全屏 · `Ctrl+P` 导出 PDF。
