"""
llm_agent.py
All calls to Groq live here. Every prompt asks for strict JSON back so the
Flask layer never has to parse free-form text.
"""
import os
import json
from groq import Groq, RateLimitError, APIStatusError

MODEL = "llama-3.3-70b-versatile"

client = None


class AgentBusyError(Exception):
    """Raised when the LLM provider is temporarily unavailable or rate-limited.
    Flask routes should catch this and show a friendly message to the user."""
    pass


def get_client():
    global client
    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        client = Groq(api_key=api_key)
    return client


def _call_json(system_prompt, user_prompt):
    """Call Groq and parse the response as JSON, tolerating stray markdown fences."""
    try:
        resp = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
    except RateLimitError:
        raise AgentBusyError(
            "The AI service is currently receiving too many requests. Please try again in a minute."
        )
    except APIStatusError:
        raise AgentBusyError(
            "The AI service is temporarily unavailable. Please try again shortly."
        )

    text = resp.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def parse_resume_to_structured(raw_text):
    """Turn raw extracted resume text into a clean structured JSON we can reuse
    for scoring, tailoring, and later re-rendering into DOCX/PDF."""
    system = (
        "You convert raw resume text into structured JSON. Never invent facts that "
        "are not present in the source text. Preserve all real information exactly. "
        "Each distinct achievement or responsibility line under a job or project must "
        "become its own separate string in the 'bullets' array — never combine several "
        "bullet points into one long string, even if the original formatting is unclear."
    )
    user = f"""Convert this resume text into JSON with this exact shape:
{{
  "name": "",
  "contact": {{"email": "", "phone": "", "location": "", "links": []}},
  "summary": "",
  "skills": [],
  "experience": [{{"title": "", "company": "", "dates": "", "bullets": []}}],
  "education": [{{"degree": "", "institution": "", "dates": ""}}],
  "projects": [{{"name": "", "description": "", "bullets": []}}]
}}

Resume text:
---
{raw_text}
---
Return only the JSON object."""
    return _call_json(system, user)


def score_resume_against_jd(resume_structured, jd_text):
    """Score how well the current resume matches a job description."""
    system = (
        "You are an ATS and recruiter-style resume evaluator. Be honest and specific. "
        "Never invent resume content, only evaluate what is given."
    )
    user = f"""Resume (JSON):
{json.dumps(resume_structured)}

Job description:
---
{jd_text}
---

Return JSON exactly in this shape:
{{
  "score": 0,
  "missing_keywords": ["keyword1", "keyword2"],
  "suggestions": ["short actionable suggestion 1", "short actionable suggestion 2"]
}}
score is 0-100, how well the resume currently matches the job description.
missing_keywords are important JD terms/skills absent from the resume.
suggestions are short, specific, actionable improvements (max 5)."""
    return _call_json(system, user)


def tailor_resume(resume_structured, jd_text, missing_keywords):
    """Rearrange/reword the resume for this JD without inventing new facts."""
    system = (
        "You rewrite resumes to better match a job description. Rules: "
        "(1) Never invent experience, employers, dates, degrees, or skills the "
        "person does not already have. (2) You may reorder bullets/sections, "
        "rephrase wording, emphasize relevant existing skills, and naturally "
        "incorporate the person's real skills using JD-aligned terminology. "
        "(3) Keep the same factual content, just better presented for this JD. "
        "(4) CRITICAL: every 'bullets' array must stay an array of separate short "
        "bullet strings — the same number of bullets as the input, each rephrased "
        "individually. NEVER merge multiple bullets into one paragraph, and NEVER "
        "move bullet content into the 'summary' or 'description' fields. If the "
        "input experience/project entry has 4 bullets, the output must also have "
        "4 bullets for that entry."
    )
    user = f"""Original resume (JSON):
{json.dumps(resume_structured)}

Job description:
---
{jd_text}
---

Missing keywords noted by the evaluator (only use these if the person's existing
skills/experience genuinely justify it — do not fabricate): {json.dumps(missing_keywords)}

Return the tailored resume in the exact same JSON shape as the input resume.
Remember: bullets stay as separate array items, same count as the input, never merged."""
    tailored = _call_json(system, user)
    return _repair_missing_bullets(resume_structured, tailored)


def _repair_missing_bullets(original, tailored):
    """Safety net: if the model dropped or merged bullets for any entry, fall
    back to that entry's original bullets so nothing gets silently lost."""
    for key in ("experience", "projects"):
        orig_list = original.get(key, []) or []
        new_list = tailored.get(key, []) or []
        for i, orig_item in enumerate(orig_list):
            orig_bullets = orig_item.get("bullets", []) or []
            if i < len(new_list):
                new_bullets = new_list[i].get("bullets", []) or []
                if orig_bullets and len(new_bullets) < len(orig_bullets):
                    new_list[i]["bullets"] = orig_bullets
    return tailored


def write_cover_letter(resume_structured, jd_text):
    system = (
        "You write short, professional, natural-sounding cover letters suitable "
        "for pasting into an email body. No fluff, no clichés, 3 short paragraphs max."
    )
    user = f"""Resume (JSON):
{json.dumps(resume_structured)}

Job description:
---
{jd_text}
---

Return JSON: {{"cover_letter": "the full short cover letter as plain text with \\n\\n between paragraphs"}}"""
    result = _call_json(system, user)
    return result.get("cover_letter", "")