# 🩺 DocQuest – AI-Powered Medical Case Simulation

DocQuest is an **AI-driven medical case simulator** that allows healthcare students and professionals to practice **patient interactions, clinical reasoning, and diagnosis building**.  
It uses **Streamlit** for the frontend and **OpenAI GPT agents** for simulating both the patient and the evaluator.

---

## Features
- **Virtual AI Patient** – responds to user questions about symptoms and history.  
- **Case Solving Mode** – enter provisional diagnosis, investigations, and management plan.  
- **Evaluator Agent** – scores your answers and provides structured feedback.  
- **Progress Tracking** – shows completed cases, average score, and assigns badge:  
  - 🌱 Beginner  
  - ⭐ Intermediate  
  - 🏆 Pro  
- **Case History Sidebar** – view your recent attempts with date, score, and **🔄 Reattempt button**.  
- **Today’s Challenge** – a highlighted random case shown on the home screen.  
- **Export Feedback as PDF** – download evaluator feedback in a report format.  

---

## Tech Stack
- **Python 3.10+**
- **Streamlit** – interactive frontend
- **OpenAI GPT-5** – patient & evaluator agents
- **dotenv** – environment variable handling
- **ReportLab** – PDF export
- **GitHub** – version control & collaboration

---

## 📂 Project Structure
DocQuest-/
- │── app.py # Main Streamlit app
- │── agents.py # AI patient + evaluator agents
- │── requirements.txt # Python dependencies
- │── cases.json # Medical case dataset
- │── global_history.jsonl # Stores shared history of attempts
- │── requirements.txt # Python dependencies

---

## Usage

- Launch the app and choose Start Simulation.
- Explore Today’s Challenge or pick a case from categories.
- Ask the virtual patient questions in chat.
- Submit your diagnosis, tests, and management plan.
- Receive scored feedback + learning points.
- Track your progress via sidebar badges and reattempt cases.
- Download a Feedback PDF for revision.

---
  
## ⚙️ Installation

1️⃣ **Clone the repository**
```bash
git clone https://github.com/Amnasabahat/DocQuest-.git
cd DocQuest-
```
2️⃣ Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```
3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
▶️ Run the App
```bash
streamlit run app.py
```

