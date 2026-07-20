let currentAnalysisId = null;

const $ = (id) => document.getElementById(id);

function setStatus(el, msg, type) {
  el.textContent = msg || "";
  el.className = "status-line" + (type ? " " + type : "");
}

// ---------- Resume upload ----------
const resumeInput = $("resume-input");
$("browse-btn").addEventListener("click", (e) => { e.stopPropagation(); resumeInput.click(); });
$("resume-empty").addEventListener("click", () => resumeInput.click());
$("replace-btn").addEventListener("click", () => resumeInput.click());

$("resume-empty").addEventListener("dragover", (e) => { e.preventDefault(); e.currentTarget.style.borderColor = "#b08d57"; });
$("resume-empty").addEventListener("dragleave", (e) => { e.currentTarget.style.borderColor = ""; });
$("resume-empty").addEventListener("drop", (e) => {
  e.preventDefault();
  e.currentTarget.style.borderColor = "";
  if (e.dataTransfer.files.length) {
    resumeInput.files = e.dataTransfer.files;
    uploadResume();
  }
});

resumeInput.addEventListener("change", uploadResume);

async function uploadResume() {
  const file = resumeInput.files[0];
  if (!file) return;
  const statusEl = $("resume-status");
  setStatus(statusEl, "Reading resume…");
  const fd = new FormData();
  fd.append("resume", file);
  try {
    const res = await fetch("/api/resume", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");
    $("resume-name").textContent = data.resume.name || "Resume stored";
    $("resume-filename").textContent = file.name;
    $("resume-empty").classList.add("hidden");
    $("resume-loaded").classList.remove("hidden");
    setStatus(statusEl, "Resume stored.", "ok");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
}

$("delete-btn").addEventListener("click", async () => {
  await fetch("/api/resume", { method: "DELETE" });
  $("resume-loaded").classList.add("hidden");
  $("resume-empty").classList.remove("hidden");
  setStatus($("resume-status"), "Resume deleted.", "ok");
});

// ---------- Analyze ----------
$("analyze-btn").addEventListener("click", async () => {
  const jdText = $("jd-text").value.trim();
  const statusEl = $("jd-status");
  if (!jdText) { setStatus(statusEl, "Paste a job description first.", "error"); return; }
  setStatus(statusEl, "Scoring your resume against this job…");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed");
    currentAnalysisId = data.analysis_id;
    showResults(data);
    setStatus(statusEl, "", "");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

function setGauge(score) {
  const circumference = 251;
  const offset = circumference - (circumference * Math.min(score, 100)) / 100;
  $("gauge-fill").style.strokeDashoffset = offset;
  const angle = -90 + (Math.min(score, 100) / 100) * 180;
  $("gauge-needle").style.transform = `rotate(${angle}deg)`;
  $("score-value").textContent = score;
}

function showResults(data) {
  $("results-panel").classList.remove("hidden");
  setGauge(data.score);
  const chipRow = $("missing-keywords");
  chipRow.innerHTML = "";
  (data.missing_keywords || []).forEach(k => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = k;
    chipRow.appendChild(chip);
  });
  if (!data.missing_keywords || !data.missing_keywords.length) {
    chipRow.innerHTML = '<span class="chip" style="background:rgba(58,107,103,0.12);color:#3a6b67;">none — good coverage</span>';
  }
  const list = $("suggestions-list");
  list.innerHTML = "";
  (data.suggestions || []).forEach(s => {
    const li = document.createElement("li");
    li.textContent = s;
    list.appendChild(li);
  });
  $("compare-panel").classList.add("hidden");
  $("letter-panel").classList.add("hidden");
  $("results-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ---------- Tailor ----------
$("tailor-btn").addEventListener("click", async () => {
  if (!currentAnalysisId) return;
  const statusEl = $("tailor-status");
  setStatus(statusEl, "Rearranging your resume for this job…");
  try {
    const res = await fetch("/api/tailor", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis_id: currentAnalysisId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Tailoring failed");
    $("score-before").textContent = data.original_score;
    $("score-after").textContent = data.new_score;
    $("compare-panel").classList.remove("hidden");
    $("compare-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
    setStatus(statusEl, "", "");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

// ---------- Cover letter ----------
$("letter-btn").addEventListener("click", async () => {
  if (!currentAnalysisId) return;
  const statusEl = $("tailor-status");
  setStatus(statusEl, "Drafting cover letter…");
  try {
    const res = await fetch("/api/cover-letter", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis_id: currentAnalysisId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Cover letter failed");
    $("letter-text").textContent = data.cover_letter;
    $("letter-panel").classList.remove("hidden");
    $("letter-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
    setStatus(statusEl, "", "");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

$("copy-letter-btn").addEventListener("click", () => {
  navigator.clipboard.writeText($("letter-text").textContent);
  const btn = $("copy-letter-btn");
  const original = btn.textContent;
  btn.textContent = "Copied";
  setTimeout(() => { btn.textContent = original; }, 1500);
});

// ---------- Downloads ----------
$("download-pdf").addEventListener("click", () => downloadFile("pdf"));
$("download-docx").addEventListener("click", () => downloadFile("docx"));

function downloadFile(fmt) {
  const url = `/api/download/${fmt}` + (currentAnalysisId ? `?analysis_id=${currentAnalysisId}` : "");
  window.location.href = url;
}
