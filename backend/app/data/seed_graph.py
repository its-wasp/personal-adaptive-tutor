"""
Seed the knowledge graph from dsa_graph.json into the database.

Usage:
    docker compose exec backend python -m app.data.seed_graph
"""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.concept_node import ConceptNode
from app.models.concept_edge import ConceptEdge, RelationType


def seed():
    data_path = Path(__file__).parent / "dsa_graph.json"
    with open(data_path) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(ConceptNode).filter(ConceptNode.subject == data["subject"]).count()
        if existing > 0:
            print(f"Graph '{data['subject']}' already seeded ({existing} nodes). Skipping.")
            return

        # Create nodes
        node_map = {}  # name -> ConceptNode
        for node_data in data["nodes"]:
            node = ConceptNode(
                subject=data["subject"],
                name=node_data["name"],
                display_name=node_data["display_name"],
                description=node_data.get("description"),
                difficulty_tier=node_data.get("difficulty_tier", 1),
                estimated_minutes=node_data.get("estimated_minutes"),
                tags_json=node_data.get("tags"),
            )
            db.add(node)
            node_map[node_data["name"]] = node

        db.flush()  # Assigns IDs to nodes

        # Create edges
        for edge_data in data["edges"]:
            from_node = node_map.get(edge_data["from"])
            to_node = node_map.get(edge_data["to"])

            if not from_node or not to_node:
                print(f"Warning: skipping edge {edge_data['from']} -> {edge_data['to']} (node not found)")
                continue

            edge = ConceptEdge(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                relation_type=RelationType(edge_data["type"]),
                weight=edge_data.get("weight", 1.0),
            )
            db.add(edge)

        db.commit()
        print(f"Seeded {len(node_map)} nodes and {len(data['edges'])} edges for '{data['subject']}'.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding graph: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
