import os, json, re, time
import requests
from datetime import datetime
from collections import Counter
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, abort, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")
app.url_map.strict_slashes = False
# =============================
# DB
# =============================
# =============================
# DB
# =============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "vector_ai.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

# =============================
# AUTH (Flask-Login) + CSRF
# =============================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

csrf = CSRFProtect(app)

# =============================
# CONFIG
# =============================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower().strip()

OLLAMA_BASE_URL = (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_URL")
        or "http://localhost:11434"
).rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

HH_BASE = "https://api.hh.ru"
HH_AREA_KZ = 40  # Казахстан
_INCL_CACHE = {}  # hh_id -> (ts, data)
_INCL_CACHE_TTL = 24 * 3600  # 24 часа

# =============================
# MODELS
# =============================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # student / employer / admin
    email = db.Column(db.String(190), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="user", uselist=False, cascade="all,delete")
    employer = db.relationship("Employer", backref="user", uselist=False, cascade="all,delete")


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)

    full_name = db.Column(db.String(120), default="")
    city = db.Column(db.String(120), default="")
    college = db.Column(db.String(200), default="")
    speciality = db.Column(db.String(200), default="")
    start_year = db.Column(db.String(20), default="")
    job_intent = db.Column(db.String(40), default="maybe")
    region = db.Column(db.String(120), default="Алматы")
    remote = db.Column(db.Boolean, default=False)
    notify = db.Column(db.Boolean, default=False)

    roles_csv = db.Column(db.String(500), default="")  # "роль1, роль2"

    # ===== RESUME / PORTFOLIO =====
    resume_title = db.Column(db.String(200), default="")
    resume_summary = db.Column(db.Text, default="")
    resume_contacts = db.Column(db.String(300), default="")  # телефон/telegram/email

    github_url = db.Column(db.String(300), default="")
    linkedin_url = db.Column(db.String(300), default="")
    portfolio_url = db.Column(db.String(300), default="")

    projects_json = db.Column(db.Text, default="[]")  # [{name,url,desc}]

    # ===== EDUCATION (где учится/учился) =====
    education_place = db.Column(db.String(200), default="")     # Колледж/ВУЗ/школа
    education_program = db.Column(db.String(200), default="")   # Направление/программа
    education_status = db.Column(db.String(80), default="")     # Учусь/Выпускник/и т.д.
    education_year = db.Column(db.String(40), default="")       # Курс/период

    # ===== JOB READINESS =====
    readiness_json = db.Column(db.Text, default="{}")  # {"resume_done":true,...}

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class StudentMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)      # system/user/assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    kind = db.Column(db.String(10), nullable=False)      # soft/hard
    name = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, default=0)


class StudentAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)

    personality_type = db.Column(db.String(10), default="")
    personality_short = db.Column(db.Text, default="")

    top_roles_json = db.Column(db.Text, default="[]")
    learning_plan_json = db.Column(db.Text, default="[]")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SkillSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    personality_type = db.Column(db.String(10), default="")
    skills_json = db.Column(db.Text, default="[]")   # list[{name,score,kind}]
    note = db.Column(db.String(120), default="после анализа")

class MarketFitSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.Column(db.String(120), default="")
    market_fit_percent = db.Column(db.Integer, default=0)  # 0-100
    missing_json = db.Column(db.Text, default="[]")        # list[str]
    have_json = db.Column(db.Text, default="[]")           # list[str]
    top_market_json = db.Column(db.Text, default="[]")     # list[str]
    note = db.Column(db.String(120), default="после анализа")

class Employer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)

    company = db.Column(db.String(200), default="")
    full_name = db.Column(db.String(120), default="")
    city = db.Column(db.String(120), default="Алматы")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmployerVacancyAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employer.id"), nullable=False, index=True)

    title = db.Column(db.String(250), default="")
    hh_id = db.Column(db.String(30), default="")
    skills_json = db.Column(db.Text, default="[]")  # list[str]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CandidateStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vacancy_analysis_id = db.Column(db.Integer, db.ForeignKey("employer_vacancy_analysis.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)

    percent = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="new")
    favorite = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, default="")

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("vacancy_analysis_id", "student_id", name="uq_vacancy_student"),
    )


class VacancyApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)

    hh_id = db.Column(db.String(30), nullable=False)   # id вакансии на HH
    hh_url = db.Column(db.Text, nullable=False)

    vacancy_name = db.Column(db.String(255), default="")
    employer_name = db.Column(db.String(255), default="")

    status = db.Column(db.String(30), default="sent")  # sent/viewed/interview/rejected/hired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("student_id", "hh_id", name="uq_student_hh_vacancy"),
    )


class VacancySkillSet(db.Model):
    """
    Канонический набор навыков для hh_id.
    Это "источник правды", чтобы проценты совпадали у студента и работодателя.
    """
    id = db.Column(db.Integer, primary_key=True)
    hh_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    skills_json = db.Column(db.Text, default="[]")  # list[str]
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)




@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


# =============================
# SECURITY HEADERS
# =============================
@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


# =============================
# ROLE GUARD
# =============================
def require_role(role: str):
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if getattr(current_user, "role", None) != role:
        abort(403)
    return None
def require_any_role(*roles: str):
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if getattr(current_user, "role", None) not in set(roles):
        abort(403)
    return None

# =============================
# TEXT HELPERS: RU guards
# =============================
def _has_latin(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text or ""))

def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text or ""))

def _is_ru_only(text: str) -> bool:
    t = (text or "").strip()
    return (not _has_latin(t)) and (not _has_cjk(t))

def _count_words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))

def _question_ok(text: str) -> bool:
    t = (text or "").strip()
    if not t.endswith("?"):
        return False
    if not _is_ru_only(t):
        return False
    if _count_words(t) > 12:
        return False
    return True

_ALLOWED_LATIN_TOKENS = {
    "frontend","backend","fullstack","devops","qa","ui","ux",
    "javascript","typescript","react","vue","angular","next","nuxt",
    "node","nodejs","express","nestjs","django","flask","fastapi",
    "html","css","sass","scss","js",
    "git","github","gitlab",
    "api","rest","graphql","sql","postgres","mysql","mongodb",
    "docker","kubernetes","k8s",
    "figma","jira","confluence",
    "aws","gcp","azure",
    "unity","c#","c++","python","java","kotlin","swift","go","rust",
}

_MBTI = {
    "INTJ","INTP","ENTJ","ENTP","INFJ","INFP","ENFJ","ENFP",
    "ISTJ","ISFJ","ESTJ","ESFJ","ISTP","ISFP","ESTP","ESFP"
}

def _has_latin_in_value(s: str) -> bool:
    if (s or "").strip() in _MBTI:
        return False
    return bool(re.search(r"[A-Za-z]", s or ""))

def _json_values_are_ru_only(obj) -> bool:
    if isinstance(obj, dict):
        return all(_json_values_are_ru_only(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_json_values_are_ru_only(x) for x in obj)
    if isinstance(obj, str):
        return (not _has_latin_in_value(obj)) and (not _has_cjk(obj))
    return True

# Небольшие алиасы, чтобы "питон" ~= "python" и т.п. (иначе часто 0%)
_SKILL_ALIASES = {
    "питон": "python",
    "пайтон": "python",
    "python": "python",
    "джанго": "django",
    "django": "django",
    "фласк": "flask",
    "flask": "flask",
    "фастапи": "fastapi",
    "fastapi": "fastapi",
    "джс": "javascript",
    "javascript": "javascript",
    "джаваскрипт": "javascript",
    "тайпскрипт": "typescript",
    "typescript": "typescript",
    "реакт": "react",
    "react": "react",
    "вью": "vue",
    "vue": "vue",
    "гит": "git",
    "git": "git",
    "гитхаб": "github",
    "github": "github",
    "постгрес": "postgres",
    "postgres": "postgres",
    "постгресql": "postgres",
    "sql": "sql",
    "докер": "docker",
    "docker": "docker",
    "кубернетес": "kubernetes",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
}

def norm_skill(s: str) -> str:
    s = (s or "").lower().strip()
    s = s.replace("ё", "е")
    s = re.sub(r"[^a-z0-9а-я\+#\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s in _SKILL_ALIASES:
        return _SKILL_ALIASES[s]
    return s

def strip_html(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


# =============================
# LLM HELPERS
# =============================
def _messages_to_prompt(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        role = (m.get("role") or "user").strip().lower()
        content = (m.get("content") or "").strip()

        if role == "system":
            parts.append(f"SYSTEM:\n{content}")
        elif role == "assistant":
            parts.append(f"ASSISTANT:\n{content}")
        else:
            parts.append(f"USER:\n{content}")
    return "\n\n".join(parts) + "\n\nASSISTANT:\n"

def _try_openrouter(messages: list[dict]) -> str:
    api_key = OPENROUTER_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise ValueError("No API key. Set OPENROUTER_API_KEY (or OPENAI_API_KEY).")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers=headers,
        json={"model": OPENAI_MODEL, "messages": messages, "temperature": 0.4},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return (data["choices"][0]["message"]["content"] or "").strip()

def _try_ollama(messages: list[dict]) -> str:
    prompt = _messages_to_prompt(messages)
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.1},
            "stop": ["\nUSER:", "\nSYSTEM:"],
        },
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()

def llm_chat(messages: list[dict]) -> str:
    provider = (LLM_PROVIDER or "auto").lower().strip()

    if provider in ("openai", "openrouter"):
        return _try_openrouter(messages)
    if provider == "ollama":
        return _try_ollama(messages)
    if provider == "auto":
        try:
            return _try_openrouter(messages)
        except Exception as e1:
            try:
                return _try_ollama(messages)
            except Exception as e2:
                raise RuntimeError(f"LLM failed. OpenRouter error: {e1}. Ollama error: {e2}")
    raise ValueError("Unknown LLM_PROVIDER. Use auto, ollama, openai/openrouter.")

def safe_json_from_text(text: str) -> dict:
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return {"ok": False, "error": "No JSON in LLM output", "raw": text}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"ok": False, "error": "Bad JSON", "raw": text}

def _repair_to_ru_question(bad_answer: str, last_user: str) -> str:
    prompt = [
        {"role": "system", "content": (
            "Перепиши текст в ОДИН вопрос на русском.\n"
            "Запрещены латиница и иероглифы.\n"
            "До 12 слов.\n"
            "Только вопрос со знаком '?'."
        )},
        {"role": "user", "content": f"Ответ студента: {last_user}"},
        {"role": "user", "content": f"Плохой вопрос: {bad_answer}"}
    ]
    return llm_chat(prompt).strip()

def _repair_to_ru_json(bad_text: str, schema_hint: str) -> str:
    prompt = [
        {"role": "system", "content": (
            "Верни ТОЛЬКО один валидный JSON по схеме ниже.\n"
            "Ключи JSON оставь ТОЧНО как в схеме (ключи могут быть на латинице).\n"
            "ЗНАЧЕНИЯ пиши ТОЛЬКО русской кириллицей.\n"
            "Запрещены транслит, латиница и иероглифы В ЗНАЧЕНИЯХ.\n"
            f"Схема:\n{schema_hint}\n"
            "Никакого текста до/после."
        )},
        {"role": "user", "content": bad_text}
    ]
    return llm_chat(prompt).strip()


# =============================
# SIMPLE RATE LIMIT (in-memory)
# =============================
_RATE = {}  # key -> [timestamps]
def rate_limit(key: str, limit: int = 20, window_s: int = 60) -> bool:
    now = time.time()
    arr = _RATE.get(key, [])
    arr = [t for t in arr if now - t < window_s]
    if len(arr) >= limit:
        _RATE[key] = arr
        return False
    arr.append(now)
    _RATE[key] = arr
    return True


# =============================
# HH HELPERS + cache (anti-lag)
# =============================
_HH_CACHE = {}  # (url, frozen_params) -> (ts, json)
_HH_TTL = 600  # было 30, подняли, чтобы не лагало и не било HH лишний раз

def _hh_get(url: str, params: dict | None = None, timeout: int = 30):
    key = (url, tuple(sorted((params or {}).items())))
    now = time.time()
    if key in _HH_CACHE:
        ts, data = _HH_CACHE[key]
        if now - ts < _HH_TTL:
            return data
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    _HH_CACHE[key] = (now, data)
    return data

def hh_search_vacancies(text: str, area: int = HH_AREA_KZ, per_page: int = 20, page: int = 0):
    params = {"text": text, "area": area, "per_page": per_page, "page": page}
    return _hh_get(f"{HH_BASE}/vacancies", params=params, timeout=30)

def hh_get_vacancy(hh_id: str) -> dict:
    return _hh_get(f"{HH_BASE}/vacancies/{hh_id}", params=None, timeout=30)


def _safe_load_json(s, default):
    try:
        return json.loads(s or "")
    except Exception:
        return default

def update_readiness_for_student(st: Student):
    r = _safe_load_json(getattr(st, "readiness_json", "") or "{}", {})
    r["analysis_done"] = bool(StudentAnalysis.query.filter_by(student_id=st.id).first())

    r["resume_done"] = bool(
        (st.resume_title or "").strip()
        and (st.resume_summary or "").strip()
        and (st.resume_contacts or "").strip()
    )

    projs = _safe_load_json(st.projects_json or "[]", [])
    r["projects_done"] = bool([p for p in projs if (p.get("name") or "").strip()])

    apps_count = VacancyApplication.query.filter_by(student_id=st.id).count()
    r["applications_done"] = apps_count >= 5

    st.readiness_json = json.dumps(r, ensure_ascii=False)
    return r

def readiness_score(st: Student) -> int:
    """
    0..100 — не просто ✅/❌.
    """
    score = 0
    r = _safe_load_json(getattr(st, "readiness_json", "") or "{}", {})

    if r.get("resume_done"): score += 25
    if r.get("analysis_done"): score += 20
    if r.get("projects_done"): score += 20
    if r.get("applications_done"): score += 20

    # market fit (последний снапшот)
    mf = (MarketFitSnapshot.query
          .filter_by(student_id=st.id)
          .order_by(MarketFitSnapshot.id.desc())
          .first())
    if mf:
        score += int(round(max(0, min(int(mf.market_fit_percent or 0), 100)) * 0.15))  # 0..15

    return max(0, min(score, 100))


def save_skill_snapshot(student_id: int, personality_type: str, note: str = "после анализа"):
    """
    Сохраняет историю навыков после каждого анализа.
    """
    rows = StudentSkill.query.filter_by(student_id=student_id).all()
    pack = []
    for s in rows:
        pack.append({
            "name": (s.name or ""),
            "score": int(s.score or 0),
            "kind": (s.kind or "")
        })

    snap = SkillSnapshot(
        student_id=student_id,
        personality_type=(personality_type or ""),
        skills_json=json.dumps(pack, ensure_ascii=False),
        note=(note or "после анализа")[:120],
    )
    db.session.add(snap)
    db.session.commit()


def save_market_fit_snapshot(student_id: int, role_query: str):
    """
    Сохраняет динамику соответствия рынку труда по роли.
    """
    # навыки студента
    sskills = StudentSkill.query.filter_by(student_id=student_id).all()
    student_skill_names = {norm_skill(s.name) for s in sskills if s.name}
    student_skill_names = {x for x in student_skill_names if x}

    # рынок vs студент
    gap = market_gap_for_role(role_query, student_skill_names, max_vac=20)
    top_market = gap.get("top_market") or []
    missing = gap.get("missing") or []
    have = gap.get("have") or []

    percent = 0
    if top_market:
        percent = int(round(len(have) / len(top_market) * 100))
    percent = max(0, min(percent, 100))

    row = MarketFitSnapshot(
        student_id=student_id,
        role=(role_query or "")[:120],
        market_fit_percent=percent,
        market_missing_json=json.dumps(missing, ensure_ascii=False),
    )
    db.session.add(row)
    db.session.commit()

    return {"percent": percent, "missing": missing, "have": have}

def market_gap_for_role(role_query: str, student_skill_names: set[str], max_vac: int = 20):
    hh = hh_search_vacancies(role_query, area=HH_AREA_KZ, per_page=min(20, max_vac), page=0)
    items = hh.get("items", []) or []

    counter = Counter()
    used = 0
    for it in items:
        hh_id = str(it.get("id") or "")
        if not hh_id:
            continue
        used += 1
        try:
            v = hh_get_vacancy(hh_id)
            ks = v.get("key_skills") or []
            for x in ks:
                if isinstance(x, dict) and x.get("name"):
                    counter[norm_skill(x["name"])] += 1
        except Exception:
            pass

    top_market = [k for k, _ in counter.most_common(20) if k]
    missing = [k for k in top_market if k not in student_skill_names][:12]
    have = [k for k in top_market if k in student_skill_names][:12]
    return {"role": role_query, "top_market": top_market, "have": have, "missing": missing, "used": used}

def market_fit_percent_from_gap(gap: dict) -> int:
    top_market = gap.get("top_market") or []
    have = gap.get("have") or []
    if not top_market:
        return 0
    return int(round((len(have) / len(top_market)) * 100))

# =============================
# HOME
# =============================
@app.get("/")
def home():
    return render_template("index.html")


# =============================
# AUTH ROUTES
# =============================
@app.get("/login")
def login():
    return render_template("auth/login.html")

@app.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password_hash, password):
        flash("Неверный email или пароль", "error")
        return redirect(url_for("login"))

    login_user(u)

    if u.role == "student":
        return redirect(url_for("student_profile"))
    if u.role == "employer":
        return redirect(url_for("employer_dashboard"))
    return redirect(url_for("home"))

@app.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.get("/register/student")
def register_student():
    return render_template("auth/register_student.html")

@app.post("/register/student")
def register_student_post():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    if not email or not password or len(password) < 6:
        flash("Введите корректный email и пароль (>=6 символов)", "error")
        return redirect(url_for("register_student"))

    if User.query.filter_by(email=email).first():
        flash("Этот email уже зарегистрирован", "error")
        return redirect(url_for("register_student"))

    u = User(role="student", email=email, password_hash=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()

    st = Student(user_id=u.id)
    db.session.add(st)
    db.session.commit()

    login_user(u)
    return redirect(url_for("student_onboarding"))

@app.get("/register/employer")
def register_employer():
    return render_template("auth/register_employer.html")

@app.post("/register/employer")
def register_employer_post():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    company = (request.form.get("company") or "").strip()

    if not email or not password or len(password) < 6:
        flash("Введите корректный email и пароль (>=6 символов)", "error")
        return redirect(url_for("register_employer"))

    if User.query.filter_by(email=email).first():
        flash("Этот email уже зарегистрирован", "error")
        return redirect(url_for("register_employer"))

    u = User(role="employer", email=email, password_hash=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()

    emp = Employer(user_id=u.id, company=company)
    db.session.add(emp)
    db.session.commit()

    login_user(u)
    return redirect(url_for("employer_dashboard"))


# =============================
# STUDENT AREA
# =============================
@app.get("/student")
def student_dashboard():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    sa = StudentAnalysis.query.filter_by(student_id=st.id).order_by(StudentAnalysis.id.desc()).first()
    return render_template("student/student.html", student=st, analysis=sa)

@app.route("/student/onboarding", methods=["GET", "POST"])
def student_onboarding():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        st = Student(user_id=current_user.id)
        db.session.add(st)
        db.session.commit()

    if request.method == "POST":
        roles = [x.strip() for x in (request.form.get("roles", "")).split(",") if x.strip()][:5]

        st.full_name = request.form.get("full_name", "").strip()
        st.city = request.form.get("city", "").strip()
        st.college = request.form.get("college", "").strip()
        st.speciality = request.form.get("speciality", "").strip()
        st.start_year = request.form.get("start_year", "").strip()
        st.job_intent = request.form.get("job_intent", "maybe").strip()
        st.roles_csv = ", ".join(roles)
        st.region = request.form.get("region", "Алматы").strip()
        st.remote = request.form.get("remote") == "on"
        st.notify = request.form.get("notify") == "on"

        db.session.commit()

        StudentMessage.query.filter_by(student_id=st.id).delete()
        StudentSkill.query.filter_by(student_id=st.id).delete()
        StudentAnalysis.query.filter_by(student_id=st.id).delete()
        db.session.commit()

        return redirect(url_for("student_interview"))

    profile = {
        "full_name": st.full_name,
        "city": st.city,
        "college": st.college,
        "speciality": st.speciality,
        "start_year": st.start_year,
        "job_intent": st.job_intent,
        "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
        "region": st.region,
        "remote": bool(st.remote),
        "notify": bool(st.notify),
    }
    return render_template("student/onboarding.html", profile=profile)

@app.get("/student/interview")
def student_interview():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return redirect(url_for("student_onboarding"))

    has_any = StudentMessage.query.filter_by(student_id=st.id).first()
    if not has_any:
        db.session.add(StudentMessage(
            student_id=st.id,
            role="system",
            content=(
                "Ты — карьерный интервьюер VECTOR AI.\n"
                "СТРОГО:\n"
                "1) Пиши ТОЛЬКО по-русски (кириллица). Запрещены латиница, транслит и иероглифы.\n"
                "2) Верни ОДИН вопрос за раз.\n"
                "3) Вопрос до 12 слов и обязательно заканчивается '?'.\n"
                "4) Никаких объяснений/списков/приветствий.\n"
                "5) Если ответ общий — задай один уточняющий вопрос.\n"
                "Собирай: interests, thinking_style, motivation, environment, skills.\n"
            )
        ))
        db.session.add(StudentMessage(
            student_id=st.id,
            role="assistant",
            content="Привет! Расскажи, что тебе больше всего нравится делать?"
        ))
        db.session.commit()

    profile = {
        "full_name": st.full_name,
        "city": st.city,
        "college": st.college,
        "speciality": st.speciality,
        "start_year": st.start_year,
        "job_intent": st.job_intent,
        "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
        "region": st.region,
        "remote": bool(st.remote),
        "notify": bool(st.notify),
    }
    return render_template("student/interview.html", profile=profile)


# JSON endpoints: CSRF exempt (иначе fetch без токена будет падать)
@csrf.exempt
@app.get("/student/api/interview/state")
def student_api_interview_state():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    msgs = StudentMessage.query.filter_by(student_id=st.id).order_by(StudentMessage.id.asc()).all()

    q_count = 0
    last_q = None
    for m in msgs:
        if m.role == "assistant" and (m.content or "").strip().endswith("?"):
            q_count += 1
            last_q = m.content

    done = q_count >= 6
    return jsonify({"ok": True, "question": last_q, "q_count": q_count, "done": done})

@csrf.exempt
@app.post("/student/api/resume/generate")
def student_api_resume_generate():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return jsonify({"ok": False, "error": "no_student"}), 400

    key = f"st:{st.id}:resume_gen"
    if not rate_limit(key, limit=6, window_s=300):
        return jsonify({"ok": False, "error": "too_many_requests"}), 429

    # данные студента
    sa = StudentAnalysis.query.filter_by(student_id=st.id).order_by(StudentAnalysis.id.desc()).first()

    hard = StudentSkill.query.filter_by(student_id=st.id, kind="hard").order_by(StudentSkill.score.desc()).all()
    soft = StudentSkill.query.filter_by(student_id=st.id, kind="soft").order_by(StudentSkill.score.desc()).all()

    profile = {
        "full_name": st.full_name,
        "city": st.city,
        "college": st.college,
        "speciality": st.speciality,
        "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
        "remote": bool(st.remote),
        "personality_type": (sa.personality_type if sa else ""),
        "personality_short": (sa.personality_short if sa else ""),
        "hard_skills": [{"name": s.name, "score": s.score} for s in hard[:12]],
        "soft_skills": [{"name": s.name, "score": s.score} for s in soft[:12]],
    }

    # схема (JSON-only)
    schema_hint = (
        "{"
        "\"resume_title\":\"желаемая позиция\","
        "\"resume_summary\":\"2-4 предложения о себе (без выдуманного опыта)\","
        "\"projects\":[{\"name\":\"...\",\"url\":\"\",\"desc\":\"что сделал и стек\"}],"
        "\"github_url\":\"\","
        "\"portfolio_url\":\"\","
        "\"linkedin_url\":\"\""
        "}"
    )

    prompt = [
        {"role": "system", "content": (
            "Ты помощник по резюме для студента.\n"
            "Верни ТОЛЬКО один валидный JSON без текста до/после.\n"
            "Не выдумывай опыт/компании/дипломы. Если данных нет — пиши аккуратно 'учусь', 'делаю проекты'.\n"
            "Пиши по-русски (кириллица). Технологии можно латиницей (Python, React, Git).\n"
            "Схема:\n" + schema_hint
        )},
        {"role": "user", "content": json.dumps(profile, ensure_ascii=False)}
    ]

    try:
        raw = llm_chat(prompt).strip()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

    data = safe_json_from_text(raw)
    if not data.get("resume_title"):
        try:
            repaired = _repair_to_ru_json(raw, schema_hint)
            data = safe_json_from_text(repaired)
        except Exception:
            pass

    # финальный фолбэк
    if not data.get("resume_title"):
        roles = profile["roles"] or ["Junior специалист"]
        data = {
            "resume_title": roles[0],
            "resume_summary": "Я студент и развиваюсь в выбранном направлении. Люблю учиться, быстро разбираюсь в новых задачах и хочу получить практический опыт в реальных проектах.",
            "projects": [],
            "github_url": "",
            "portfolio_url": "",
            "linkedin_url": ""
        }

    # ограничим проекты
    projects = data.get("projects") or []
    if not isinstance(projects, list):
        projects = []
    projects = projects[:3]

    return jsonify({
        "ok": True,
        "resume_title": (data.get("resume_title") or "").strip(),
        "resume_summary": (data.get("resume_summary") or "").strip(),
        "projects": projects,
        "github_url": (data.get("github_url") or "").strip(),
        "portfolio_url": (data.get("portfolio_url") or "").strip(),
        "linkedin_url": (data.get("linkedin_url") or "").strip()
    })




@app.route("/student/resume", methods=["GET", "POST"])
def student_resume():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return redirect(url_for("student_onboarding"))

    if request.method == "POST":
        st.resume_title = (request.form.get("resume_title") or "").strip()
        st.resume_summary = (request.form.get("resume_summary") or "").strip()
        st.resume_contacts = (request.form.get("resume_contacts") or "").strip()

        # ===== EDUCATION SAVE =====
        st.education_place = (request.form.get("education_place") or "").strip()
        st.education_program = (request.form.get("education_program") or "").strip()
        st.education_status = (request.form.get("education_status") or "").strip()
        st.education_year = (request.form.get("education_year") or "").strip()

        st.github_url = (request.form.get("github_url") or "").strip()
        st.linkedin_url = (request.form.get("linkedin_url") or "").strip()
        st.portfolio_url = (request.form.get("portfolio_url") or "").strip()

        projects = []
        for i in range(1, 4):
            name = (request.form.get(f"proj{i}_name") or "").strip()
            url = (request.form.get(f"proj{i}_url") or "").strip()
            desc = (request.form.get(f"proj{i}_desc") or "").strip()
            if name:
                projects.append({"name": name, "url": url, "desc": desc})
        st.projects_json = json.dumps(projects, ensure_ascii=False)

        update_readiness_for_student(st)
        db.session.commit()

        flash("Резюме сохранено", "success")
        return redirect(url_for("student_profile"))

    projects = _safe_load_json(st.projects_json or "[]", [])
    while len(projects) < 3:
        projects.append({"name": "", "url": "", "desc": ""})

    return render_template("student/resume_edit.html", student=st, projects=projects)


@app.get("/student/applications")
def student_applications():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    rows = VacancyApplication.query.filter_by(student_id=st.id).order_by(VacancyApplication.id.desc()).all()

    stats = {"sent": 0, "viewed": 0, "interview": 0, "rejected": 0, "hired": 0}
    for r in rows:
        if r.status in stats:
            stats[r.status] += 1

    return render_template("student/applications.html", rows=rows, stats=stats)


@app.get("/student/market-bridge")
def student_market_bridge():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    roles = [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()] or ["Junior Developer"]
    q = (request.args.get("q") or roles[0]).strip()

    sskills = StudentSkill.query.filter_by(student_id=st.id).all()
    student_skill_names = {norm_skill(s.name) for s in sskills if s.name}
    student_skill_names = {x for x in student_skill_names if x}

    gap = market_gap_for_role(q, student_skill_names, max_vac=20)
    return render_template("student/market_bridge.html", roles=roles, q=q, gap=gap)


@app.get("/student/profile")
def student_profile():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return redirect(url_for("student_onboarding"))

    sa = (StudentAnalysis.query
          .filter_by(student_id=st.id)
          .order_by(StudentAnalysis.id.desc())
          .first())

    soft = (StudentSkill.query
            .filter_by(student_id=st.id, kind="soft")
            .order_by(StudentSkill.score.desc())
            .all())

    hard = (StudentSkill.query
            .filter_by(student_id=st.id, kind="hard")
            .order_by(StudentSkill.score.desc())
            .all())

    projects = _safe_load_json(st.projects_json or "[]", [])
    readiness = update_readiness_for_student(st)

    # applications stats
    rows = VacancyApplication.query.filter_by(student_id=st.id).all()
    app_stats = {"sent": 0, "viewed": 0, "interview": 0, "rejected": 0, "hired": 0}
    for r in rows:
        if r.status in app_stats:
            app_stats[r.status] += 1

    # market gap preview by first role
    roles = [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()] or ["Junior Developer"]
    sskills = StudentSkill.query.filter_by(student_id=st.id).all()
    student_skill_names = {norm_skill(s.name) for s in sskills if s.name}
    student_skill_names = {x for x in student_skill_names if x}
    gap_preview = market_gap_for_role(roles[0], student_skill_names, max_vac=15)

    # history snapshots (skills)
    history_rows = (SkillSnapshot.query
                    .filter_by(student_id=st.id)
                    .order_by(SkillSnapshot.created_at.desc())
                    .limit(10).all())

    history = []
    for h in history_rows:
        skills = _safe_load_json(h.skills_json or "[]", [])
        history.append({
            "created_at": h.created_at,
            "personality_type": h.personality_type,
            "skills": skills,
            "note": h.note
        })

    # market fit history (динамика соответствия рынку)
    market_rows = (MarketFitSnapshot.query
                   .filter_by(student_id=st.id)
                   .order_by(MarketFitSnapshot.created_at.desc())
                   .limit(10).all())

    market_history = []
    for r in market_rows:
        market_history.append({
            "created_at": r.created_at,
            "role": r.role,
            "percent": r.market_fit_percent,
            "missing": _safe_load_json(r.missing_json or "[]", []),
            "have": _safe_load_json(r.have_json or "[]", []),
        })

    return render_template(
        "student/profile.html",
        student=st,
        analysis=sa,
        soft=soft,
        hard=hard,
        projects=projects,
        readiness=readiness,
        app_stats=app_stats,
        gap_preview=gap_preview,
        history=history,
        market_history=market_history
    )



@csrf.exempt
@app.post("/student/api/interview")
def student_api_interview():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()

    msg = ((request.get_json(silent=True) or {}).get("message") or "").strip()
    if not msg:
        return jsonify({"ok": False, "error": "empty"}), 400

    key = f"st:{st.id}:interview"
    if not rate_limit(key, limit=25, window_s=60):
        return jsonify({"ok": False, "error": "too_many_requests"}), 429

    MAX_Q = 6

    msgs = StudentMessage.query.filter_by(student_id=st.id).order_by(StudentMessage.id.asc()).all()
    convo = [{"role": m.role, "content": m.content} for m in msgs]

    q_count = sum(1 for m in convo if m["role"] == "assistant" and (m["content"] or "").strip().endswith("?"))

    db.session.add(StudentMessage(student_id=st.id, role="user", content=msg))
    db.session.commit()

    if q_count >= MAX_Q:
        return jsonify({"ok": True, "answer": "Готово. Жми “Завершить и анализировать”.", "q_count": MAX_Q, "done": True})

    convo.append({"role": "user", "content": msg})

    try:
        answer = llm_chat(convo).strip()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    if not _question_ok(answer):
        try:
            answer = _repair_to_ru_question(answer, msg)
        except Exception:
            pass

    if not _question_ok(answer):
        answer = "Можешь привести конкретный пример из недавней ситуации?"

    db.session.add(StudentMessage(student_id=st.id, role="assistant", content=answer))
    db.session.commit()

    return jsonify({"ok": True, "answer": answer, "q_count": q_count + 1, "done": False})

@csrf.exempt
@app.post("/student/api/analyze")
def student_api_analyze():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return jsonify({"ok": False, "error": "no_student"}), 400

    key = f"st:{st.id}:analyze"
    if not rate_limit(key, limit=6, window_s=300):
        return jsonify({"ok": False, "error": "too_many_requests"}), 429

    msgs = StudentMessage.query.filter_by(student_id=st.id).order_by(StudentMessage.id.asc()).all()
    convo = [{"role": m.role, "content": m.content} for m in msgs]

    profile = {
        "full_name": st.full_name,
        "city": st.city,
        "college": st.college,
        "speciality": st.speciality,
        "start_year": st.start_year,
        "job_intent": st.job_intent,
        "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
        "region": st.region,
        "remote": bool(st.remote),
        "notify": bool(st.notify),
    }

    schema_hint = (
        "{"
        "\"personality_type\":\"(один из 16 типов)\","
        "\"personality_short\":\"коротко 1-2 предложения\","
        "\"soft_skills\":[{\"name\":\"...\",\"score\":0-100}],"
        "\"hard_skills\":[{\"name\":\"...\",\"score\":0-100}],"
        "\"top_roles\":[\"роль1\",\"роль2\",\"роль3\"],"
        "\"learning_plan\":[{\"skill\":\"...\",\"why\":\"...\",\"next_step\":\"...\"}]"
        "}"
    )

    prompt = [
        {"role": "system", "content": (
            "Ты анализатор профиля студента VECTOR AI.\n"
            "Верни ТОЛЬКО один валидный JSON-объект, без текста до/после.\n"
            "Ключи JSON — ТОЧНО как в схеме (ключи могут быть на латинице).\n"
            "ЗНАЧЕНИЯ — ТОЛЬКО по-русски (кириллица), без транслита и латиницы.\n"
            f"Схема:\n{schema_hint}\n"
            "Оцени score реалистично. Не выдумывай дипломы/опыт."
        )},
        {"role": "user", "content": "Onboarding profile:\n" + json.dumps(profile, ensure_ascii=False)},
        {"role": "user", "content": "Interview messages:\n" + json.dumps(convo, ensure_ascii=False)},
    ]

    try:
        raw = llm_chat(prompt).strip()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    analysis = safe_json_from_text(raw)

    if not analysis.get("personality_type"):
        try:
            repaired = _repair_to_ru_json(raw, schema_hint)
            analysis = safe_json_from_text(repaired)
        except Exception:
            pass

    if analysis.get("personality_type") and not _json_values_are_ru_only(analysis):
        try:
            repaired = _repair_to_ru_json(json.dumps(analysis, ensure_ascii=False), schema_hint)
            analysis = safe_json_from_text(repaired)
        except Exception:
            pass

    if not analysis.get("personality_type"):
        return jsonify({"ok": False, "error": "bad_analysis", "raw": raw}), 200

    StudentSkill.query.filter_by(student_id=st.id).delete()
    StudentAnalysis.query.filter_by(student_id=st.id).delete()
    db.session.commit()

    sa = StudentAnalysis(
        student_id=st.id,
        personality_type=analysis.get("personality_type", ""),
        personality_short=analysis.get("personality_short", ""),
        top_roles_json=json.dumps(analysis.get("top_roles", []), ensure_ascii=False),
        learning_plan_json=json.dumps(analysis.get("learning_plan", []), ensure_ascii=False),
    )
    db.session.add(sa)

    for x in (analysis.get("soft_skills") or []):
        name = (x.get("name") or "").strip()
        try:
            score = int(x.get("score") or 0)
        except Exception:
            score = 0
        if name:
            db.session.add(StudentSkill(student_id=st.id, kind="soft", name=name, score=max(0, min(score, 100))))

    for x in (analysis.get("hard_skills") or []):
        name = (x.get("name") or "").strip()
        try:
            score = int(x.get("score") or 0)
        except Exception:
            score = 0
        if name:
            db.session.add(StudentSkill(student_id=st.id, kind="hard", name=name, score=max(0, min(score, 100))))

    # --- сохраняем навыки/анализ ---
    db.session.commit()

    # =============================
    # ✅ HISTORY: SkillSnapshot (история навыков)
    # =============================
    try:
        snap_skills = []
        for x in (analysis.get("soft_skills") or []):
            n = (x.get("name") or "").strip()
            sc = int(x.get("score") or 0)
            if n:
                snap_skills.append({"name": n, "score": max(0, min(sc, 100)), "kind": "soft"})

        for x in (analysis.get("hard_skills") or []):
            n = (x.get("name") or "").strip()
            sc = int(x.get("score") or 0)
            if n:
                snap_skills.append({"name": n, "score": max(0, min(sc, 100)), "kind": "hard"})

        db.session.add(SkillSnapshot(
            student_id=st.id,
            personality_type=analysis.get("personality_type", ""),
            skills_json=json.dumps(snap_skills, ensure_ascii=False),
            note="после анализа"
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # =============================
    # ✅ HISTORY: MarketFitSnapshot (динамика соответствия рынку)
    # =============================
    try:
        # построим skill_set студента из анализа (быстро, без запросов к БД)
        student_skill_names = set()
        for it in (analysis.get("soft_skills") or []) + (analysis.get("hard_skills") or []):
            n = (it.get("name") or "").strip()
            if n:
                student_skill_names.add(norm_skill(n))
        student_skill_names = {x for x in student_skill_names if x}

        roles_for_market = (analysis.get("top_roles") or [])[:3]
        if not roles_for_market:
            roles_for_market = [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()][:3]

        for role in roles_for_market:
            try:
                gap = market_gap_for_role(role, student_skill_names, max_vac=20)
                mf = market_fit_percent_from_gap(gap)

                db.session.add(MarketFitSnapshot(
                    student_id=st.id,
                    role=role,
                    market_fit_percent=max(0, min(int(mf), 100)),
                    missing_json=json.dumps(gap.get("missing") or [], ensure_ascii=False),
                    have_json=json.dumps(gap.get("have") or [], ensure_ascii=False),
                    top_market_json=json.dumps(gap.get("top_market") or [], ensure_ascii=False),
                    note="после анализа"
                ))
            except Exception:
                continue

        db.session.commit()
    except Exception:
        db.session.rollback()
    # === NEW: сохраняем историю навыков + динамику соответствия рынку ===
    try:
        # 1) история навыков
        save_skill_snapshot(st.id, sa.personality_type, note="после анализа")

        # 2) динамика рынка по первой роли
        roles2 = analysis.get("top_roles") or [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()]
        role0 = (roles2[0] if roles2 else "Junior Developer")
        save_market_fit_snapshot(st.id, role0)
    except Exception:
        logging.exception("snapshot saving failed")
    return jsonify({"ok": True, "analysis": analysis})

@app.get("/student/result")
def student_result():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    sa = StudentAnalysis.query.filter_by(student_id=st.id).order_by(StudentAnalysis.id.desc()).first()
    if not sa:
        return redirect(url_for("student_interview"))

    analysis = {
        "personality_type": sa.personality_type,
        "personality_short": sa.personality_short,
        "top_roles": json.loads(sa.top_roles_json or "[]"),
        "learning_plan": json.loads(sa.learning_plan_json or "[]"),
        "soft_skills": [{"name": s.name, "score": s.score} for s in StudentSkill.query.filter_by(student_id=st.id, kind="soft").all()],
        "hard_skills": [{"name": s.name, "score": s.score} for s in StudentSkill.query.filter_by(student_id=st.id, kind="hard").all()],
    }

    profile = {
        "full_name": st.full_name,
        "city": st.city,
        "college": st.college,
        "speciality": st.speciality,
        "start_year": st.start_year,
        "job_intent": st.job_intent,
        "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
        "region": st.region,
        "remote": bool(st.remote),
        "notify": bool(st.notify),
    }

    return render_template("student/result.html", analysis=analysis, res=analysis, profile=profile)


# =============================
# MATCH HELPERS (единая формула + каноника навыков по hh_id)
# =============================
def compute_match_percent(vacancy_skills: set[str], student_skill_names: set[str]) -> int:
    if not vacancy_skills:
        return 0
    match_count = len(vacancy_skills & student_skill_names)
    return int(round((match_count / len(vacancy_skills)) * 100))


# ✅ NEW: merge skills HH + LLM (unique by norm_skill)
def merge_skills_unique(primary: list[str], extra: list[str], limit: int = 18) -> list[str]:
    out = []
    seen = set()
    for s in (primary or []) + (extra or []):
        if not isinstance(s, str):
            continue
        s2 = s.strip()
        if not s2:
            continue
        k = norm_skill(s2)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(s2)
        if limit and len(out) >= limit:
            break
    return out


# ✅ UPDATED: can save canonical skillset with overwrite option
def _save_canonical_skillset(hh_id: str, skills: list[str], overwrite: bool = True) -> list[str]:
    hh_id = str(hh_id or "").strip()

    cleaned = []
    for s in (skills or []):
        if isinstance(s, str):
            s2 = s.strip()
            if s2:
                cleaned.append(s2)

    row = VacancySkillSet.query.filter_by(hh_id=hh_id).first()

    # if exists and overwrite is False -> return existing
    if row and not overwrite:
        try:
            return json.loads(row.skills_json or "[]")
        except Exception:
            return []

    if not row:
        row = VacancySkillSet(
            hh_id=hh_id,
            skills_json=json.dumps(cleaned, ensure_ascii=False),
            updated_at=datetime.utcnow()
        )
        db.session.add(row)
    else:
        row.skills_json = json.dumps(cleaned, ensure_ascii=False)
        row.updated_at = datetime.utcnow()

    db.session.commit()
    return cleaned


# ✅ NEW: create canonical ONCE using HH key_skills + extra(LMM) if canonical doesn't exist
def ensure_canonical_skillset_once(hh_id: str, extra_skills: list[str] | None = None) -> list[str]:
    hh_id = str(hh_id or "").strip()
    if not hh_id:
        return []

    row = VacancySkillSet.query.filter_by(hh_id=hh_id).first()
    if row:
        try:
            return json.loads(row.skills_json or "[]")
        except Exception:
            return []

    # get HH key_skills
    hh_skills = []
    try:
        vac = hh_get_vacancy(hh_id)
        ks = vac.get("key_skills") or []
        hh_skills = [x.get("name") for x in ks if isinstance(x, dict) and x.get("name")]
    except Exception:
        hh_skills = []

    merged = merge_skills_unique(hh_skills, extra_skills or [], limit=18)

    # create canonical
    return _save_canonical_skillset(hh_id, merged, overwrite=True)


def get_canonical_vacancy_skills(hh_id: str) -> list[str]:
    """
    ЕДИНЫЙ источник навыков для hh_id:
    1) если уже есть VacancySkillSet -> берём его (НЕ МЕНЯЕМ)
    2) иначе, если есть свежий EmployerVacancyAnalysis -> создаём канонику ОДИН РАЗ из HH+LLM
    3) иначе создаём канонику ОДИН РАЗ только из HH key_skills
    """
    hh_id = str(hh_id or "").strip()
    if not hh_id:
        return []

    row = VacancySkillSet.query.filter_by(hh_id=hh_id).first()
    if row:
        try:
            return json.loads(row.skills_json or "[]")
        except Exception:
            return []

    eva = (EmployerVacancyAnalysis.query
           .filter_by(hh_id=hh_id)
           .order_by(EmployerVacancyAnalysis.id.desc())
           .first())
    if eva:
        try:
            llm_skills = json.loads(eva.skills_json or "[]")
        except Exception:
            llm_skills = []
        return ensure_canonical_skillset_once(hh_id, llm_skills)

    return ensure_canonical_skillset_once(hh_id, extra_skills=[])


def build_skill_set(skills: list[str]) -> set[str]:
    out = set()
    for s in (skills or []):
        if isinstance(s, str):
            x = norm_skill(s)
            if x:
                out.add(x)
    return out


def canonical_skill_set(hh_id: str) -> set[str]:
    return build_skill_set(get_canonical_vacancy_skills(hh_id))


# =============================
# STUDENT: vacancies list
# =============================
@app.get("/student/vacancies")
def student_vacancies():
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    sa = StudentAnalysis.query.filter_by(student_id=st.id).order_by(StudentAnalysis.id.desc()).first()

    roles = []
    if sa:
        roles = json.loads(sa.top_roles_json or "[]")
    if not roles:
        roles = [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()] or ["Junior Developer"]

    q = (request.args.get("q") or roles[0]).strip()
    page = max(0, int(request.args.get("page", 0) or 0))
    per_page = 20

    try:
        hh = hh_search_vacancies(q, area=HH_AREA_KZ, per_page=per_page, page=page)
        items = hh.get("items", [])
        found = int(hh.get("found", 0) or 0)
        pages = (found // per_page) + (1 if found % per_page else 0)
    except Exception:
        items, found, pages = [], 0, 0

    sskills = StudentSkill.query.filter_by(student_id=st.id).all()
    student_skill_names = set(norm_skill(s.name) for s in sskills if s.name)
    student_skill_names = {x for x in student_skill_names if x}

    match_map = {}
    for v in items:
        hh_id = str(v.get("id") or "")
        if not hh_id:
            continue
        vacancy_skills = canonical_skill_set(hh_id)
        percent = compute_match_percent(vacancy_skills, student_skill_names) if vacancy_skills else 0
        match_map[hh_id] = percent

    items.sort(key=lambda x: match_map.get(str(x.get("id") or ""), 0), reverse=True)

    return render_template("student/vacancies.html", items=items, q=q, roles=roles, page=page, pages=pages, match_map=match_map)


@app.post("/student/vacancy/<string:hh_id>/apply")
@login_required
def student_apply_vacancy(hh_id):
    guard = require_role("student")
    if guard:
        return guard

    st = Student.query.filter_by(user_id=current_user.id).first()
    if not st:
        return redirect(url_for("student_onboarding"))

    hh_url = (request.form.get("hh_url") or "").strip()
    vac_name = (request.form.get("vacancy_name") or "").strip()
    emp_name = (request.form.get("employer_name") or "").strip()

    if not hh_url:
        flash("Не удалось получить ссылку на вакансию.", "error")
        return redirect(url_for("student_vacancy_detail", hh_id=hh_id))

    key = f"st:{st.id}:apply"
    if not rate_limit(key, limit=15, window_s=60):
        flash("Слишком много попыток. Подожди минуту.", "error")
        return redirect(url_for("student_vacancy_detail", hh_id=hh_id))

    row = VacancyApplication.query.filter_by(student_id=st.id, hh_id=str(hh_id)).first()
    if not row:
        row = VacancyApplication(
            student_id=st.id,
            hh_id=str(hh_id),
            hh_url=hh_url,
            vacancy_name=vac_name[:255],
            employer_name=emp_name[:255],
            status="sent",
        )
        db.session.add(row)
        db.session.commit()

    return redirect(hh_url)


@app.get("/student/vacancy/<string:hh_id>")
def student_vacancy_detail(hh_id):
    guard = require_role("student")
    if guard:
        return guard

    vac = hh_get_vacancy(hh_id)

    st = Student.query.filter_by(user_id=current_user.id).first()
    sa = StudentAnalysis.query.filter_by(student_id=st.id).order_by(StudentAnalysis.id.desc()).first()

    analysis = {}
    if sa:
        analysis = {
            "personality_type": sa.personality_type,
            "personality_short": sa.personality_short,
            "top_roles": json.loads(sa.top_roles_json or "[]"),
        }

    skills = StudentSkill.query.filter_by(student_id=st.id).all()
    student_skill_names = set(norm_skill(s.name) for s in skills if s.name)
    student_skill_names = {x for x in student_skill_names if x}

    vacancy_skills = canonical_skill_set(hh_id)
    match_source = "canonical"

    match_percent = compute_match_percent(vacancy_skills, student_skill_names) if vacancy_skills else 0
    matched = sorted(list(vacancy_skills & student_skill_names))[:30]
    missing = sorted(list(vacancy_skills - student_skill_names))[:30]

    system = (
        "Ты карьерный консультант.\n"
        "Сделай 3–6 коротких буллетов: почему вакансия подходит студенту.\n"
        "Учитывай personality_type, top_roles и навыки.\n"
        "Можно писать названия технологий латиницей (React, TypeScript, Git и т.п.).\n"
        "Пиши простыми словами.\n"
        "Только буллеты."
    )

    skill_pack = [{"name": s.name, "score": s.score, "kind": s.kind} for s in skills]

    user_payload = {
        "student_profile": {
            "full_name": st.full_name,
            "city": st.city,
            "speciality": st.speciality,
            "roles": [x.strip() for x in (st.roles_csv or "").split(",") if x.strip()],
            "remote": bool(st.remote),
        },
        "student_analysis": analysis,
        "student_skills": skill_pack,
        "vacancy": {
            "name": vac.get("name"),
            "area": (vac.get("area") or {}).get("name"),
            "employer": (vac.get("employer") or {}).get("name"),
            "key_skills": vac.get("key_skills", []),
            "snippet": vac.get("snippet"),
            "description": strip_html((vac.get("description") or ""))[:2500],
        },
    }

    try:
        explain = llm_chat([
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ]).strip()
        if not explain:
            raise ValueError("empty")
    except Exception:
        explain = (
            "• Совпадает направление и тип задач.\n"
            "• Подходит по сильным навыкам из профиля.\n"
            "• Есть понятные шаги роста по недостающим навыкам.\n"
            "• Формат работы можно подстроить под студента."
        )

    return render_template(
        "student/vacancy_detail.html",
        vac=vac,
        explain=explain,
        match_percent=match_percent,
        match_source=match_source,
        matched=matched,
        missing=missing
    )


# --- обновлённая эвристика, возвращает категории + теги + note (фолбэк для LLM) ---
def heuristic_inclusivity(text: str) -> dict:
    """
    Возвращает словарь:
    {
      "categories": {
         "visually_impaired": bool,
         "hearing_impaired": bool,
         "mobility_access": bool,
         "neurodiversity_friendly": bool,
         "junior_friendly": bool,
         "remote_possible": bool,
         "flexible_schedule": bool
      },
      "tags": [...],
      "note": "короткое объяснение",
    }
    """
    t = (text or "").lower()
    cats = {
        "visually_impaired": False,
        "hearing_impaired": False,
        "mobility_access": False,
        "neurodiversity_friendly": False,
        "junior_friendly": False,
        "remote_possible": False,
        "flexible_schedule": False,
    }
    tags = set()

    # Junior / no experience
    if any(k in t for k in ["без опыта", "стажировка", "обучение", "готовность обучать", "open to juniors", "junior"]):
        cats["junior_friendly"] = True
        tags.add("novice_friendly")

    # Remote
    if any(k in t for k in ["удал", "remote", "work from home", "telecommute"]):
        cats["remote_possible"] = True
        tags.add("remote")

    # Flexible schedule / part-time
    if any(k in t for k in ["гибкий график", "частичная занятость", "flexible", "part-time", "частичная"]):
        cats["flexible_schedule"] = True
        tags.add("flexible_hours")

    # Mobility / accessibility mentions
    if any(k in t for k in ["доступн", "адапт", "пандус", "wheelchair", "безбарьер", "безбарьерная"]):
        cats["mobility_access"] = True
        tags.add("accessibility")

    # Visual / bigger font, screen reader hints
    if any(k in t for k in ["шрифт", "контраст", "screen reader", "скринридер", "размер шрифта", "тактильн"]):
        cats["visually_impaired"] = True
        tags.add("visually_friendly")

    # Hearing: subtitles, silent tasks, нет звонков
    if any(k in t for k in ["субтитры", "без звонков", "без телефонных", "без звонков", "caption", "subtitles", "видео с субтитрами"]):
        cats["hearing_impaired"] = True
        tags.add("hearing_friendly")

    # Neurodiversity (explicit or words like predictable, structured)
    if any(k in t for k in ["нейро", "нейродивер", "структур", "предсказуем", "clear instructions", "mentorship"]):
        cats["neurodiversity_friendly"] = True
        tags.add("neurodiversity")

    # Negative/discriminatory flags
    risk_flags = []
    NEGATIVE_KEYWORDS = ["только для мужчин", "только для женщин", "без инвалидов", "age limit", "требования: возраст", "максимальный возраст"]
    if any(k in t for k in NEGATIVE_KEYWORDS):
        risk_flags.append("possible_discrimination")

    note_parts = []
    if cats["remote_possible"]:
        note_parts.append("Вакансия допускает удалённую работу")
    if cats["junior_friendly"]:
        note_parts.append("Подходит для начинающих / без опыта")
    if cats["flexible_schedule"]:
        note_parts.append("Гибкий график")
    if cats["mobility_access"]:
        note_parts.append("Обратил внимание на доступность для маломобильных")
    if cats["visually_impaired"]:
        note_parts.append("Есть маркеры, полезные для слабовидящих (контраст/шрифт)")
    if cats["hearing_impaired"]:
        note_parts.append("Поддержка для слабослышащих (субтитры/без звонков)")
    if cats["neurodiversity_friendly"]:
        note_parts.append("Поддержка нейродиверситета / структурированность задач")

    note = "; ".join(note_parts) if note_parts else "Информации об инклюзивности немного — требуется дополнительный анализ."

    return {"categories": cats, "tags": sorted(tags), "note": note, "risk_flags": risk_flags}


# =============================
# EMPLOYER AREA
# =============================
@app.get("/employer")
def employer_dashboard():
    guard = require_role("employer")
    if guard:
        return guard

    emp = Employer.query.filter_by(user_id=current_user.id).first()
    analyses = EmployerVacancyAnalysis.query.filter_by(employer_id=emp.id).order_by(EmployerVacancyAnalysis.id.desc()).all()
    return render_template("employer/index.html", employer=emp, analyses=analyses)

@csrf.exempt
@app.post("/student/api/inclusive/search")
def student_inclusive_search():
    try:
        # require_role: если возвращает ненулевое значение — это ответ (redirect / jsonify / abort)
        guard = require_role("student")
        if guard is not None:
            return guard

        data = request.get_json(silent=True) or {}

        # входные параметры с защитой типов
        query = (data.get("query") or "").strip()
        all_roles = bool(data.get("all_roles", False))
        try:
            llm_depth = max(0, min(50, int(data.get("llm_depth", 10))))
        except Exception:
            llm_depth = 10

        # если пустой запрос — ищем по всем ролям
        if not query:
            all_roles = True

        # ожидаемые категории (константа)
        EXPECTED_CATS = {
            "visually_impaired",
            "hearing_impaired",
            "mobility_access",
            "neurodiversity_friendly",
            "junior_friendly",
            "remote_possible",
            "flexible_schedule"
        }

        # required_categories: ожидаем dict {cat: bool}
        required_categories_in = data.get("required_categories") or {}
        if isinstance(required_categories_in, dict):
            required_categories = {
                k: bool(v)
                for k, v in required_categories_in.items()
                if k in EXPECTED_CATS
            }
        else:
            required_categories = {}

        match_logic = (data.get("match_logic") or "and").lower()
        if match_logic not in ("and", "or"):
            match_logic = "and"

        DEFAULT_ROLES = [
            "Backend Developer","Frontend Developer","QA","DevOps",
            "Маркетолог","Бухгалтер","HR","Менеджер по продажам",
            "Инженер","Учитель","Водитель","Медицинская сестра"
        ]

        search_roles = DEFAULT_ROLES if (all_roles or not query) else [query]

        # ===== СБОР ВАКАНСИЙ (по ролям) =====
        collected = {}
        for role in search_roles:
            try:
                hh = hh_search_vacancies(role, area=HH_AREA_KZ, per_page=20, page=0)
            except Exception:
                logging.exception("hh_search_vacancies failed for role=%s", role)
                continue

            for v in (hh.get("items") or []):
                hh_id = str(v.get("id") or "")
                if hh_id:
                    # держим последний встретившийся объект (можно изменить по логике)
                    collected.setdefault(hh_id, v)

        if not collected:
            return jsonify({
                "ok": True,
                "searched_roles": search_roles,
                "items": []
            })

        # ===== НАВЫКИ СТУДЕНТА =====
        try:
            st = Student.query.filter_by(user_id=current_user.id).first()
            sskills = StudentSkill.query.filter_by(student_id=st.id).all() if st else []
        except Exception:
            logging.exception("failed to load student skills")
            sskills = []

        student_skill_names = set(
            norm_skill(s.name)
            for s in sskills
            if getattr(s, "name", None)
        )

        enriched = []

        # ===== КЭШ ДЛЯ canonical_skill_set в пределах запроса =====
        @lru_cache(maxsize=1024)
        def _cached_canonical_skill_set(hh_id):
            try:
                return canonical_skill_set(hh_id)
            except Exception:
                logging.exception("canonical_skill_set failed for %s", hh_id)
                return None

        # помогаем получать полные данные вакансии + вычислить процент сопадения
        def process_vacancy_pair(hh_id, v):
            # v — минимальные данные из поиска; попробуем получить полную вакансию,
            # но не критично если fails (fallback использует v)
            try:
                vac = hh_get_vacancy(hh_id)
            except Exception:
                vac = v

            title = str(vac.get("name") or "")
            employer = str((vac.get("employer") or {}).get("name") or "")

            # snippet safe
            snippet = v.get("snippet") or {}
            if isinstance(snippet, dict):
                snippet_text = (
                    str(snippet.get("requirement") or "") + " " +
                    str(snippet.get("responsibility") or "")
                )
            else:
                snippet_text = str(snippet)

            # key skills
            keyskills_raw = v.get("key_skills") or []
            keyskills = []
            for k in keyskills_raw:
                if isinstance(k, dict):
                    keyskills.append(str(k.get("name") or ""))
                else:
                    keyskills.append(str(k))

            text_for_soft = " ".join([
                title,
                " ".join(keyskills),
                snippet_text,
                employer
            ]).lower()

            # inclusive heuristics (простая и быстрая)
            categories = {
                "visually_impaired": "доступн" in text_for_soft,
                "hearing_impaired": "субтитр" in text_for_soft,
                "mobility_access": "пандус" in text_for_soft,
                "neurodiversity_friendly": "нейро" in text_for_soft,
                "junior_friendly": "без опыта" in text_for_soft,
                "remote_possible": "удален" in text_for_soft or "remote" in text_for_soft,
                "flexible_schedule": "гибк" in text_for_soft
            }

            # compute percent (через кэш)
            try:
                vacancy_skills = _cached_canonical_skill_set(hh_id)
                percent = compute_match_percent(vacancy_skills, student_skill_names) if vacancy_skills else 0
            except Exception:
                logging.exception("compute_match_percent failed for %s", hh_id)
                percent = 0

            # фильтр required_categories
            if required_categories:
                requested = [k for k, v in required_categories.items() if v]
                if requested:
                    if match_logic == "and":
                        if not all(categories.get(k) for k in requested):
                            return None
                    else:
                        if not any(categories.get(k) for k in requested):
                            return None

            true_count = sum(1 for val in categories.values() if val)

            return {
                "id": hh_id,
                "name": title,
                "employer": employer,
                "url": vac.get("alternate_url"),
                "percent": int(percent),
                "categories": categories,
                "category_true_count": true_count
            }

        # ===== Параллельная обработка (ограничение по размеру) =====
        # Берём максимум N элементов для обработки, чтобы не сделать сотни сетевых вызовов.
        MAX_PROCESS = max(50, min(200, len(collected)))  # гибко: 50..200
        items_to_process = list(collected.items())[:MAX_PROCESS]

        with ThreadPoolExecutor(max_workers=min(12, len(items_to_process) or 1)) as ex:
            futures = {
                ex.submit(process_vacancy_pair, hh_id, v): hh_id
                for hh_id, v in items_to_process
            }
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    if res:
                        enriched.append(res)
                except Exception:
                    logging.exception("error processing vacancy %s", futures.get(fut))

        # ===== FALLBACK: если фильтр всё удалил или не было enriched =====
        if not enriched:
            for hh_id, v in list(collected.items())[:20]:
                enriched.append({
                    "id": hh_id,
                    "name": str(v.get("name") or ""),
                    "employer": str((v.get("employer") or {}).get("name") or ""),
                    "url": v.get("alternate_url"),
                    "percent": 0,
                    "categories": {},
                    "category_true_count": 0
                })

        # ===== СОРТИРОВКА =====
        enriched.sort(
            key=lambda x: (x.get("category_true_count", 0), x.get("percent", 0)),
            reverse=True
        )

        return jsonify({
            "ok": True,
            "searched_roles": search_roles,
            "items": enriched
        })

    except Exception as e:
        logging.exception("internal error in inclusive search")
        return jsonify({
            "ok": False,
            "error": "internal_error",
            "details": str(e)
        }), 200

@app.get("/student/inclusive")
def student_inclusive():
    guard = require_role("student")
    if guard:
        return guard

    return render_template("student/inclusive.html")


@app.get("/student/site2")
def student_site2():
    guard = require_role("student")
    if guard:
        return guard

    target = os.getenv("INCLUSIVE_URL", "http://127.0.0.1:3000")
    return redirect(target)

@csrf.exempt
@app.post("/employer/api/analyze")
def employer_analyze():
    guard = require_role("employer")
    if guard:
        return guard

    emp = Employer.query.filter_by(user_id=current_user.id).first()

    data = request.get_json() or {}
    hh_url = (data.get("hh_url") or "").strip()
    if not hh_url:
        return jsonify({"ok": False, "error": "no_url"}), 400

    match = re.search(r"/vacancy/(\d+)", hh_url)
    if not match:
        return jsonify({"ok": False, "error": "invalid_link"}), 400

    hh_id = match.group(1)

    try:
        vacancy = hh_get_vacancy(hh_id)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    system_prompt = (
        "Верни ТОЛЬКО JSON.\n"
        "Выдели 8-18 ключевых навыков из вакансии.\n"
        "Значения пиши по-русски, технологии можно латиницей.\n"
        "Схема:\n"
        "{"
        "\"skills\": [\"навык1\",\"навык2\",\"навык3\"]"
        "}"
    )

    user_payload = {
        "title": vacancy.get("name"),
        "description": strip_html(vacancy.get("description") or "")[:5000],
        "key_skills": vacancy.get("key_skills", []),
    }

    llm_skills = []
    try:
        raw = llm_chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ])
        parsed = safe_json_from_text(raw)
        llm_skills = parsed.get("skills", []) or []
    except Exception:
        llm_skills = []

    # ✅ Каноника: создаём ОДИН РАЗ HH+LLM, дальше не меняем
    canonical_skills = ensure_canonical_skillset_once(hh_id, llm_skills)

    eva = EmployerVacancyAnalysis(
        employer_id=emp.id,
        title=vacancy.get("name") or "",
        hh_id=hh_id,
        # в анализ сохраняем то же самое, что в канонике
        skills_json=json.dumps(canonical_skills, ensure_ascii=False),
    )
    db.session.add(eva)
    db.session.commit()

    return jsonify({"ok": True, "analysis_id": eva.id})


@app.get("/employer/vacancy/<int:analysis_id>")
def employer_vacancy_page(analysis_id: int):
    guard = require_role("employer")
    if guard:
        return guard

    emp = Employer.query.filter_by(user_id=current_user.id).first()
    eva = EmployerVacancyAnalysis.query.get(analysis_id)
    if not eva or eva.employer_id != emp.id:
        abort(404)

    skills = json.loads(eva.skills_json or "[]")
    return render_template("employer/result.html", analysis=eva, skills=skills)


@csrf.exempt
@app.get("/employer/api/match")
def employer_match_students():
    guard = require_role("employer")
    if guard:
        return guard

    emp = Employer.query.filter_by(user_id=current_user.id).first()

    analysis_id = request.args.get("analysis_id", type=int)
    if not analysis_id:
        return jsonify({"ok": False, "error": "no_analysis_id"}), 400

    eva = EmployerVacancyAnalysis.query.get(analysis_id)
    if not eva or eva.employer_id != emp.id:
        return jsonify({"ok": False, "error": "not_found"}), 404

    min_percent = request.args.get("min", default=0, type=int)
    only_fav = request.args.get("fav") == "1"
    status_filter = (request.args.get("status") or "").strip()
    city_filter = (request.args.get("city") or "").strip().lower()
    remote_filter = request.args.get("remote")
    page = max(0, int(request.args.get("page", 0) or 0))
    per_page = min(50, max(10, int(request.args.get("per_page", 20) or 20)))

    vacancy_skills = canonical_skill_set(eva.hh_id)

    students_q = db.session.query(Student).join(StudentAnalysis, StudentAnalysis.student_id == Student.id)
    if city_filter:
        students_q = students_q.filter(db.func.lower(Student.city) == city_filter)
    if remote_filter in ("0", "1"):
        students_q = students_q.filter(Student.remote == (remote_filter == "1"))

    students = students_q.all()

    out = []
    for st in students:
        sskills = StudentSkill.query.filter_by(student_id=st.id).all()
        student_skill_names = set(norm_skill(s.name) for s in sskills if s.name)
        student_skill_names = {x for x in student_skill_names if x}

        percent = compute_match_percent(vacancy_skills, student_skill_names)
        if percent < max(0, min(min_percent, 100)):
            continue

        cs = CandidateStatus.query.filter_by(vacancy_analysis_id=eva.id, student_id=st.id).first()
        if not cs:
            cs = CandidateStatus(vacancy_analysis_id=eva.id, student_id=st.id, percent=percent)
            db.session.add(cs)
            db.session.commit()
        else:
            if cs.percent != percent:
                cs.percent = percent
                cs.updated_at = datetime.utcnow()
                db.session.commit()

        if only_fav and not cs.favorite:
            continue
        if status_filter and cs.status != status_filter:
            continue

        out.append({
            "student_id": st.id,
            "name": st.full_name or f"Студент #{st.id}",
            "city": st.city or "",
            "remote": bool(st.remote),
            "percent": percent,
            "favorite": bool(cs.favorite),
            "status": cs.status,
            "note": cs.note or "",
        })

    out.sort(key=lambda x: (x["favorite"], x["percent"]), reverse=True)
    total = len(out)
    start = page * per_page
    out_page = out[start:start + per_page]
    pages = (total // per_page) + (1 if total % per_page else 0)

    return jsonify({"ok": True, "candidates": out_page, "total": total, "page": page, "pages": pages})


@csrf.exempt
@app.post("/employer/api/candidate/favorite")
def employer_candidate_favorite():
    guard = require_role("employer")
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    analysis_id = int(data.get("analysis_id") or 0)
    student_id = int(data.get("student_id") or 0)
    fav = bool(data.get("favorite"))

    if not analysis_id or not student_id:
        return jsonify({"ok": False, "error": "bad_args"}), 400

    emp = Employer.query.filter_by(user_id=current_user.id).first()
    eva = EmployerVacancyAnalysis.query.get(analysis_id)
    if not eva or eva.employer_id != emp.id:
        return jsonify({"ok": False, "error": "not_found"}), 404

    cs = CandidateStatus.query.filter_by(vacancy_analysis_id=analysis_id, student_id=student_id).first()
    if not cs:
        cs = CandidateStatus(vacancy_analysis_id=analysis_id, student_id=student_id, percent=0)
        db.session.add(cs)

    cs.favorite = fav
    cs.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"ok": True, "favorite": cs.favorite})


@csrf.exempt
@app.post("/employer/api/candidate/status")
def employer_candidate_status():
    guard = require_role("employer")
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    analysis_id = int(data.get("analysis_id") or 0)
    student_id = int(data.get("student_id") or 0)
    status = (data.get("status") or "new").strip()
    note = (data.get("note") or "").strip()

    allowed = {"new", "shortlist", "interview", "rejected", "hired"}
    if status not in allowed:
        return jsonify({"ok": False, "error": "bad_status"}), 400
    if not analysis_id or not student_id:
        return jsonify({"ok": False, "error": "bad_args"}), 400

    emp = Employer.query.filter_by(user_id=current_user.id).first()
    eva = EmployerVacancyAnalysis.query.get(analysis_id)
    if not eva or eva.employer_id != emp.id:
        return jsonify({"ok": False, "error": "not_found"}), 404

    cs = CandidateStatus.query.filter_by(vacancy_analysis_id=analysis_id, student_id=student_id).first()
    if not cs:
        cs = CandidateStatus(vacancy_analysis_id=analysis_id, student_id=student_id, percent=0)
        db.session.add(cs)

    cs.status = status
    cs.note = note[:2000]
    cs.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"ok": True, "status": cs.status, "note": cs.note})


@csrf.exempt
@app.post("/employer/api/candidate/note")
def employer_candidate_note():
    guard = require_role("employer")
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    analysis_id = int(data.get("analysis_id") or 0)
    student_id = int(data.get("student_id") or 0)
    note = (data.get("note") or "").strip()

    if not analysis_id or not student_id:
        return jsonify({"ok": False, "error": "bad_args"}), 400

    emp = Employer.query.filter_by(user_id=current_user.id).first()
    eva = EmployerVacancyAnalysis.query.get(analysis_id)
    if not eva or eva.employer_id != emp.id:
        return jsonify({"ok": False, "error": "not_found"}), 404

    cs = CandidateStatus.query.filter_by(vacancy_analysis_id=analysis_id, student_id=student_id).first()
    if not cs:
        cs = CandidateStatus(vacancy_analysis_id=analysis_id, student_id=student_id, percent=0)
        db.session.add(cs)

    cs.note = note[:2000]
    cs.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"ok": True, "note": cs.note})



@csrf.exempt
@app.get("/employer/api/candidate/details")
def employer_candidate_details():
    guard = require_role("employer")
    if guard:
        return guard

    try:
        analysis_id = request.args.get("analysis_id", type=int)
        student_id = request.args.get("student_id", type=int)

        if not analysis_id or not student_id:
            return jsonify({"ok": False, "error": "bad_args"}), 400

        # Проверяем работодателя
        emp = Employer.query.filter_by(user_id=current_user.id).first()
        eva = EmployerVacancyAnalysis.query.get(analysis_id)

        if not emp or not eva or eva.employer_id != emp.id:
            return jsonify({"ok": False, "error": "not_found"}), 404

        # Загружаем студента
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"ok": False, "error": "student_not_found"}), 404

        # Навыки студента
        student_skills_rows = StudentSkill.query.filter_by(student_id=student.id).all()
        student_skill_set = set(
            (s.name or "").strip().lower()
            for s in student_skills_rows
            if s.name
        )

        # Навыки вакансии
        vacancy_list = get_canonical_vacancy_skills(eva.hh_id) or []
        vacancy_skill_set = set(
            (x or "").strip().lower()
            for x in vacancy_list
            if x
        )

        # Совпадения
        matched = sorted(list(vacancy_skill_set & student_skill_set))
        missing = sorted(list(vacancy_skill_set - student_skill_set))

        # Процент совпадения
        percent = 0
        if vacancy_skill_set:
            percent = int(round(len(matched) / len(vacancy_skill_set) * 100))

        # Статус кандидата
        cs = CandidateStatus.query.filter_by(
            vacancy_analysis_id=analysis_id,
            student_id=student.id
        ).first()

        status = cs.status if cs else "new"
        note = cs.note if cs else ""
        favorite = bool(cs.favorite) if cs else False

        # Personality (если есть)
        sa = StudentAnalysis.query.filter_by(
            student_id=student.id
        ).order_by(StudentAnalysis.id.desc()).first()

        personality = sa.personality_type if sa else ""
        personality_short = sa.personality_short if sa else ""

        # Финальный ответ
        return jsonify({
            "ok": True,
            "data": {
                "student": {
                    "id": student.id,
                    "name": student.full_name or f"Студент #{student.id}",
                    "city": student.city or "",
                    "remote": bool(getattr(student, "remote", False)),
                    "college": getattr(student, "college", "") or "",
                    "speciality": getattr(student, "speciality", "") or "",
                },
                "percent": percent,
                "matched": matched,
                "missing": missing,
                "status": status,
                "note": note,
                "favorite": favorite,
                "personality": personality,
                "personality_short": personality_short,
            }
        })

    except Exception:
        return jsonify({"ok": False, "error": "internal_error"}), 500

# =============================
# API: diploma-analysis / market-analytics / risk-forecast
# =============================
@csrf.exempt
@app.route("/api/diploma-analysis", methods=["POST"])
def diploma_analysis():
    data = request.get_json() or {}
    institution = (data.get("institution") or "").strip()
    profession = (data.get("profession") or "").strip() or "специалист"

    try:
        hh = hh_search_vacancies(profession, area=HH_AREA_KZ, per_page=30, page=0)
        vacancies = hh.get("items", [])
    except Exception:
        vacancies = []

    skill_counter = Counter()
    for v in vacancies:
        for skill in v.get("key_skills", []) or []:
            name = (skill.get("name") or "").lower().strip()
            if name:
                skill_counter[name] += 1

    if not skill_counter:
        skill_counter = Counter({
            "коммуникация": 5,
            "анализ данных": 4,
            "работа в команде": 6,
            "базовые технические навыки": 5
        })

    total_weight = sum(skill_counter.values())

    try:
        program_prompt = [
            {"role": "system", "content": (
                "Пиши только по-русски. Запрещены латиница и иероглифы.\n"
                "Сгенерируй типовые ключевые навыки, которые изучаются по данной профессии.\n"
                "Верни JSON: {\"skills\": [\"skill1\",\"skill2\",...]}\n"
                "Никакого текста до/после."
            )},
            {"role": "user", "content": f"Учебное заведение: {institution}. Профессия: {profession}"}
        ]
        raw = llm_chat(program_prompt)
        parsed = safe_json_from_text(raw)
        program_skills = set(
            s.strip().lower()
            for s in parsed.get("skills", [])
            if isinstance(s, str)
        )
    except Exception:
        program_skills = set()

    if not program_skills:
        program_skills = {"коммуникация", "работа в команде", "базовые технические навыки"}

    matched_weight = sum(
        count for skill, count in skill_counter.items()
        if skill in program_skills
    )

    percent = 0
    if total_weight > 0:
        percent = round((matched_weight / total_weight) * 100)

    percent = max(20, min(percent, 95))

    try:
        explanation = llm_chat([
            {"role": "system", "content": (
                "Пиши только по-русски. Запрещены латиница и иероглифы.\n"
                "Кратко объясни соответствие подготовки рынку труда. 2-3 предложения."
            )},
            {"role": "user", "content": f"Профессия: {profession}. Процент: {percent}%."}
        ]).strip()
        if not _is_ru_only(explanation):
            explanation = f"Подготовка по направлению «{profession}» демонстрирует {percent}% соответствия рынку труда."
    except Exception:
        explanation = f"Подготовка по направлению «{profession}» демонстрирует {percent}% соответствия рынку труда."

    return jsonify({"percent": percent, "explanation": explanation})


@csrf.exempt
@app.route("/api/market-analytics", methods=["GET", "POST"])
def market_analytics():
    payload = {}
    try:
        if request.method == "POST":
            payload = request.get_json(force=True) or {}
    except Exception:
        payload = {}

    roles = payload.get("roles") or [
        "Backend Developer",
        "Frontend Developer",
        "Медицинская сестра",
        "Инженер строитель",
        "Менеджер по продажам"
    ]

    results = []
    for role in roles:
        try:
            hh = hh_search_vacancies(role, area=HH_AREA_KZ, per_page=1, page=0)
            found = hh.get("found", 0)
        except Exception:
            found = 0

        if found >= 1000:
            heat = "high"
        elif found >= 500:
            heat = "medium"
        elif found > 0:
            heat = "low"
        else:
            heat = "none"

        results.append({"role": role, "found": int(found), "heat": heat})

    return jsonify({"results": results})


@csrf.exempt
@app.route("/api/risk-forecast", methods=["POST"])
def risk_forecast():
    data = request.get_json(silent=True) or {}
    profession = (data.get("profession") or "").strip()
    if not profession:
        return jsonify({"error": "empty_profession"}), 400

    schema_hint = (
        "{"
        "\"demand\":\"высокий|средний|низкий\","
        "\"competition\":\"растёт|стабильная|снижается\","
        "\"automation\":\"низкая|умеренная|высокая\","
        "\"risk_score\":0-100,"
        "\"summary\":\"краткий аналитический вывод\""
        "}"
    )

    prompt = [
        {"role": "system", "content": (
            "Ты аналитическая система рынка труда.\n"
            "Верни ТОЛЬКО один валидный JSON.\n"
            "Ключи JSON — как в схеме.\n"
            "Значения — ТОЛЬКО по-русски (кириллица), без транслита и латиницы.\n"
            f"Схема:\n{schema_hint}\n"
            "Никакого текста до и после JSON."
        )},
        {"role": "user", "content": f"Проанализируй профессию: {profession}"}
    ]

    try:
        raw = llm_chat(prompt).strip()
    except Exception as e:
        return jsonify({"error": "llm_failed", "details": str(e)}), 200

    result = safe_json_from_text(raw)

    if not result.get("demand"):
        try:
            repaired_raw = _repair_to_ru_json(raw, schema_hint)
            result = safe_json_from_text(repaired_raw)
        except Exception:
            pass

    if result.get("demand") and not _json_values_are_ru_only(result):
        try:
            repaired_raw = _repair_to_ru_json(json.dumps(result, ensure_ascii=False), schema_hint)
            result = safe_json_from_text(repaired_raw)
        except Exception:
            pass

    if not result.get("demand"):
        return jsonify({
            "demand": "средний",
            "competition": "стабильная",
            "automation": "умеренная",
            "risk_score": 50,
            "summary": f"Для профессии «{profession}» требуется дополнительный анализ. Данные модели временно недоступны."
        })

    try:
        result["risk_score"] = int(result.get("risk_score", 50))
        result["risk_score"] = max(0, min(result["risk_score"], 100))
    except Exception:
        result["risk_score"] = 50

    return jsonify(result)

@csrf.exempt
@app.get("/api/analytics/summary")
def analytics_summary():
    guard = require_any_role("admin", "hr")
    if guard:
        return guard

    students = Student.query.all()
    total = len(students) or 0

    scores = []
    for st in students:
        update_readiness_for_student(st)  # обновим флаги
        scores.append(readiness_score(st))
    db.session.commit()

    avg_score = int(round(sum(scores) / (len(scores) or 1)))

    low = []
    for st in students:
        low.append({
            "id": st.id,
            "name": st.full_name or f"Студент #{st.id}",
            "city": st.city or "",
            "score": readiness_score(st),
        })
    low.sort(key=lambda x: x["score"])
    low = low[:10]

    return jsonify({
        "ok": True,
        "students_total": total,
        "avg_readiness_score": avg_score,
        "low_readiness": low
    })


@csrf.exempt
@app.get("/api/analytics/market-gap")
def analytics_market_gap():
    guard = require_any_role("admin", "hr")
    if guard:
        return guard

    role = (request.args.get("role") or "").strip() or "Junior Developer"
    rare_threshold = int(request.args.get("rare_threshold", 3) or 3)

    # рынок (топ навыков)
    market = market_gap_for_role(role, student_skill_names=set(), max_vac=20)
    market_top = market.get("top_market") or []

    # студенты (частота hard skills)
    counter = Counter()
    for s in StudentSkill.query.filter_by(kind="hard").all():
        k = norm_skill(s.name)
        if k:
            counter[k] += 1
    students_top = [k for k, _ in counter.most_common(30)]

    # gap: на рынке часто, у студентов редко
    gap = []
    for sk in market_top:
        if counter.get(sk, 0) < rare_threshold:
            gap.append({"skill": sk, "students_count": counter.get(sk, 0)})

    # coverage: доля рыночных навыков, которые хоть как-то встречаются у студентов
    coverage = 0
    market_set = set(market_top)
    if market_set:
        coverage = int(round(len(market_set & set(students_top)) / len(market_set) * 100))

    return jsonify({
        "ok": True,
        "role": role,
        "coverage_pct": coverage,
        "market_top": market_top[:20],
        "students_top": students_top[:20],
        "gap_top": gap[:20],
        "rare_threshold": rare_threshold
    })


# =============================
# DB INIT
# =============================
with app.app_context():
    db.create_all()

# =============================
# RUN
# =============================


if __name__ == "__main__":
    app.run(debug=True)
