# Casefile — Resume Intelligence

An AI-powered resume assistant that analyzes how well your resume matches a job description, tailors it accordingly, and helps you generate a polished, ready-to-send version — all through a clean, case-file-inspired interface.

## Overview

Casefile helps job seekers quickly evaluate and improve their resumes against real job postings. Upload a resume once, paste in any job description, and get an instant match score along with specific, actionable suggestions — then let the tool rearrange and reword your resume (using only your real experience) to better align with that role.

## Features

- **Resume Upload** — Supports PDF, DOCX, and TXT formats. One resume is stored at a time, with options to replace or delete it.
- **Match Scoring** — Paste any job description to get a 0–100 match score, visualized through an animated instrument-panel style gauge.
- **Keyword Gap Analysis** — Highlights important keywords from the job description that are missing from your resume.
- **Actionable Suggestions** — Specific, practical recommendations to improve alignment with the role.
- **Resume Tailoring** — Reorders and rewords your resume to better match a job description, without inventing new experience or fabricating facts.
- **Before/After Comparison** — See your match score improve after tailoring.
- **Export Options** — Download your tailored resume as a PDF or DOCX file.
- **Cover Letter Generation** — Generates a short, professional, email-ready cover letter based on your resume and the job description.

## Tech Stack


|
 Layer 
|
 Technology 
|
|
---
|
---
|
|
 Backend 
|
 Python (Flask) 
|
|
 Database 
|
 SQLite 
|
|
 LLM 
|
 Groq API (
`llama-3.3-70b-versatile`
) 
|
|
 Document Generation 
|
`python-docx`
, 
`reportlab`
|
|
 Resume Parsing 
|
`pdfplumber`
|
|
 Frontend 
|
 HTML, CSS, JavaScript (custom, no framework) 
|

## Design

The interface follows a "dossier / case-file" visual theme — an ink-navy background with brass and gold accents, Fraunces serif headings, and an SVG instrument-panel style gauge for score visualization.

## Project Structure

career-agent/
├── app.py # Flask routes
├── database.py # SQLite (resume + analysis history)
├── llm_agent.py # Groq API calls (parse, score, tailor, cover letter)
├── file_generator.py # Resume text extraction + DOCX/PDF rendering
├── templates/index.html
├── static/css/style.css
├── static/js/script.js
├── requirements.txt
├── .gitignore
├── .env.example
├── Procfile # For deployment (gunicorn)
└── README.md


## Setup & Local Development

1. Clone the repository:
```bash
   git clone https://github.com/nayab-gull-it/casefile-resume-agent.git
   cd casefile-resume-agent
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Set your Groq API key as an environment variable:
```bash
   # Windows (PowerShell)
   $env:GROQ_API_KEY="your-api-key-here"

   # macOS/Linux
   export GROQ_API_KEY="your-api-key-here"
```

4. Run the app:
```bash
   python app.py
```

5. Open `http://localhost:5000` in your browser.

## Live Demo

*(Link will be added here once deployed.)*

## Notes

- This is a portfolio/demonstration project. On free hosting tiers, the app may sleep after inactivity and the local SQLite database resets on redeploy — expected behavior for a demo environment.
- The resume tailoring feature is designed to only reorganize and rephrase existing content — it does not fabricate experience, skills, or credentials.

## Author

Built by Nayab Gull.
