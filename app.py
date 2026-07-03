from flask import Flask, render_template, request, redirect, url_for, session, send_file
from pdf_generator import generate_pdf
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

import hashlib
import os
import re
import uuid
import sqlite3
from dotenv import load_dotenv
from groq import Groq

import utils
print("utils imported successfully")

from resume_ranker import rank_resumes
from utils import extract_text_from_pdf

from llm_utils import generate_local_feedback

from database import (
    init_db,
    save_analysis,
    get_all_analyses,
    get_total_analyses,
    get_avg_scores,
    get_max_ats,
    create_user,
    get_user,
    delete_analysis,
    get_user_analysis_count,
    get_best_ats,
    get_ats_distribution,
    get_upload_trend,
    get_ranked_resumes,
    init_cache_table,
    get_recent_analyses
)

from ml.parser import extract_text
from ml.matcher import match_skills, extract_skills
from ml.scorer import calculate_ats
from ml.similarity import calculate_similarity
from ml.nlp import extract_skills as spacy_extract_skills, extract_entities


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
cache = {}
latest_report = {}
app.secret_key = "resume_analyzer_secret_key"

# ---------- GROQ SETUP ----------
load_dotenv()
print("API KEY:", os.getenv("GROQ_API_KEY"))

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)

init_db()
init_cache_table()

# ---------- VALIDATION FUNCTIONS ----------
def is_strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
    return re.match(pattern, password)

def is_valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]{3,}@[A-Za-z0-9.-]{3,}\.[A-Za-z]{2,}$'
    return re.match(pattern, email)

def create_hash(text1, text2):
    combined = text1 + "||" + text2
    return hashlib.md5(combined.encode()).hexdigest()

def generate_ai_feedback(resume_text, job_desc):

    key = create_hash(resume_text, job_desc)

    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    # 🔍 CHECK CACHE FIRST
    cursor.execute(
        "SELECT feedback FROM ai_cache WHERE resume_hash=?",
        (key,)
    )
    row = cursor.fetchone()

    if row:
        conn.close()
        return row[0]   # ⚡ cached result

    # ❗ NOT IN CACHE → CALL GROQ
    try:
        prompt = f"""
You are an expert resume reviewer.

Return output ONLY in this format:

Strengths:
- point 1
- point 2
- point 3

Weaknesses:
- point 1
- point 2
- point 3

Missing Skills:
- point 1
- point 2
- point 3

Final Verdict:
- one short sentence only

Do NOT add any extra explanation or text.

Resume:
{resume_text}

Job:
{job_desc}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a career coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        result = response.choices[0].message.content

        # 💾 SAVE TO SQLITE CACHE
        cursor.execute(
            "INSERT INTO ai_cache (resume_hash, feedback) VALUES (?, ?)",
            (key, result)
        )

        conn.commit()
        conn.close()

        return result

    except Exception as e:
        print("🔥 GROQ ERROR:", e)
        return "AI feedback temporarily unavailable."
# ---------- AUTH ----------

@app.route("/")
def root():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        # Email format validation
        if not is_valid_email(email):
            return """
            <script>
                alert("Please enter a valid email address.");
                window.history.back();
            </script>
            """

        # Password empty check
        if len(password) == 0:
            return """
            <script>
                alert("Password cannot be empty.");
                window.history.back();
            </script>
            """

        user = get_user(email)

        if user and check_password_hash(user[3], password):
            session["user"] = user[1]
            session["email"] = user[2]
            return redirect("/dashboard")
        else:
            return """
            <script>
                alert("Invalid email or password.");
                window.history.back();
            </script>
            """

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        if not is_valid_email(email):
            return "Enter a valid email address"
        if "@" not in email or "." not in email:
            return "Invalid email format"
        
        password = request.form["password"]
        if not is_strong_password(password):
            return "Weak password"

        if len(password) < 6:
            return "Password must be at least 6 characters"

        hashed_password = generate_password_hash(password)

        try:
            create_user(username, email, hashed_password)
            return redirect("/login")
        except:
            return "User already exists"

    return render_template("signup.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()

        if not is_valid_email(email):
            return """
            <script>
                alert("Please enter a valid email address.");
                window.history.back();
            </script>
            """

        conn = sqlite3.connect("resume.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            return """
            <script>
                alert("No account found with this email.");
                window.history.back();
            </script>
            """

        token = str(uuid.uuid4())

        cursor.execute(
            "UPDATE users SET reset_token=? WHERE email=?",
            (token, email)
        )

        conn.commit()
        conn.close()

        return redirect(f"/reset-password/{token}")

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE reset_token=?",
        (token,)
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "Invalid or expired reset link"

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            conn.close()
            return """
            <script>
                alert("Passwords do not match.");
                window.history.back();
            </script>
            """

        if len(password) < 6:
            conn.close()
            return """
            <script>
                alert("Password must be at least 6 characters.");
                window.history.back();
            </script>
            """

        hashed = generate_password_hash(password)

        cursor.execute(
            "UPDATE users SET password=?, reset_token=NULL WHERE reset_token=?",
            (hashed, token)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    conn.close()
    return render_template("reset_password.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- MAIN APP ----------

@app.route("/analyzer")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("analyzer.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]
    job_desc = request.form["job_desc"]

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Extract resume text
    resume_text = extract_text(filepath)

    # OPTIMIZATION (IMPORTANT)
    resume_text = resume_text[:3000]
    job_desc = job_desc[:1500]

    # Skill matching
    matched, missing = match_skills(resume_text, job_desc)

    # Extract job skills
    job_skills = extract_skills(job_desc)

    # Skill score
    skill_score = 0
    if len(job_skills) > 0:
        skill_score = (len(matched) / len(job_skills)) * 100

    # ATS score
    ats_score = calculate_ats(matched, len(job_skills))

    # Similarity score
    similarity_score = calculate_similarity(resume_text, job_desc)

    # Final AI Ranking Score
    final_score = round(
        (ats_score * 0.4) +
        (similarity_score * 0.4) +
        (skill_score * 0.2),
        2
    )

    # NLP
    resume_skills_spacy = spacy_extract_skills(resume_text)
    resume_entities = extract_entities(resume_text)

    # Save to DB
    save_analysis(
        file.filename,
        ats_score,
        similarity_score,
        final_score
    )

    # Suggestions
    suggestions = []

    if "aws" in missing:
        suggestions.append("Consider learning AWS for cloud-related roles.")

    if "docker" in missing:
        suggestions.append("Docker is useful for deployment and DevOps roles.")

    if "machine learning" in missing:
        suggestions.append("Build ML projects to improve AI/ML profile.")

    if len(resume_entities) < 2:
        suggestions.append(
            "Consider adding education, company, or project details."
        )

    if len(resume_skills_spacy) < 4:
        suggestions.append(
            "Add more relevant technical skills to improve your resume."
        )

    if similarity_score < 50:
        suggestions.append(
            "Customize your resume according to the job description."
        )

    if ats_score >= 80:
        suggestions.append(
            "Excellent resume match!"
        )

    if not suggestions:
        suggestions.append("Great profile! Your resume matches well.")

    try:
        ai_feedback = generate_ai_feedback(resume_text, job_desc)
    except Exception as e:
        print("Groq error:", e)

    ai_feedback = generate_local_feedback(
        ats_score,
        similarity_score,
        matched,
        missing
    )

    global latest_report

    latest_report = {
        "filename": file.filename,
        "ats": ats_score,
        "similarity": similarity_score,
        "matched": matched,
        "missing": missing,
        "suggestions": suggestions
    }

    return render_template(
        "result.html",
        ats=ats_score,
        similarity=similarity_score,
        final_score=final_score,
        matched=matched,
        missing=missing,
        suggestions=suggestions,
        entities=resume_entities,
        ai_feedback=ai_feedback
    )


@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    records = get_all_analyses()
    formatted_records = []

    for row in records:
        formatted_time = "N/A"

        if row[5]:
            try:
                dt = datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                formatted_time = dt.strftime("%d %b %Y, %I:%M %p")
            except:
                formatted_time = row[5]

        formatted_records.append((
            row[0],   # id
            row[1],   # filename
            row[2],   # ats
            row[3],   # similarity
            row[4],   # final score
            row[5],   # raw timestamp
            formatted_time
        ))

    return render_template("history.html", records=formatted_records)


@app.route("/delete-history/<int:record_id>")
def delete_history(record_id):
    if "user" not in session:
        return redirect("/login")

    delete_analysis(record_id)
    return redirect("/history")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    total = get_total_analyses()
    avg_ats, avg_similarity = get_avg_scores()
    max_ats = get_max_ats()
    records = get_recent_analyses(2)
    ats_data = get_ats_distribution()
    upload_data = get_upload_trend()
    status = "Analysis Active" if total > 0 else "Waiting for Resume Upload"

    return render_template(
    "dashboard.html",
    total=total,
    avg_ats=avg_ats,
    avg_similarity=avg_similarity,
    max_ats=max_ats,
    records=records,
    username=session["user"],
    ats_data=ats_data,
    upload_data=upload_data,
    status=status
)


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    total_uploads = get_user_analysis_count()
    avg_ats, _ = get_avg_scores()
    best_ats = get_best_ats()

    return render_template(
        "profile.html",
        username=session["user"],
        email=session["email"],
        total_uploads=total_uploads,
        avg_ats=avg_ats,
        best_ats=best_ats
    )


@app.route("/download-report")
def download_report():
    global latest_report

    pdf_file = generate_pdf(
        latest_report["filename"],
        latest_report["ats"],
        latest_report["similarity"],
        latest_report["matched"],
        latest_report["missing"],
        latest_report["suggestions"]
    )

    return send_file(pdf_file, as_attachment=True)



@app.route("/ranking")
def ranking():
    records = get_ranked_resumes()
    return render_template("ranking.html", records=records)

@app.route("/rank", methods=["GET", "POST"])
def rank():
    if request.method == "POST":

        job_description = request.form["jd"]

        files = request.files.getlist("resumes")

        resume_texts = []

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            text = extract_text_from_pdf(open(path, "rb"))
            resume_texts.append(text)

        results = rank_resumes(job_description, resume_texts)

        return render_template("rank.html", results=results)

    return render_template("rank.html")


if __name__ == "__main__":
    app.run(debug=True)

