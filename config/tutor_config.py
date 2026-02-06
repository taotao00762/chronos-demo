# ===========================================================================
# Chronos AI Learning Companion
# File: config/tutor_config.py
# Purpose: Tutor module configuration - subjects, grades, teaching styles
# ===========================================================================

"""
Tutor Configuration

Defines available subjects, grades, and teaching styles for the AI tutor.
"""

from typing import List, Dict, Any


# =============================================================================
# Subjects
# =============================================================================

SUBJECTS: List[Dict[str, Any]] = [
    {"id": "math", "name_en": "Mathematics", "name_zh": "Math", "icon": "calculate"},
    {"id": "physics", "name_en": "Physics", "name_zh": "Physics", "icon": "science"},
    {"id": "chemistry", "name_en": "Chemistry", "name_zh": "Chemistry", "icon": "science"},
    {"id": "biology", "name_en": "Biology", "name_zh": "Biology", "icon": "biotech"},
    {"id": "english", "name_en": "English", "name_zh": "English", "icon": "translate"},
    {"id": "history", "name_en": "History", "name_zh": "History", "icon": "history_edu"},
    {"id": "geography", "name_en": "Geography", "name_zh": "Geography", "icon": "public"},
    {"id": "computer", "name_en": "Computer Science", "name_zh": "CS", "icon": "computer"},
    {"id": "custom", "name_en": "Custom Topic", "name_zh": "Custom", "icon": "edit"},
]

SUBJECT_MAP = {s["id"]: s for s in SUBJECTS}


# =============================================================================
# Grades
# =============================================================================

GRADES: List[Dict[str, Any]] = [
    {"id": "elementary", "name_en": "Elementary (1-6)", "name_zh": "Elementary", "level": 1},
    {"id": "middle", "name_en": "Middle School (7-9)", "name_zh": "Middle", "level": 2},
    {"id": "high", "name_en": "High School (10-12)", "name_zh": "High", "level": 3},
    {"id": "college", "name_en": "College", "name_zh": "College", "level": 4},
    {"id": "professional", "name_en": "Professional", "name_zh": "Pro", "level": 5},
]

GRADE_MAP = {g["id"]: g for g in GRADES}


# =============================================================================
# Teaching Styles
# =============================================================================

TEACHING_STYLES: List[Dict[str, Any]] = [
    {
        "id": "patient",
        "name_en": "Patient & Detailed",
        "name_zh": "Patient",
        "icon": "psychology",
        "prompt": "Explain concepts slowly and thoroughly with step-by-step breakdowns. "
                  "Use multiple examples and check understanding frequently.",
    },
    {
        "id": "concise",
        "name_en": "Concise & Direct",
        "name_zh": "Concise",
        "icon": "bolt",
        "prompt": "Be brief and precise. Give direct answers with minimal elaboration. "
                  "Focus on key points only.",
    },
    {
        "id": "socratic",
        "name_en": "Socratic Method",
        "name_zh": "Socratic",
        "icon": "quiz",
        "prompt": "Guide learning through thought-provoking questions. "
                  "Help the student discover answers themselves rather than giving direct answers.",
    },
    {
        "id": "visual",
        "name_en": "Visual & Diagrams",
        "name_zh": "Visual",
        "icon": "image",
        "prompt": "Use visual descriptions and diagrams whenever possible. "
                  "When explaining visual concepts, include [GENERATE_IMAGE: description] tags.",
    },
    {
        "id": "practical",
        "name_en": "Practical Examples",
        "name_zh": "Practical",
        "icon": "handyman",
        "prompt": "Focus on real-world applications and hands-on examples. "
                  "Connect concepts to practical scenarios the student can relate to.",
    },
]

STYLE_MAP = {s["id"]: s for s in TEACHING_STYLES}


# =============================================================================
# System Prompt Generator
# =============================================================================

def generate_tutor_system_prompt(
    subject_id: str = "custom",
    grade_id: str = "high",
    style_id: str = "patient",
    plan_context: dict = None,
    memory_context: dict = None,
    visual_mode: bool = False,
) -> str:
    """
    Generate a context-aware system prompt for the AI tutor.
    
    Args:
        subject_id: Subject identifier.
        grade_id: Grade level identifier.
        style_id: Teaching style identifier.
        plan_context: Optional Principal plan context dict with keys:
            - mode: "recovery" | "standard" | "sprint"
            - topics: List of planned topics for today
            - reasons: List of decision reasons
            - life_pressure: 0.0 to 1.0
        memory_context: 记忆上下文，用于个性化回答
        visual_mode: When True, enforce illustrated responses
    
    Returns:
        System prompt string.
    """
    subject = SUBJECT_MAP.get(subject_id, SUBJECT_MAP["custom"])
    grade = GRADE_MAP.get(grade_id, GRADE_MAP["high"])
    style = STYLE_MAP.get(style_id, STYLE_MAP["patient"])
    
    # Determine complexity level
    complexity_hints = {
        1: "Use simple language, short sentences, and fun examples.",
        2: "Balance simplicity with some technical terms. Build on basics.",
        3: "Use standard academic language. Include formulas and theories.",
        4: "Use advanced terminology. Discuss nuances and edge cases.",
        5: "Assume expert knowledge. Focus on cutting-edge topics.",
    }
    complexity = complexity_hints.get(grade["level"], complexity_hints[3])
    
    # Build Principal context section if available
    principal_section = ""
    if plan_context:
        mode = plan_context.get("mode", "standard")
        topics = plan_context.get("topics", [])
        reasons = plan_context.get("reasons", [])
        pressure = plan_context.get("life_pressure", 0.5)
        
        mode_hints = {
            "recovery": "The student may be tired or stressed. Be extra patient, use simpler examples, and keep sessions shorter.",
            "standard": "Normal learning pace. Balance challenge with support.",
            "sprint": "The student is in a good state. Feel free to introduce more challenging material.",
        }
        
        principal_section = f"""
PRINCIPAL'S CONTEXT (Today's Learning Plan):
- Learning Mode: {mode.upper()}
  {mode_hints.get(mode, mode_hints["standard"])}
- Life Pressure: {"High" if pressure > 0.6 else "Medium" if pressure > 0.3 else "Low"}
"""
        if topics:
            principal_section += f"- Planned Topics: {', '.join(topics[:3])}\n"
        if reasons:
            principal_section += f"- Decision Reason: {reasons[0] if reasons else 'Standard curriculum'}\n"
    
    memory_section = ""
    if memory_context:
        personal = memory_context.get("personal_memories", [])
        strategies = memory_context.get("task_strategies", [])

        memory_lines = []
        if personal:
            pref_list = [m.get("content", "") for m in personal[:3] if m.get("content")]
            if pref_list:
                memory_lines.append(f"- Learner preferences: {'; '.join(pref_list)}")
        if strategies:
            strat_list = []
            for s in strategies[:2]:
                strategy = s.get("strategy", "")
                topic = s.get("topic", "")
                if strategy and topic:
                    strat_list.append(f"{strategy} (for {topic})")
                elif strategy:
                    strat_list.append(strategy)
            if strat_list:
                memory_lines.append(f"- Effective strategies: {'; '.join(strat_list)}")

        if memory_lines:
            memory_section = "\nLEARNER MEMORY (Use to personalize):\n" + "\n".join(memory_lines) + "\n"

    visual_section = ""
    if visual_mode:
        visual_section = """
VISUAL MODE ENABLED:
- Provide dual-channel explanations (text + visuals).
- ALWAYS include at least one [GENERATE_IMAGE: ...] per reply describing the essential diagram or scene.
- Highlight what the learner should notice in the generated image.
"""

    prompt = f"""You are an expert {subject["name_en"]} tutor for {grade["name_en"]} students.

TEACHING STYLE: {style["name_en"]}
{style["prompt"]}

COMPLEXITY LEVEL: {grade["name_en"]}
{complexity}
{principal_section}
{memory_section}
{visual_section}
GUIDELINES:
- Always teach in the context of {subject["name_en"]}
- Adjust your language complexity for {grade["name_en"]} level
- If the student asks about other subjects, gently redirect to {subject["name_en"]}
- **VISUAL TEACHING**: When explaining abstract concepts (math graphs, physics forces, chemical structures, geometric shapes, data flows, etc.), include [GENERATE_IMAGE: detailed description] to create a visual diagram. Examples:
  - Math: [GENERATE_IMAGE: unit circle showing sin(θ) and cos(θ) with angle θ marked]
  - Physics: [GENERATE_IMAGE: free body diagram showing forces on an inclined plane]
  - Chemistry: [GENERATE_IMAGE: 3D model of water molecule H2O with bond angles]
- Be encouraging and supportive
- If uncertain about something, admit it honestly

Start by greeting the student and asking what they'd like to learn about {subject["name_en"]} today."""

    return prompt


def get_subject_options() -> List[Dict[str, str]]:
    """Get subject options for dropdown."""
    return [{"key": s["id"], "text": s["name_en"]} for s in SUBJECTS]


def get_grade_options() -> List[Dict[str, str]]:
    """Get grade options for dropdown."""
    return [{"key": g["id"], "text": g["name_en"]} for g in GRADES]


def get_style_options() -> List[Dict[str, str]]:
    """Get teaching style options for dropdown."""
    return [{"key": s["id"], "text": s["name_en"]} for s in TEACHING_STYLES]
