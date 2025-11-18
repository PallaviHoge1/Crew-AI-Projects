from src.tools.serper_tool import search_serper
from src.utils.llm import safe_summarize
from src.models.learning_models import LearningMaterial
from typing import List
import os

def generate_learning_materials(topics: List[str], max_per_topic: int = 3, serper_key: str = None) -> List[LearningMaterial]:
    out = []
    for topic in topics:
        query = f"{topic} tutorial tutorial video exercises"
        results = search_serper(query, api_key=serper_key, max_results=max_per_topic)
        for r in results:
            summary = None
            # try summarizing the snippet via local LLM (best-effort)
            snippet = r.get('snippet') or ''
            try:
                if snippet:
                    summary = safe_summarize(snippet)
            except Exception as e:
                summary = None
            mat = LearningMaterial(
                title=r.get('title') or topic,
                url=r.get('link'),
                source=r.get('source'),
                type='article' if 'video' not in (r.get('title') or '').lower() else 'video',
                summary=summary,
                estimated_time_minutes=None
            )
            out.append(mat)
    return out
