from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.tutor_config import generate_tutor_system_prompt


def test_tutor_prompt_includes_memory_context():
    memory_context = {
        "personal_memories": [{"content": "Prefers visual explanations"}],
        "task_strategies": [{"strategy": "Use spaced repetition", "topic": "math"}],
    }
    prompt = generate_tutor_system_prompt(
        subject_id="math",
        grade_id="high",
        style_id="patient",
        memory_context=memory_context,
    )
    assert "LEARNER MEMORY" in prompt
    assert "Prefers visual explanations" in prompt
    assert "Use spaced repetition" in prompt
