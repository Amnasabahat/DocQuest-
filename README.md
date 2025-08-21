# 🩺 DocQuest – AI-Powered Medical Case Simulation

DocQuest is an **AI-driven medical case simulator** that allows healthcare students and professionals to practice **patient interactions, clinical reasoning, and diagnosis building**.  
It uses **Streamlit** for the frontend and **OpenAI GPT agents** for simulating both the patient and the evaluator.

---

## Features
- **Virtual AI Patient** – responds to user questions about symptoms and history.  
- **Provisional Diagnosis Generator** – builds differential diagnosis based on interaction.  
- **Initial Management Plan** – suggests first-line management steps.  
- **Evaluator Agent** – gives feedback on case handling.  
- **Streamlit Web UI** – simple and interactive interface.  

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **Streamlit** – UI framework
- **OpenAI API GPT-5 PRO** – powering the patient & evaluator agents
- **dotenv** – environment variable handling
- **GitHub** – version control & collaboration

---

## 📂 Project Structure
DocQuest-/
- │── app.py # Main Streamlit app
- │── agents.py # AI patient + evaluator agents
- │── requirements.txt # Python dependencies


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
