# Placeholder
from typing import List
from src.models.quiz_models import Quiz, MCQ
from src.utils.llm import call_ollama
import json

def _build_prompt_for_quiz(topic: str, n_questions: int = 5):
    return (
        f"""You are an educational assistant. Create {n_questions} multiple-choice questions (MCQ) on the following topic."""
        f"Topic: {topic}\n\n"
        "Requirements:\n"
        "- Return output as a JSON array of objects with fields: question, options (array of 4), answer_index (0-3), explanation (short), difficulty (easy|medium|hard)\n"
        "- Make a mix of difficulties, and keep questions clear and concise.\n\n"
        "Provide only the JSON array as the model output."
    )

def generate_quiz_for_topic(topic: str, n_questions: int = 5, model: str = 'llama3.2:3b') -> Quiz:
    prompt = _build_prompt_for_quiz(topic, n_questions)
    resp = call_ollama(prompt, model=model)
    # Attempt to parse JSON from model output
    arr = None
    try:
        arr = json.loads(resp)
    except Exception:
        # Try to locate first JSON substring
        import re
        m = re.search(r"\[\s*\{.*\}\s*\]", resp, re.S)
        if m:
            try:
                arr = json.loads(m.group(0))
            except Exception:
                arr = None
    if not arr:
        # fallback: create simple placeholder questions
        arr = []
        for i in range(n_questions):
            arr.append({
                'question': f'What is a key concept of {topic}? (placeholder {i+1})',
                'options': ['Option A','Option B','Option C','Option D'],
                'answer_index': 0,
                'explanation': 'Placeholder explanation',
                'difficulty': 'easy' if i<2 else 'medium'
            })
    # Build MCQ objects
    mcqs = []
    for item in arr:
        try:
            mcq = MCQ(
                question=item.get('question',''),
                options=item.get('options',[]),
                answer_index=int(item.get('answer_index',0)),
                explanation=item.get('explanation',''),
                difficulty=item.get('difficulty','medium')
            )
            mcqs.append(mcq)
        except Exception:
            continue
    quiz = Quiz(topic=topic, questions=mcqs)
    return quiz
