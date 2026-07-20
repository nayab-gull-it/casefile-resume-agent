import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file

import database as db
import llm_agent as agent
import file_generator as fg

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
ALLOWED_EXT = {"pdf", "docx", "txt"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

# This must run on import (not just when run directly with `python app.py`),
# because gunicorn imports this module instead of executing it as __main__.
# Without this, the database tables never get created on Render.
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
db.init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/")
def index():
    resume = db.get_resume()
    return render_template("index.html", resume=resume)


@app.route("/api/resume", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["resume"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Please upload a .pdf, .docx, or .txt file"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    saved_name = f"{uuid.uuid4().hex}.{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)
    file.save(saved_path)

    try:
        raw_text = fg.extract_text(saved_path)
        if not raw_text.strip():
            return jsonify({"error": "Couldn't read any text from that file"}), 400
        structured = agent.parse_resume_to_structured(raw_text)
        db.save_resume(file.filename, raw_text, structured)
        return jsonify({"ok": True, "resume": structured})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(saved_path):
            os.remove(saved_path)


@app.route("/api/resume", methods=["DELETE"])
def delete_resume():
    db.delete_resume()
    return jsonify({"ok": True})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    jd_text = (data.get("jd_text") or "").strip()
    if not jd_text:
        return jsonify({"error": "Paste a job description first"}), 400

    resume = db.get_resume()
    if not resume:
        return jsonify({"error": "Upload a resume first"}), 400

    try:
        result = agent.score_resume_against_jd(resume["structured"], jd_text)
        analysis_id = db.save_analysis(
            jd_text, result["score"], result.get("missing_keywords", []), result.get("suggestions", [])
        )
        return jsonify({
            "ok": True,
            "analysis_id": analysis_id,
            "score": result["score"],
            "missing_keywords": result.get("missing_keywords", []),
            "suggestions": result.get("suggestions", []),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tailor", methods=["POST"])
def tailor():
    data = request.get_json(force=True)
    analysis_id = data.get("analysis_id")
    analysis = db.get_analysis(analysis_id)
    resume = db.get_resume()
    if not analysis or not resume:
        return jsonify({"error": "Run an analysis first"}), 400

    try:
        tailored = agent.tailor_resume(resume["structured"], analysis["jd_text"], analysis["missing_keywords"])
        rescored = agent.score_resume_against_jd(tailored, analysis["jd_text"])
        db.update_analysis_tailored(analysis_id, rescored["score"], tailored)
        return jsonify({
            "ok": True,
            "tailored_resume": tailored,
            "new_score": rescored["score"],
            "original_score": analysis["original_score"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cover-letter", methods=["POST"])
def cover_letter():
    data = request.get_json(force=True)
    analysis_id = data.get("analysis_id")
    analysis = db.get_analysis(analysis_id)
    resume = db.get_resume()
    if not analysis or not resume:
        return jsonify({"error": "Run an analysis first"}), 400

    resume_for_letter = analysis["tailored_resume_json"] or resume["structured"]
    try:
        letter = agent.write_cover_letter(resume_for_letter, analysis["jd_text"])
        db.update_analysis_tailored(analysis_id, analysis["new_score"], analysis["tailored_resume_json"], letter)
        return jsonify({"ok": True, "cover_letter": letter})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<fmt>")
def download(fmt):
    analysis_id = request.args.get("analysis_id")
    resume_data = None
    if analysis_id:
        analysis = db.get_analysis(analysis_id)
        if analysis and analysis["tailored_resume_json"]:
            resume_data = analysis["tailored_resume_json"]
    if resume_data is None:
        resume = db.get_resume()
        if not resume:
            return jsonify({"error": "No resume available"}), 400
        resume_data = resume["structured"]

    name_slug = (resume_data.get("name") or "resume").strip().replace(" ", "_") or "resume"
    out_name = f"{name_slug}_resume.{fmt}"
    out_path = os.path.join(GENERATED_DIR, out_name)

    try:
        if fmt == "docx":
            fg.render_docx(resume_data, out_path)
        elif fmt == "pdf":
            fg.render_pdf(resume_data, out_path)
        else:
            return jsonify({"error": "Unsupported format"}), 400
        return send_file(out_path, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)