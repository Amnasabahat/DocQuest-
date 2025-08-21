import streamlit as st
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import patient_agent, evaluator_agent   # <-- AI patient + evaluator

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
# Load cases
# -------------------------
@st.cache_data
def load_cases():
    with open("cases.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]

cases = load_cases()

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

# -------------------------
# Helper Functions
# -------------------------
def reset_case_state():
    ss.current_case = None
    ss.revealed_tests = []
    ss.chat_log = []
    ss.latest_feedback = None

def reveal_test(test_name):
    if test_name not in ss.revealed_tests:
        ss.revealed_tests.append(test_name)

# -------------------------
# Sidebar
# -------------------------
st.sidebar.title("DocQuest 🩺")
st.sidebar.markdown("**Disclaimer:** Educational simulation only — not medical advice.")

# Show progress
if ss.scores:
    st.sidebar.metric("Cases Completed", len(ss.scores))
    avg_score = sum(f["diagnosis_score"]+f["tests_score"]+f["plan_score"] for f in ss.scores) / len(ss.scores)
    st.sidebar.metric("Average Score", f"{avg_score:.1f}/10")
else:
    st.sidebar.info("No cases attempted yet.")

# -------------------------
# ROUTES
# -------------------------
def page_home():
    st.title("🏥 DocQuest")
    st.markdown("Welcome to **DocQuest**, your medical case simulation platform. 🚑\n\n"
                "Your journey through real medical cases — learn, practice, and grow like a doctor.")
    if st.button("▶️ Start Simulation"):
        ss.page = "CATEGORY_SELECT"
        st.rerun()

def page_category_select():
    st.title("📂 Select Case Category")

    categories = sorted(set(c["category"] for c in cases))
    selected_category = st.selectbox("Choose a category", ["-- Select --"] + categories)

    if selected_category != "-- Select --":
        ss.current_category = selected_category
        st.markdown(f"### Cases in {selected_category}")

        category_cases = [c for c in cases if c["category"] == selected_category]
        for case in category_cases:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**Case {case['id']}**")  # sirf Case number show hoga
            with col2:
                if st.button("Open", key=f"open_{case['id']}"):
                    ss.current_case = case
                    ss.page = "CASE_DETAIL"
                    st.rerun()

def page_case_detail():
    case = ss.current_case

    # Back button
    if st.button("⬅️ Back to Categories"):
        reset_case_state()
        ss.page = "CATEGORY_SELECT"
        st.rerun()

    # Case Info
    st.markdown(f"### 🩺 Case {case['id']}")
    st.markdown(f"**Title:** {(case['title'])}")
    st.markdown(f"**Description:** {(case['description'])}")
    st.markdown(f"**Symptoms:** {', '.join(case['symptoms'])}")

    # Tabs
    tab1, tab2 = st.tabs(["💬 Interview Patient",  "📝 Solve Case"])

    # -------------------------
    # Interview Patient (GPT-5)
    # -------------------------
    with tab1:
        st.subheader("Interview the Patient")

        if "interview_q" not in ss:
            ss.interview_q = ""  # Initialize session state

        question = st.text_input("Ask your question:", value=ss.interview_q, key="interview_q_input")

        if st.button("Send Question", key="interview_btn"):
            if question.strip():
                ss.chat_log.append(("You", question))

                # Call GPT-5 for patient reply
                messages = patient_agent(case, question)
                response = client.chat.completions.create(
                    model="openai/gpt-5-chat-latest",
                    messages=messages,
                    temperature=0.7,
                    top_p=0.7,
                    frequency_penalty=1,
                )
                reply = response.choices[0].message.content
                ss.chat_log.append(("Patient", reply))

                # Clear text input after sending
                ss.interview_q = ""  
                st.rerun()

        for who, msg in ss.chat_log[-10:]:
            st.write(f"**{who}:** {msg}")




    # -------------------------
    # Solve Case (Evaluator)
    # -------------------------
    with tab2:
        st.subheader("Solve the Case")
        with st.form("solve_form"):
            student_diag = st.text_input("Provisional Diagnosis")

            # Ab student khud tests likhega (comma separated)
            tests_input = st.text_area("Key Tests (separate multiple tests with commas)")
            student_tests = [t.strip() for t in tests_input.split(",") if t.strip()]

            student_plan = st.text_area("Initial Management Plan")
            submit = st.form_submit_button("Submit for Feedback")
        
        if submit:
            student_answer = {
                "diagnosis": student_diag,
                "tests": student_tests,
                "plan": student_plan
            }
            ss.student_answers[case["id"]] = student_answer

            # AI evaluator feedback
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
            ss.page = "FEEDBACK"
            st.rerun()


def page_feedback():
    fb = ss.latest_feedback
    st.subheader("📊 Feedback & Learning")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Diagnosis", f"{fb['diagnosis_score']}/4")
    col2.metric("Tests", f"{fb['tests_score']}/3")
    col3.metric("Plan", f"{fb['plan_score']}/3")
    col4.metric("Total", f"{fb['diagnosis_score']+fb['tests_score']+fb['plan_score']}/10")

    st.subheader("💡 Feedback Notes")
    for line in fb["feedback"]:
        st.write(f"- {line}")

    if fb.get("learning_points"):
        st.subheader("📘 Learning Points")
        for lp in fb["learning_points"]:
            st.write(f"- {lp}")

    if fb.get("red_flags"):
        st.error("⚠️ Red flags detected! Review carefully.")

    if st.button("➡️ Back to Categories"):
        reset_case_state()
        ss.page = "CATEGORY_SELECT"
        st.rerun()

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
