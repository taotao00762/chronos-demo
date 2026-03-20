# Chronos - Life Event-Driven Learning Companion

Chronos is an AI-powered learning system with "life event interference" as its core feature. It encourages users to express their real-time states during learning (such as fatigue, busyness, or emotional fluctuations). The system interprets these "complaints" as life event signals, enabling the "Director Decision System" to adjust learning plans in real time and deliver an explainable daily briefing at startup.

## Highlights

- **Life Event-Driven**: Transforms "real-life interruptions" into computable learning signals.
- **Director Decision System**: Integrates learning records, weekly plans, and life events to dynamically adjust the daily schedule.
- **Explainable Adjustments**: A daily popup explains the reasoning behind each adjustment, allowing users to accept or modify it.

## Features

- **Daily Briefing Popup**: Displays yesterday's snapshot and today's recommendations.
- **Planning Module**: Generates daily tasks based on pressure levels and goals.
- **AI Tutor**: Multi-session chat with streaming responses and image-based teaching.
- **Memory System**: Stores preferences, events, and skill memories with search and update support.
- **Knowledge Graph**: Generates concept networks based on learning records.
- **Settings Center**: Language, learning preferences, model configuration, and more.

## Tech Stack

- Python
- Flet
- SQLite / aiosqlite
- Google Gemini API
- PyVis

## Getting Started

1. **Install dependencies**

```bash
pip install flet google-genai aiosqlite numpy pydantic pyvis pytest
```

2. **Configure API Key** (choose one)
   - Environment variable: `GEMINI_API_KEY=your_key`
   - Or enter your Gemini API Key in the Settings page

3. **Run the application**

```bash
python main.py
```

## Important Notes

- The project generates database and server files under `data/` locally.
- Do not commit `data/*.db`, `data/images/`, or `data/settings.json` to public repositories.
- The `.gitignore` is pre-configured to filter out these local and sensitive files.
- ReMe-related features are optional dependencies — the core workflow runs without them.

## Testing

```bash
pytest
```
