import streamlit as st
import json
import os
import random
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from agents import patient_agent, evaluator_agent   # AI patient + evaluator
import threading

HISTORY_FILE = "global_history.jsonl"

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    st.error("API_KEY missing in .env file")
    st.stop()

# initialize client
client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=api_key,
)

# -------------------------
# Helper: History Persistence
# -------------------------
@st.cache_resource
def _history_lock():
    return threading.Lock()

def load_global_history() -> list:
    """Read all attempts from a shared JSONL file (one JSON per line)."""
    if not os.path.exists(HISTORY_FILE):
        return []
    items = []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return items  # newest last

def append_global_history(entry: dict):
    """Append a single attempt to the global history file (thread-safe)."""
    lock = _history_lock()
    with lock:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# -------------------------
# Load cases
# -------------------------
@st.cache_data
def load_cases():
    with open("cases.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]

cases = load_cases()
global_history = load_global_history()

# -------------------------
# Session State Init
# -------------------------
ss = st.session_state
ss.setdefault("page", "HOME")
ss.setdefault("current_category", None)
ss.setdefault("current_case", None)
ss.setdefault("revealed_tests", [])
ss.setdefault("student_answers", {})
ss.setdefault("latest_feedback", None)
ss.setdefault("scores", [])
ss.setdefault("chat_log", [])
ss.setdefault("attempt_history", [])   # per-user, but global added separately

# -------------------------
# Navigation Helper
# -------------------------
def set_page(name: str):
    ss.page = name

# -------------------------
# Helper Functions
# -------------------------
def reset_case_state():
    ss.current_case = None
    ss.revealed_tests = []
    ss.chat_log = []
    ss.latest_feedback = None

def score_to_badge(avg: float) -> str:
    if avg >= 8:
        return "🏆 Pro"
    elif avg >= 5:
        return "⭐ Intermediate"
    elif avg > 0:
        return "🌱 Beginner"
    else:
        return "—"

def snippet(text: str, n: int = 90) -> str:
    return (text[:n] + "…") if len(text) > n else text

# -------------------------
# Sidebar
# -------------------------
st.sidebar.title("DocQuest 🩺")
st.sidebar.markdown("**Disclaimer:** Educational simulation only — not medical advice.")

# 📊 Progress
st.sidebar.markdown("### 📈 Your Progress")
if ss.scores:
    total = len(ss.scores)
    avg_score = sum(
        f["diagnosis_score"] + f["tests_score"] + f["plan_score"] for f in ss.scores
    ) / total
    st.sidebar.write(f"Cases Completed: **{total}**")
    st.sidebar.progress(min(int((avg_score/10)*100), 100))
    st.sidebar.write(f"Average Score: **{avg_score:.1f}/10**")
    st.sidebar.write(f"Badge: **{score_to_badge(avg_score)}**")
else:
    st.sidebar.info("No cases attempted yet.")
    st.sidebar.progress(0)
    st.sidebar.write("Average Score: —")
    st.sidebar.write("Badge: —")

# 📜 Global History (merged)
st.sidebar.markdown("### 📜 Recent Case History")
history_to_show = (ss.attempt_history or []) + global_history

# ✅ keep only highest score per case_id
best_by_case = {}
for item in history_to_show:
    cid = item.get("case_id")
    score = item.get("score", 0)
    if cid not in best_by_case or score > best_by_case[cid]["score"]:
        best_by_case[cid] = item

# sorted by date (latest first)
merged = sorted(best_by_case.values(), key=lambda x: x.get("date", ""), reverse=True)

if merged:
    for i, att in enumerate(merged[:8], 1):  # show last 8 unique cases
        case_id = att.get('case_id', '—')
        score = att.get('score', '—')
        date = att.get('date', '—')

        c1, c2 = st.sidebar.columns([4, 1])
        with c1:
            st.markdown(
                f"""
                <div style="padding:6px 0;">
                    <b>Case {case_id}</b> | {score}/10  
                    <div style="font-size:12px; opacity:.7;">{date}</div>
                </div>
                """, unsafe_allow_html=True
            )
        with c2:
            if st.button("🔄", key=f"reattempt_{i}"):
                case = next((c for c in cases if c["id"] == case_id), None)
                if case:
                    ss.current_case = case
                    set_page("CASE_DETAIL")
else:
    st.sidebar.info("No history yet.")


# -------------------------
# ROUTES
# -------------------------
def page_home():
    st.markdown("<h1 style='margin-bottom:0'>🩺 DocQuest</h1>", unsafe_allow_html=True)
    st.markdown(
        "### Practice real medical cases. Build your diagnostic skills.\n"
        "DocQuest is your safe space to simulate patient encounters and sharpen clinical reasoning."
    )

    st.button("▶️ Start Simulation", use_container_width=True,
              on_click=lambda: set_page("CATEGORY_SELECT"))

    try:
        rc = random.choice(cases)
        st.markdown(f"""
            <div style="border-radius: 12px;
                        padding: 12px;
                        background-color: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        margin-top:15px; margin-bottom:15px;">
                <h3 style="color:#ff9800; margin-bottom:8px;">🔥 Today’s Challenge</h3>
                <p><b>Case:</b> {rc['id']}</p>
                <p style="color:#ccc; font-size:14px;">{snippet(rc.get('description',''), 100)}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Take Challenge", use_container_width=True):
            ss.current_case = rc
            set_page("CASE_DETAIL")
    except Exception:
        st.info("A featured case will appear here when cases.json is loaded.")

def page_category_select():
    st.title("📂 Select Case Category")
    categories = sorted(set(c.get("category", "General") for c in cases))
    selected_category = st.selectbox("Choose a category", categories)
    ss.current_category = selected_category

    st.markdown(f"### Cases in **{selected_category}**")
    category_cases = [c for c in cases if c.get("category") == selected_category]
    if not category_cases:
        st.warning("No cases in this category yet.")
        return

    for case in category_cases:
        with st.container():
            col1, col2 = st.columns([6, 2])
            with col1:
                st.markdown(f"**Case {case['id']}**")
                st.caption(snippet(case.get("description", ""), 110))
            with col2:
                st.button("Open", key=f"open_{case['id']}", use_container_width=True,
                          on_click=_open_case, args=(case,))

def _open_case(case):
    ss.current_case = case
    set_page("CASE_DETAIL")

def page_case_detail():
    case = ss.current_case
    if not case:
        st.warning("No case selected.")
        return

    st.button("⬅️ Back to Categories", on_click=lambda: (_back_to_cat()))
    st.markdown(f"### 🩺 Case {case['id']}")

    st.markdown("#### 🧾 Description")
    st.write(case.get("description", "—"))

    with st.expander("🩺 Symptoms / History", expanded=True):
        st.write(", ".join(case.get("symptoms", [])) or "—")

    tab1, tab2 = st.tabs(["💬 Interview Patient",  "📝 Solve Case"])

    # Interview Patient
    with tab1:
        st.subheader("Interview the Patient")
        if ss.chat_log:
            for who, msg in ss.chat_log[-20:]:
                role = "user" if who == "You" else "assistant"
                with st.chat_message(role):
                    st.write(msg)
        else:
            st.info("Ask follow-up questions like: *When did it start? Any weight loss? Travel history?*")

        user_q = st.chat_input("Type your question to the patient…")
        if user_q:
            ss.chat_log.append(("You", user_q))
            messages = patient_agent(case, user_q)
            response = client.chat.completions.create(
                model="openai/gpt-5-chat-latest",
                messages=messages,
                temperature=0.7,
            )
            reply = response.choices[0].message.content
            ss.chat_log.append(("Patient", reply))

    # Solve Case
    with tab2:
        st.subheader("Solve the Case")
        with st.form("solve_form"):
            student_diag = st.text_input("Provisional Diagnosis")
            tests_input = st.text_area("Key Tests (comma separated)")
            student_tests = [t.strip() for t in tests_input.split(",") if t.strip()]
            student_plan = st.text_area("Initial Management Plan")
            submit = st.form_submit_button("Submit for Feedback")

        if submit:
            student_answer = {"diagnosis": student_diag, "tests": student_tests, "plan": student_plan}
            ss.student_answers[case["id"]] = student_answer

            messages = evaluator_agent(case, student_answer)
            response = client.chat.completions.create(
                model="openai/gpt-5-chat-latest",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            fb = json.loads(response.choices[0].message.content)
            ss.latest_feedback = fb
            ss.scores.append(fb)

            # ✅ Save attempt history (local + global)
            entry = {
                "case_id": case["id"],
                "score": fb["diagnosis_score"] + fb["tests_score"] + fb["plan_score"],
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            ss.attempt_history.append(entry)
            append_global_history(entry)

            set_page("FEEDBACK")

def _back_to_cat():
    reset_case_state()
    set_page("CATEGORY_SELECT")

def page_feedback():
    fb = ss.latest_feedback
    if not fb:
        st.warning("No feedback yet.")
        return

    st.subheader("📊 Feedback & Learning")
    col1, col2, col3, col4 = st.columns(4)
    col1.success(f"Diagnosis: {fb['diagnosis_score']}/4")
    col2.warning(f"Tests: {fb['tests_score']}/3")
    col3.info(f"Plan: {fb['plan_score']}/3")
    col4.write(f"**Total:** {fb['diagnosis_score']+fb['tests_score']+fb['plan_score']}/10")

    st.markdown("### 💡 Feedback Notes")
    for line in fb.get("feedback", []):
        st.write(f"- {line}")

    if fb.get("learning_points"):
        with st.expander("📘 Learning Points", expanded=True):
            for lp in fb["learning_points"]:
                st.write(f"- {lp}")

    if fb.get("red_flags"):
        st.error("⚠️ Red flags detected! Review carefully.")

    # Export option
    export_feedback(fb)

    c1, c2 = st.columns(2)
    c1.button("⬅️ Back to Categories", on_click=_back_to_cat, use_container_width=True)
    c2.button("🎯 Try Another Case", on_click=_back_to_cat, use_container_width=True)

# -------------------------
# Export Feedback PDF
# -------------------------
def export_feedback(fb):
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate("feedback.pdf")
    styles = getSampleStyleSheet()
    story = [Paragraph("Feedback Report", styles["Heading1"])]
    for k, v in fb.items():
        story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    doc.build(story)
    with open("feedback.pdf", "rb") as f:
        st.download_button("📥 Download Feedback PDF", f, file_name="feedback.pdf")

# -------------------------
# Router
# -------------------------
ROUTES = {
    "HOME": page_home,
    "CATEGORY_SELECT": page_category_select,
    "CASE_DETAIL": page_case_detail,
    "FEEDBACK": page_feedback,
}

ROUTES.get(ss.page, page_home)()
