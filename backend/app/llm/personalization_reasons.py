"""
Build a short, human-readable list of the personalization signals that
shaped a given assistant message.

Mirrors the blocks in prompt_builder.build_personalization_block so the
UI can surface *why* the tutor adapted the way it did — turning the
hidden machinery into a visible differentiator.

Each reason is `{"label": str, "detail": str}`. We cap at 4 so the pill
under a message stays compact — the ordering below reflects priority
(learner-specific signals first, generic ones last).
"""


def build_reasons(
    profile: dict | None,
    retrieved_chunks: list[dict] | None,
) -> list[dict]:
    if not profile:
        return []

    reasons: list[dict] = []

    # Learning style — the single most distinctive shaping signal.
    style = profile.get("learning_style")
    style_map = {
        "EXAMPLE_FIRST": (
            "Example-first",
            "Started with a concrete example because you learn best from examples.",
        ),
        "THEORY_FIRST": (
            "Theory-first",
            "Led with the concept because you prefer theory up front.",
        ),
        "VISUAL": (
            "Visual style",
            "Used diagrams or step-by-step traces — you learn visually.",
        ),
        "READING": (
            "Reading style",
            "Wrote a clear, structured explanation — your preferred format.",
        ),
    }
    if style in style_map:
        label, detail = style_map[style]
        reasons.append({"label": label, "detail": detail})

    # Weaknesses get priority over strengths — "extra care" is a stronger
    # felt signal than "built on strengths".
    weaknesses = profile.get("weaknesses") or []
    if weaknesses:
        top = ", ".join(weaknesses[:2])
        reasons.append({
            "label": "Extra care",
            "detail": f"Went slower on {top} — it's been tricky for you.",
        })

    strengths = profile.get("strengths") or []
    if strengths:
        top = ", ".join(strengths[:2])
        reasons.append({
            "label": "Built on strengths",
            "detail": f"Referenced your solid grasp of {top}.",
        })

    # Cross-session memory — the "gets smarter every session" story.
    if profile.get("learner_summary"):
        reasons.append({
            "label": "Remembered you",
            "detail": "Used what I've learned about you from earlier sessions.",
        })

    # Pace only if explicitly non-default (otherwise every message gets this).
    pace = profile.get("pace_preference")
    detail_level = profile.get("explanation_detail_level")
    if pace == "QUICK" or detail_level == "CONCISE":
        reasons.append({
            "label": "Concise pace",
            "detail": "Kept things brief — you prefer to move quickly.",
        })
    elif pace == "DETAILED" or detail_level == "VERBOSE":
        reasons.append({
            "label": "Thorough pace",
            "detail": "Walked through it step-by-step — you like detail.",
        })

    # RAG grounding — shows the tutor isn't freestyling.
    if retrieved_chunks:
        n = len(retrieved_chunks)
        reasons.append({
            "label": "Grounded",
            "detail": f"Drew from {n} reference explanation{'s' if n != 1 else ''}.",
        })

    return reasons[:4]
