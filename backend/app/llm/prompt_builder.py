"""
Prompt building with personalization and RAG context injection.

The key idea: every prompt to the LLM is assembled from modular blocks.
Each block adds a layer of context — learner profile, retrieved content,
conversation history — so the LLM can generate truly personalized responses.
"""


# ── Personalization Block ──

def build_personalization_block(profile: dict) -> str:
    """
    Convert the learner profile dict into a natural-language instruction
    that tells the LLM how to adapt its response.
    """
    if not profile:
        return ""

    lines = ["Adapt your response to this learner's profile:"]

    style = profile.get("learning_style", "not set")
    if style == "EXAMPLE_FIRST":
        lines.append("- Start with a concrete example, THEN explain the theory behind it.")
    elif style == "THEORY_FIRST":
        lines.append("- Start with the concept/theory, THEN show examples.")
    elif style == "VISUAL":
        lines.append("- Use diagrams (ASCII art), visual analogies, and step-by-step traces.")
    elif style == "READING":
        lines.append("- Use clear written explanations with well-structured paragraphs.")

    pace = profile.get("pace_preference", "MODERATE")
    if pace == "QUICK":
        lines.append("- Be concise. Skip obvious details. Get to the point fast.")
    elif pace == "DETAILED":
        lines.append("- Be thorough. Explain each step. Don't skip anything.")

    detail = profile.get("explanation_detail_level", "STANDARD")
    if detail == "CONCISE":
        lines.append("- Keep explanations short and focused.")
    elif detail == "VERBOSE":
        lines.append("- Give detailed, comprehensive explanations.")

    complexity = profile.get("preferred_code_complexity", "SIMPLE")
    if complexity == "SIMPLE":
        lines.append("- Use simple, beginner-friendly code with comments.")
    elif complexity == "ADVANCED":
        lines.append("- Use production-quality code with proper patterns.")

    if profile.get("use_analogies", True):
        lines.append("- Include real-world analogies to make concepts intuitive.")

    strengths = profile.get("strengths", [])
    if strengths:
        lines.append(f"- The learner is strong in: {', '.join(strengths)}. You can reference these.")

    weaknesses = profile.get("weaknesses", [])
    if weaknesses:
        lines.append(f"- The learner struggles with: {', '.join(weaknesses)}. Be extra clear here.")

    return "\n".join(lines)


# ── RAG Context Block ──

def build_rag_context_block(retrieved_chunks: list[dict], max_chars_per_chunk: int = 500) -> str:
    """
    Format retrieved content chunks into a prompt block that grounds
    the LLM's response in accurate reference material.

    Truncates each chunk to stay within token budget constraints.
    """
    if not retrieved_chunks:
        return ""

    lines = [
        "Use the following reference material to ground your explanation.",
        "You may rephrase or adapt this material, but stay factually consistent.",
        ""
    ]

    for i, chunk in enumerate(retrieved_chunks, 1):
        summary = chunk.get("content_summary", f"Reference {i}")
        text = chunk.get("content_text", "")
        # Truncate long content to stay within token budget
        if len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + "..."
        lines.append(f"--- Reference {i}: {summary} ---")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


# ── System Prompt (with personalization) ──

def build_system_prompt(profile: dict = None, retrieved_chunks: list[dict] = None) -> str:
    """
    Build the system message that sets up the tutor persona,
    injects learner personalization, and includes RAG context.
    """
    parts = [
        "You are an expert tutor specializing in Data Structures and Algorithms. "
        "You explain concepts clearly with examples and code snippets. "
        "Use markdown formatting for code blocks and emphasis. "
        "Be encouraging but accurate."
    ]

    # Add learner memory (cross-session understanding of the learner)
    learner_summary = profile.get("learner_summary") if profile else None
    if learner_summary:
        parts.append("")
        parts.append("What you know about this learner from previous sessions:")
        parts.append(learner_summary)
        parts.append("Use this understanding to tailor your explanations — but don't mention this summary to the learner.")

    # Add personalization
    personalization = build_personalization_block(profile)
    if personalization:
        parts.append("")
        parts.append(personalization)

    # Add RAG context
    rag_context = build_rag_context_block(retrieved_chunks)
    if rag_context:
        parts.append("")
        parts.append(rag_context)

    return "\n".join(parts)


# ── Explanation Prompt (for initial chat creation) ──

def build_explanation_prompt(
    topic_name: str,
    knowledge_level: str,
    description: str | None,
    profile: dict = None,
    retrieved_chunks: list[dict] = None,
):
    """Build the prompt for the initial explanation when creating a chat session."""
    prompt = f"""Generate a structured JSON response for the topic below.

Topic: {topic_name}
Level: {knowledge_level}
Additional description: {description or "None"}

Return STRICTLY in JSON format like:

{{
  "title": "Short 4-6 word chat title",
  "explanation": "Detailed explanation here using markdown formatting..."
}}

Do not include extra text outside the JSON.
Return valid JSON only."""

    return prompt


# ── Quiz Prompt ──

def build_quiz_prompt(
    topic_name: str,
    level: str,
    profile: dict = None,
    weak_areas: list[str] = None,
):
    """Build the prompt for generating a quiz question."""
    base = f"""You are an expert tutor.

Generate a quiz (only one question) in STRICT JSON format:

{{
  "question": "Question text",
  "options": {{
      "A": "Option text",
      "B": "Option text",
      "C": "Option text",
      "D": "Option text"
  }},
  "correct_option": "A",
  "points": 10,
  "hint": "Short hint",
  "explanation": "Detailed explanation"
}}

Topic: {topic_name}
Level: {level}
Points should be based on the level of the question."""

    # Target weak areas if available
    if weak_areas:
        base += f"\n\nFocus the question on these areas the learner struggles with: {', '.join(weak_areas)}"

    base += "\nReturn ONLY valid JSON."
    return base
