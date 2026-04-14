"""
One-time script to generate and index educational content for all concept nodes.

For each concept, generates 3 explanation variants (beginner, intermediate, advanced)
using the LLM, then embeds and stores them in the vector store.

Usage:
    docker compose exec backend python -m app.rag.content_seeder
"""
import time
import json
from app.db.session import SessionLocal
from app.models.concept_node import ConceptNode
from app.llm.factory import get_llm_provider
from app.rag.indexer import index_batch
from app.repositories.embedding_repo import EmbeddingRepository

LEVELS = [
    {
        "name": "BEGINNER",
        "instruction": (
            "Explain this to a complete beginner. Use simple language, "
            "real-world analogies, and avoid jargon. Include a very simple code example."
        ),
    },
    {
        "name": "INTERMEDIATE",
        "instruction": (
            "Explain this to someone who knows basic programming. "
            "Include code examples with comments, mention time/space complexity, "
            "and compare with related concepts."
        ),
    },
    {
        "name": "ADVANCED",
        "instruction": (
            "Explain this at an advanced level. Include edge cases, "
            "optimization techniques, formal complexity analysis, "
            "and real-world applications. Show production-quality code."
        ),
    },
]


def _generate_explanation(llm, concept: ConceptNode, level: dict) -> str | None:
    """Call the LLM to generate one explanation variant."""
    prompt = f"""You are an expert DSA tutor. Generate a clear, educational explanation.

Topic: {concept.display_name}
Description: {concept.description or concept.display_name}
Level: {level['name']}
Instructions: {level['instruction']}

Write the explanation directly as plain text using markdown formatting.
Do NOT wrap it in JSON or code fences. Just write the explanation."""

    try:
        raw = llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        # The response IS the explanation — no JSON parsing needed
        return raw.strip()
    except Exception as e:
        print(f"  Error generating {level['name']} for {concept.name}: {e}")
        return None


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        repo = EmbeddingRepository(db)
        existing_count = repo.count_all()
        if existing_count > 0:
            print(f"Vector store already has {existing_count} embeddings. Skipping seed.")
            print("To re-seed, delete existing embeddings first.")
            return

        concepts = db.query(ConceptNode).order_by(ConceptNode.difficulty_tier).all()
        if not concepts:
            print("No concept nodes found. Run seed_graph.py first.")
            return

        llm = get_llm_provider()
        total_indexed = 0

        for i, concept in enumerate(concepts):
            print(f"\n[{i+1}/{len(concepts)}] Generating content for: {concept.display_name}")

            batch_items = []
            for level in LEVELS:
                explanation = _generate_explanation(llm, concept, level)
                if not explanation:
                    continue

                batch_items.append({
                    "content_type": "EXPLANATION",
                    "content_text": explanation,
                    "concept_node_id": concept.id,
                    "difficulty_level": level["name"],
                    "content_summary": f"{concept.display_name} — {level['name']}",
                    "metadata": {
                        "subject": concept.subject,
                        "tags": concept.tags_json or [],
                        "concept_name": concept.name,
                    },
                })

                # Small delay to respect Groq rate limits (30 req/min)
                time.sleep(2.5)

            if batch_items:
                count = index_batch(db, batch_items)
                total_indexed += count
                print(f"  Indexed {count} chunks for {concept.display_name}")

        print(f"\nDone! Total chunks indexed: {total_indexed}")

    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
