[中文](README.md) | [English](README_EN.md)
# Chronos - 生活事件驱动的学习伴侣

Chronos 是一个以“生活事件干扰”为核心亮点的 AI 学习系统。它鼓励用户在学习过程中表达真实的状态（如疲惫、忙碌、情绪波动），系统会将这些“抱怨”作为生活事件信号，交给“主任决策系统”实时调整学习计划，并在每日启动时提供可解释的简报。

## 项目亮点
- 生活事件驱动：把“现实干扰”变成可计算的学习信号。
- 主任决策系统：综合学习记录、周计划与生活事件，实时调整当日计划。
- 可解释调整：每日弹窗展示调整原因，用户可以接受或微调。

## 功能概览
- 每日简报弹窗：展示昨日快照与今日建议。
- 计划模块：根据压力与目标生成当天任务。
- AI 导师：多会话聊天，支持流式回复与图像教学。
- 记忆系统：保存偏好、事件、技能记忆，支持检索与更新。
- 知识图谱：基于学习记录生成概念网络。
- 设置中心：语言、学习偏好、模型配置等。

## 技术栈
- Python
- Flet
- SQLite / aiosqlite
- Google Gemini API
- PyVis

## 运行方式
1. 安装依赖（示例）
```bash
pip install flet google-genai aiosqlite numpy pydantic pyvis pytest
```
2. 配置 API Key（二选一）
- 环境变量方式：`GEMINI_API_KEY=你的密钥`
- 或在设置页中填写 Gemini API Key
3. 启动应用
```bash
python main.py
```

## 重要说明
- 项目会在本地生成 `data/` 下的数据库与缓存文件。
- 请勿将 `data/*.db`、`data/images/`、`data/settings.json` 等文件提交到公开仓库。
- 已提供 `.gitignore` 过滤上述本地与敏感文件。
- ReMe 相关功能为可选依赖，未安装不影响核心流程。

## 测试
```bash
pytest
```
