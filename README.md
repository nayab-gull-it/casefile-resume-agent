# Casefile — Resume Intelligence Agent

An AI agent that stores your resume once, scores it against any job description,
rewrites/rearranges it for that specific job (no invented facts), drafts a short
cover letter, and exports the result as PDF or DOCX.

This is a genuine **agent**, not a chat wrapper: it parses your resume into
structured data, calls the LLM as one step in a multi-step pipeline (parse →
score → tailor → re-score → generate files), and produces real downloadable
output — not just a chat reply.

## 1. Get a free Groq API key

1. Go to https://console.groq.com
2. Sign up (email or Google/GitHub, no credit card)
3. Create an API key from the dashboard

## 2. Run it locally

```bash
cd career-agent
pip install -r requirements.txt

# set your key (Mac/Linux)
export GROQ_API_KEY="your_key_here"
# set your key (Windows PowerShell)
$env:GROQ_API_KEY="your_key_here"

python app.py
```

Open http://localhost:5000 in your browser.

## 3. Deploy it for free (so you can put a live link on LinkedIn/CV)

**Render.com (recommended, free tier):**
1. Push this folder to a GitHub repo
2. On render.com → New → Web Service → connect your repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (add `gunicorn` to requirements.txt first)
5. Add environment variable `GROQ_API_KEY` in Render's dashboard
6. Deploy — you'll get a live URL like `casefile-yourname.onrender.com`

Note: Render's free tier sleeps after inactivity and the SQLite file resets on
redeploy — fine for a portfolio demo, not for real production use.

## How it avoids running out of free-tier requests

Each full run (upload → score → tailor → cover letter) uses about 4 API calls.
Groq's free tier allows roughly 1,000 requests/day, so you have room for 200+
full runs per day — more than enough for demos and recruiters trying it live.

## Project structure

```
career-agent/
├── app.py              # Flask routes
├── database.py         # SQLite (resume + analysis history)
├── llm_agent.py         # All Groq calls (parse, score, tailor, cover letter)
├── file_generator.py   # Resume text extraction + DOCX/PDF rendering
├── templates/index.html
├── static/css/style.css
├── static/js/script.js
└── requirements.txt
```
