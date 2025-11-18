# Placeholder for project tool
from typing import List, Dict
from src.models.project_models import ProjectIdea
from src.utils.llm import call_ollama
import json, re

def _build_project_prompt(topics: List[str], level: str, n: int = 3):
    topics_str = ', '.join(topics)
    return (f"You are an assistant that suggests practical project ideas.\n\n"
            f"Topics: {topics_str}\n"
            f"Expertise level: {level}\n\n"
            f"Return a JSON array of {n} project objects with fields: title, description, difficulty (beginner|intermediate|advanced), estimated_hours (int), steps (array of short step strings), required_skills (array of strings).\n\n"
            "Provide only the JSON array as the output.")


def suggest_projects(topics: List[str], level: str = 'beginner', n: int = 3, model: str = 'llama3.2:3b') -> List[ProjectIdea]:
    prompt = _build_project_prompt(topics, level, n)
    resp = call_ollama(prompt, model=model)
    arr = None
    try:
        arr = json.loads(resp)
    except Exception:
        m = re.search(r"\[\s*\{.*\}\s*\]", resp, re.S)
        if m:
            try:
                arr = json.loads(m.group(0))
            except Exception:
                arr = None
    if not arr:
        # fallback simple ideas
        arr = []
        for i in range(n):
            arr.append({
                'title': f'{level.title()} Project on {topics[0]} #{i+1}',
                'description': f'A simple project to practice {topics[0]}.',
                'difficulty': level,
                'estimated_hours': 5*(i+1),
                'steps': [f'Step {j+1}' for j in range(4)],
                'required_skills': [topics[0]]
            })
    projects = []
    for obj in arr:
        try:
            p = ProjectIdea(
                title=obj.get('title',''),
                description=obj.get('description',''),
                difficulty=obj.get('difficulty', level),
                estimated_hours=int(obj.get('estimated_hours', 5)),
                steps=obj.get('steps', []),
                required_skills=obj.get('required_skills', [])
            )
            projects.append(p)
        except Exception:
            continue
    return projects
