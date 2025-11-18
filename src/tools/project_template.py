# src/tools/project_template.py
import os
import re
from pathlib import Path
from typing import List
from src.models.project_models import ProjectIdea
import json

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

NOTEBOOK_MINIMAL = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# Notebook\n\nThis is a starter notebook generated automatically.\n"]
  }
 ],
 "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}},
 "nbformat": 4,
 "nbformat_minor": 5
}

def create_project_template(project: ProjectIdea, base_dir: str = "generated_projects") -> str:
    """
    Creates a folder with a README, requirements.txt, main.py, notebook.ipynb, src/, data/.
    Returns the path to the created project folder.
    """
    title = project.title or "project"
    slug = _slugify(title)[:120] or "project"
    root = Path(base_dir) / slug
    if root.exists():
        # add suffix to avoid collision
        import time
        root = Path(f"{str(root)}-{int(time.time())}")
    root.mkdir(parents=True, exist_ok=True)

    # README
    readme = f"# {project.title}\n\n"
    readme += f"**Difficulty:** {project.difficulty}\n\n"
    if project.estimated_hours:
        readme += f"**Estimated hours:** {project.estimated_hours}\n\n"
    readme += f"## Description\n\n{project.description}\n\n"
    readme += "## Steps\n\n"
    if project.steps:
        for i, s in enumerate(project.steps, 1):
            readme += f"{i}. {s}\n"
    else:
        readme += "1. TODO: define steps\n"

    readme += "\n## Required Skills\n\n"
    if project.required_skills:
        readme += "\n".join([f"- {s}" for s in project.required_skills]) + "\n"
    else:
        readme += "- TODO: list required skills\n"

    readme += "\n## How to run\n\n"
    readme += "1. Create virtualenv: `python -m venv .venv`\n"
    readme += "2. Activate and install `pip install -r requirements.txt`\n"
    readme += "3. Run `python main.py` or open `notebook.ipynb` in Jupyter.\n"

    (root / "README.md").write_text(readme, encoding="utf-8")

    # requirements.txt (starter)
    requirements = [
        "pandas",
        "numpy",
    ]
    # add hints from required_skills
    if project.required_skills:
        if any("flask" in s.lower() for s in project.required_skills):
            requirements.append("flask")
        if any("streamlit" in s.lower() for s in project.required_skills):
            requirements.append("streamlit")
        if any("scikit" in s.lower() for s in project.required_skills):
            requirements.append("scikit-learn")

    (root / "requirements.txt").write_text("\n".join(requirements), encoding="utf-8")

    # main.py
    main_py = """\"\"\"Starter main.py for the generated project. Fill in the TODOs.\"\"\"
def main():
    print("This is a starter script for the project. Please open README.md for next steps.")

if __name__ == '__main__':
    main()
"""
    (root / "main.py").write_text(main_py, encoding="utf-8")

    # create src and data folders
    (root / "src").mkdir(exist_ok=True)
    (root / "data").mkdir(exist_ok=True)

    # create minimal notebook
    nb_path = root / "notebook.ipynb"
    nb_path.write_text(json.dumps(NOTEBOOK_MINIMAL, indent=2), encoding="utf-8")

    # create a small metadata.json describing the project idea (useful later)
    meta = {
        "title": project.title,
        "description": project.description,
        "difficulty": project.difficulty,
        "estimated_hours": project.estimated_hours,
        "required_skills": project.required_skills,
        "steps": project.steps
    }
    (root / "project.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return str(root)
