# from src.agents.learning_agent import generate_learning_materials
# from src.agents.quiz_agent import generate_quiz_for_topic
# from src.agents.project_agent import generate_project_ideas
# # example usage: call after the pipeline produced ProjectIdea objects (projects)
# from src.tools.project_template import create_project_template
# from typing import List
# import os, json

# def run_pipeline(topics: List[str], serper_key: str = None):
#     print('Running pipeline for topics:', topics)
#     materials = generate_learning_materials(topics, max_per_topic=3, serper_key=serper_key)

#     # Use Pydantic's model_dump with mode="json" so HttpUrl/Url objects become plain strings
#     jo = [m.model_dump(mode="json") for m in materials]

#     # write example output to disk
#     os.makedirs('data/examples', exist_ok=True)
#     out_path = os.path.join('data/examples', 'learning_materials.json')
#     with open(out_path, 'w', encoding='utf-8') as f:
#         json.dump(jo, f, indent=2, ensure_ascii=False)
#     print(f'Wrote {len(jo)} learning materials to {out_path}')
    

#     #Generate quizzes per topic
#     quizzes = []
#     for t in topics:
#         q = generate_quiz_for_topic(t, n_questions=5)
#         quizzes.append(q)
#     jo_quizzes = [q.model_dump(mode='json') for q in quizzes]
#     qpath = os.path.join('data/examples', 'quizzes.json')
#     with open(qpath, 'w', encoding='utf-8') as f:
#         json.dump(jo_quizzes, f, indent=2, ensure_ascii=False)
#     print(f'Wrote {len(jo_quizzes)} quizzes to {qpath}')

#     # Generate project ideas
#     projects = generate_project_ideas(topics, level=level, n=3)
#     jo_projects = [p.model_dump(mode='json') for p in projects]
#     ppath = os.path.join('data/examples', 'projects.json')
#     with open(ppath, 'w', encoding='utf-8') as f:
#         json.dump(jo_projects, f, indent=2, ensure_ascii=False)
#     print(f'Wrote {len(jo_projects)} project ideas to {ppath}')

#     return {
#         'materials': jo_materials,
#         'quizzes': jo_quizzes,
#         'projects': jo_projects
#     }


from src.agents.learning_agent import generate_learning_materials
from src.agents.quiz_agent import generate_quiz_for_topic
from src.agents.project_agent import generate_project_ideas
from src.tools.project_template import create_project_template
from typing import List, Optional, Dict, Any
import os, json, time, traceback

# Simple retry decorator (lightweight)
def retry(fn, tries=2):
    def wrapper(*a, **kw):
        last_exc = None
        for i in range(tries):
            try:
                return fn(*a, **kw)
            except Exception as e:
                last_exc = e
                # quick backoff
                time.sleep(0.5 + i * 0.5)
        # final raise
        raise last_exc
    return wrapper

# Wrap potentially flaky functions
generate_learning_materials_safe = retry(generate_learning_materials, tries=2)
generate_quiz_for_topic_safe = retry(generate_quiz_for_topic, tries=2)
generate_project_ideas_safe = retry(generate_project_ideas, tries=2)

def _ensure_dirs():
    os.makedirs('data/examples', exist_ok=True)
    os.makedirs('data/examples/raw', exist_ok=True)
    os.makedirs('data/generated_projects', exist_ok=True)

def _dump_raw(name: str, content: Any):
    path = os.path.join('data/examples/raw', f'{name}.txt')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(content))
    except Exception:
        # best-effort; do not crash pipeline for logging issues
        pass

def run_pipeline(
    topics: List[str],
    serper_key: Optional[str] = None,
    level: str = 'beginner',
    generate_templates: bool = True,
    max_per_topic: int = 3
) -> Dict[str, Any]:
    """
    Run the full sequential pipeline:
      1) Learning materials (uses Serper + local LLM)
      2) Quizzes (per topic)
      3) Project ideas (based on topics + level)
      4) Optionally generate small project templates

    Returns a dictionary with JSON-serializable lists for materials/quizzes/projects.
    """
    _ensure_dirs()
    results = {"materials": [], "quizzes": [], "projects": []}
    print(f'Running pipeline for topics: {topics} | level={level}')
    start_all = time.time()

    # --- STEP 1: Learning materials ---
    try:
        t0 = time.time()
        print('> Generating learning materials...')
        materials = generate_learning_materials_safe(topics, max_per_topic=max_per_topic, serper_key=serper_key)
        dur = time.time() - t0
        print(f'  - Retrieved {len(materials)} materials in {dur:.1f}s')
        # model_dump as JSON-serializable dicts
        jo_materials = []
        for i, m in enumerate(materials):
            try:
                jo = m.model_dump(mode='json')
            except Exception:
                # fallback to dict() if model_dump not available
                jo = getattr(m, '__dict__', dict(m))
            jo_materials.append(jo)
        results['materials'] = jo_materials

        # save raw pydantic repr just for debugging
        _dump_raw('materials_raw', jo_materials)
        # write canonical file
        with open('data/examples/learning_materials.json', 'w', encoding='utf-8') as f:
            json.dump(jo_materials, f, indent=2, ensure_ascii=False)
        print('  - Wrote learning_materials.json')
    except Exception as e:
        print('Error in Learning Materials step:', e)
        traceback.print_exc()
        # continue to next steps with empty materials
        results['materials'] = []

    # --- STEP 2: Quiz generation ---
    try:
        t1 = time.time()
        print('> Generating quizzes for each topic...')
        quizzes_objs = []
        for t in topics:
            try:
                q = generate_quiz_for_topic_safe(t, n_questions=5)
                quizzes_objs.append(q)
            except Exception as iqe:
                print(f'  - Quiz generation failed for topic "{t}":', iqe)
                # fallback simple placeholder quiz via function fallback inside agent
                try:
                    q = generate_quiz_for_topic_safe(t, n_questions=3)
                    quizzes_objs.append(q)
                except Exception:
                    print('  - Could not create fallback quiz for topic', t)
        # serialize quizzes
        jo_quizzes = []
        for q in quizzes_objs:
            try:
                joq = q.model_dump(mode='json')
            except Exception:
                joq = getattr(q, '__dict__', dict(q))
            jo_quizzes.append(joq)
        results['quizzes'] = jo_quizzes

        _dump_raw('quizzes_raw', jo_quizzes)
        with open('data/examples/quizzes.json', 'w', encoding='utf-8') as f:
            json.dump(jo_quizzes, f, indent=2, ensure_ascii=False)
        print(f'  - Wrote {len(jo_quizzes)} quizzes to data/examples/quizzes.json')
        print(f'  - Quiz step took {time.time()-t1:.1f}s')
    except Exception as e:
        print('Error in Quiz step:', e)
        traceback.print_exc()
        results['quizzes'] = []

    # --- STEP 3: Project ideas ---
    try:
        t2 = time.time()
        print('> Generating project ideas...')
        projects = generate_project_ideas_safe(topics, level=level, n=3)
        jo_projects = []
        for p in projects:
            try:
                jop = p.model_dump(mode='json')
            except Exception:
                jop = getattr(p, '__dict__', dict(p))
            jo_projects.append(jop)
        results['projects'] = jo_projects

        _dump_raw('projects_raw', jo_projects)
        with open('data/examples/projects.json', 'w', encoding='utf-8') as f:
            json.dump(jo_projects, f, indent=2, ensure_ascii=False)
        print(f'  - Wrote {len(jo_projects)} projects to data/examples/projects.json')
        print(f'  - Project step took {time.time()-t2:.1f}s')
    except Exception as e:
        print('Error in Project step:', e)
        traceback.print_exc()
        results['projects'] = []

    # --- OPTIONAL: Generate project templates ---
    if generate_templates and results.get('projects'):
        print('> Generating project templates for each suggested project...')
        created = []
        for i, proj_dict in enumerate(results['projects']):
            # proj_dict is JSON-serializable; reconstruct ProjectIdea object is optional
            try:
                # create_project_template accepts ProjectIdea model, but it also works if it expects fields on object.
                # We'll call it with a minimal shim object that has the attributes used by create_project_template.
                class Shim:
                    def __init__(self, d):
                        self.title = d.get('title') or f'project-{i+1}'
                        self.description = d.get('description','')
                        self.difficulty = d.get('difficulty','beginner')
                        self.estimated_hours = d.get('estimated_hours', None)
                        self.required_skills = d.get('required_skills', [])
                        self.steps = d.get('steps', [])
                shim = Shim(proj_dict)
                path = create_project_template(shim, base_dir='data/generated_projects')
                created.append(path)
                print('  - Created template:', path)
            except Exception as e:
                print('  - Failed to create template for project', proj_dict.get('title', ''), e)
        results['generated_templates'] = created

    total_time = time.time() - start_all
    print(f'Pipeline finished in {total_time:.1f}s')
    return results

# quick CLI convenience
if __name__ == '__main__':
    import argparse
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument('--topics', type=str, required=False,
                        help='Comma separated topics', default='Pandas data manipulation,Exploratory Data Analysis with Python')
    parser.add_argument('--level', type=str, default='beginner', choices=['beginner','intermediate','advanced'])
    parser.add_argument('--no-templates', dest='templates', action='store_false', help='Do not generate project templates')
    parser.add_argument('--max-per-topic', type=int, default=3)
    args = parser.parse_args()

    topics = [t.strip() for t in args.topics.split(',') if t.strip()]
    serper_key = os.getenv('SERPER_API_KEY', None)
    run_pipeline(topics, serper_key=serper_key, level=args.level, generate_templates=args.templates, max_per_topic=args.max_per_topic)
