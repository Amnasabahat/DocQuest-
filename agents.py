# agents.py
import json

# Patient Agent
def patient_agent(case_memory: dict, user_message: str, history: list = None) -> list:
    """
    Generates message history for GPT-5 patient simulation.
    Maintains conversation history to avoid delayed/out-of-sync responses.
    """
    system_prompt = """You are a standardized patient. 
    Answer ONLY as the patient using details from the provided case memory. 
    Do not suggest diagnoses, tests, or treatments. 
    If the student asks for a test result that exists in the case, reveal exactly that result. 
    If a test is not in the case, say “Not available.” 
    Stay brief and realistic."""

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(case_memory)}]

    # Agar purani history hai toh add karo
    if history:
        messages.extend(history)

    # Abhi ka user message add karo
    messages.append({"role": "user", "content": user_message})
    return messages


# Evaluator Agent (no change)
def evaluator_agent(case_memory: dict, student_answer: dict) -> list:
    system_prompt = """You are a medical tutor for an educational simulation (not real medical advice). 
    Compare the student’s diagnosis, tests, and initial plan to the case’s gold answers. 
    Score: diagnosis 0–4, tests 0–3, plan 0–3. 
    Return STRICT JSON with keys: 
      - diagnosis_score 
      - tests_score 
      - plan_score 
      - feedback (array of short strings) 
      - learning_points (array of short strings) 
      - red_flags (boolean) 
    Do not include any text outside JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({
            "student_answer": student_answer,
            "gold_case": case_memory
        })}
    ]
    return messages
