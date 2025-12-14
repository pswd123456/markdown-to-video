## 项目概述

本项目是一个基于 LLM 和 Manim 引擎的自动化技术视频生成系统。核心目标是将文本技术草稿自动转化为高质量的 MP4 视频讲解。

采用 "Robust Context-Driven" 架构。

## 核心设计理念 (Design Philosophy)

AI 在编写代码时必须严格遵循以下三大原则：

1.  **Context Injection (上下文注入):**
    - 不依赖 LLM 的训练记忆来生成 Manim 代码。
    - **必须** 依赖动态注入的 `api_stubs.txt` (API定义) 和 `examples.txt` (One-Shot 示例)。
    - 这解决了 Manim 版本更新导致的 API 幻觉问题。

2.  **Fail-Fast (快速失败机制):**
    - 在渲染像素前，必须先通过 `Linter`。
    - `Linter` 包含 AST 语法检查和 Dry Run (空运行)。
    - **原则**: 让低级错误在生成 Python 代码阶段就被拦截，不消耗 GPU 资源。

3.  **Semantic Correction (语义化修正):**
    - 视觉审查 (Vision Critic) **禁止** 输出像素坐标建议 (如 "向右移 20px")。
    - **必须** 输出基于组件关系的语义化指令 (如 "使用 `next_to(A, B, RIGHT)` 修正重叠")。

## 业务流程简述
1.  **Input**: 用户草稿 -> 场景 JSON。
2.  **Code Loop**: LLM 生成代码 -> Linter 检查 -> (失败则重写) -> Pass。
3.  **Visual Loop**: Docker 渲染 -> 视觉大模型审查 -> (布局问题则语义化重写) -> Pass。
4.  **Output**: 合并视频片段与音频。