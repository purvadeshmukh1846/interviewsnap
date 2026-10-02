# 🎯 InterviewSnap

InterviewSnap is an AI mock interview coach built with Streamlit and Gemini.
Attach a screenshot of a job description (or paste it), and the AI interviews
you one question at a time, giving feedback and a better sample answer after
each reply. One click emails you a full prep sheet to revise from.

## Features

- Gemini vision: reads job descriptions from screenshots
- Chat-based mock interview with feedback on every answer
- Scoped system prompt: only interview preparation topics
- Email summary (prep sheet) via Gmail SMTP

## Run locally

1. Clone the repo and create a virtual environment:

```
   python -m venv venv
```

Activate it, then install dependencies:

```
   pip install -r requirements.txt
```

2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:
   - `GEMINI_API_KEY` from Google AI Studio
   - `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` (Google Account > Security >
     2-Step Verification > App passwords)
3. Start the app:

```
   streamlit run app.py
```

## Deploy

Push to GitHub (never commit `secrets.toml`), then deploy on Streamlit
Community Cloud and paste your secrets in Settings > Secrets.
