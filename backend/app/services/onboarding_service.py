"""
Onboarding flow: collect preferences → placement quiz → set initial mastery.

The placement quiz is a fixed set of questions spanning difficulty tiers.
Based on performance, we set initial mastery levels for concept groups
so the knowledge graph starts with a meaningful state instead of all zeros.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.learner_profile_service import LearnerProfileService
from app.repositories.knowledge_graph_repo import KnowledgeGraphRepository
from app.models.concept_mastery import ConceptMastery


# Pre-defined placement questions — no LLM call needed.
# Each question maps to concept(s) and a difficulty tier.
PLACEMENT_QUESTIONS = [
    {
        "question": "What is the time complexity of accessing an element in an array by index?",
        "options": {"A": "O(1)", "B": "O(n)", "C": "O(log n)", "D": "O(n²)"},
        "correct": "A",
        "tier": 1,
        "concepts": ["arrays", "time_complexity"],
    },
    {
        "question": "Which data structure follows the LIFO (Last In, First Out) principle?",
        "options": {"A": "Queue", "B": "Array", "C": "Stack", "D": "Linked List"},
        "correct": "C",
        "tier": 1,
        "concepts": ["stacks"],
    },
    {
        "question": "What is the worst-case time complexity of linear search?",
        "options": {"A": "O(1)", "B": "O(log n)", "C": "O(n)", "D": "O(n log n)"},
        "correct": "C",
        "tier": 1,
        "concepts": ["linear_search", "time_complexity"],
    },
    {
        "question": "In a singly linked list, what does each node contain?",
        "options": {
            "A": "Only data",
            "B": "Data and a pointer to the next node",
            "C": "Data and pointers to next and previous nodes",
            "D": "Only a pointer to the next node",
        },
        "correct": "B",
        "tier": 1,
        "concepts": ["linked_lists"],
    },
    {
        "question": "What is the time complexity of binary search on a sorted array?",
        "options": {"A": "O(n)", "B": "O(n²)", "C": "O(log n)", "D": "O(1)"},
        "correct": "C",
        "tier": 2,
        "concepts": ["binary_search"],
    },
    {
        "question": "Which sorting algorithm has the best average-case time complexity?",
        "options": {
            "A": "Bubble Sort — O(n²)",
            "B": "Merge Sort — O(n log n)",
            "C": "Selection Sort — O(n²)",
            "D": "Insertion Sort — O(n²)",
        },
        "correct": "B",
        "tier": 2,
        "concepts": ["merge_sort", "sorting_basics"],
    },
    {
        "question": "What happens when two different keys hash to the same index in a hash table?",
        "options": {
            "A": "The second key is discarded",
            "B": "A collision occurs",
            "C": "The hash table doubles in size",
            "D": "An error is thrown",
        },
        "correct": "B",
        "tier": 2,
        "concepts": ["hash_tables"],
    },
    {
        "question": "In a binary search tree, where is the smallest element located?",
        "options": {
            "A": "The root node",
            "B": "The rightmost node",
            "C": "The leftmost node",
            "D": "Any leaf node",
        },
        "correct": "C",
        "tier": 3,
        "concepts": ["binary_search_trees"],
    },
    {
        "question": "Which traversal visits nodes level by level in a tree?",
        "options": {
            "A": "In-order traversal",
            "B": "Pre-order traversal",
            "C": "Post-order traversal",
            "D": "Breadth-first search (BFS)",
        },
        "correct": "D",
        "tier": 3,
        "concepts": ["bfs", "trees"],
    },
    {
        "question": "What is the key idea behind dynamic programming?",
        "options": {
            "A": "Always use recursion",
            "B": "Store solutions to subproblems to avoid recomputation",
            "C": "Divide the problem into unrelated subproblems",
            "D": "Use greedy choices at each step",
        },
        "correct": "B",
        "tier": 4,
        "concepts": ["dynamic_programming", "recursion"],
    },
]


class OnboardingService:

    def __init__(self, db: Session):
        self.db = db
        self.profile_service = LearnerProfileService(db)
        self.graph_repo = KnowledgeGraphRepository(db)

    def get_placement_quiz(self):
        """Return the placement quiz questions (without correct answers)."""
        questions = []
        for i, q in enumerate(PLACEMENT_QUESTIONS):
            questions.append({
                "index": i,
                "question": q["question"],
                "options": q["options"],
                "tier": q["tier"],
            })
        return questions

    def submit_preferences(self, user_id, preferences: dict):
        """Save learning preferences from onboarding step 1."""
        self.profile_service.update_preferences(user_id, {
            "learning_style": preferences.get("learning_style"),
            "pace_preference": preferences.get("pace_preference"),
            "explanation_detail_level": preferences.get("explanation_detail_level", "STANDARD"),
            "preferred_code_complexity": preferences.get("preferred_code_complexity", "SIMPLE"),
            "analogy_preference": preferences.get("use_analogies", True),
        })

    def submit_placement(self, user_id, answers: list[dict]):
        """
        Grade the placement quiz and set initial mastery levels.

        Returns a summary of the results.
        """
        # Grade answers
        correct_by_concept = {}  # concept_name -> [True/False, ...]
        total_correct = 0
        results = []

        for answer in answers:
            idx = answer["question_index"]
            if idx < 0 or idx >= len(PLACEMENT_QUESTIONS):
                continue

            question = PLACEMENT_QUESTIONS[idx]
            is_correct = answer["selected_option"] == question["correct"]
            if is_correct:
                total_correct += 1

            results.append({
                "question_index": idx,
                "is_correct": is_correct,
                "correct_option": question["correct"],
                "tier": question["tier"],
            })

            # Track per-concept performance
            for concept_name in question["concepts"]:
                if concept_name not in correct_by_concept:
                    correct_by_concept[concept_name] = []
                correct_by_concept[concept_name].append(is_correct)

        # Set initial mastery levels based on placement results
        all_nodes = self.graph_repo.get_all_nodes("dsa")
        node_map = {n.name: n for n in all_nodes}

        for concept_name, correctness_list in correct_by_concept.items():
            node = node_map.get(concept_name)
            if not node:
                continue

            accuracy = sum(correctness_list) / len(correctness_list)
            # Convert accuracy to initial mastery (placement is just a starting point)
            initial_mastery = accuracy * 0.6  # Cap at 0.6 — they haven't studied yet

            mastery = self.graph_repo.get_user_mastery(user_id, node.id)
            if not mastery:
                mastery = ConceptMastery(
                    user_id=user_id,
                    concept_node_id=node.id,
                )
                mastery = self.graph_repo.create_mastery(mastery)

            mastery.mastery_level = initial_mastery
            mastery.confidence = 0.2  # Low confidence — just a placement test
            mastery.total_answers = len(correctness_list)
            mastery.correct_answers = sum(correctness_list)
            mastery.total_interactions = len(correctness_list)
            mastery.last_reviewed_at = datetime.utcnow()

        self.db.commit()

        # Mark onboarding as complete
        profile = self.profile_service.get_or_create_profile(user_id)
        profile.onboarding_completed = True
        self.db.commit()

        # Determine overall level
        score_pct = (total_correct / len(PLACEMENT_QUESTIONS)) * 100 if PLACEMENT_QUESTIONS else 0
        if score_pct >= 70:
            level = "ADVANCED"
        elif score_pct >= 40:
            level = "INTERMEDIATE"
        else:
            level = "BEGINNER"

        return {
            "total_questions": len(PLACEMENT_QUESTIONS),
            "correct_answers": total_correct,
            "score_percentage": round(score_pct, 1),
            "assessed_level": level,
            "results": results,
        }
