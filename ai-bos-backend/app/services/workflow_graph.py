"""Helpers to sync linear React Flow graphs with denormalized trigger/actions."""

from __future__ import annotations

from typing import Any


def empty_definition() -> dict[str, Any]:
    return {"nodes": [], "edges": []}


def normalize_definition(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return empty_definition()
    nodes = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
    edges = raw.get("edges") if isinstance(raw.get("edges"), list) else []
    clean_nodes: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        position = node.get("position") if isinstance(node.get("position"), dict) else {"x": 0, "y": 0}
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        clean_nodes.append(
            {
                "id": str(node["id"]),
                "type": str(node.get("type") or "action"),
                "position": {
                    "x": float(position.get("x") or 0),
                    "y": float(position.get("y") or 0),
                },
                "data": {
                    "label": str(data.get("label") or "Étape"),
                    "kind": str(data.get("kind") or node.get("type") or "action"),
                },
            }
        )
    clean_edges: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        clean_edges.append(
            {
                "id": str(edge.get("id") or f"e-{source}-{target}"),
                "source": str(source),
                "target": str(target),
            }
        )
    return {"nodes": clean_nodes, "edges": clean_edges}


def definition_from_legacy(trigger: str, actions: list[str] | None) -> dict[str, Any]:
    """Build a linear canvas for seeded workflows that only have trigger/actions."""
    nodes: list[dict[str, Any]] = [
        {
            "id": "trigger-1",
            "type": "trigger",
            "position": {"x": 80, "y": 120},
            "data": {"label": trigger or "Déclencheur manuel", "kind": "trigger"},
        }
    ]
    edges: list[dict[str, Any]] = []
    prev = "trigger-1"
    for index, action in enumerate(actions or []):
        node_id = f"action-{index + 1}"
        nodes.append(
            {
                "id": node_id,
                "type": "action",
                "position": {"x": 80 + (index + 1) * 220, "y": 120},
                "data": {"label": action, "kind": "action"},
            }
        )
        edges.append({"id": f"e-{prev}-{node_id}", "source": prev, "target": node_id})
        prev = node_id
    return {"nodes": nodes, "edges": edges}


def derive_trigger_actions(definition: dict[str, Any]) -> tuple[str, list[str]]:
    nodes = {n["id"]: n for n in definition.get("nodes") or []}
    outgoing: dict[str, list[str]] = {}
    incoming: set[str] = set()
    for edge in definition.get("edges") or []:
        outgoing.setdefault(edge["source"], []).append(edge["target"])
        incoming.add(edge["target"])

    triggers = [n for n in nodes.values() if n.get("type") == "trigger" or (n.get("data") or {}).get("kind") == "trigger"]
    start = triggers[0]["id"] if triggers else next((nid for nid in nodes if nid not in incoming), None)
    if not start and nodes:
        start = next(iter(nodes))

    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    current = start
    while current and current in nodes and current not in seen:
        ordered.append(nodes[current])
        seen.add(current)
        nexts = outgoing.get(current) or []
        current = nexts[0] if nexts else None

    # Append orphans (not in the linear path) as trailing actions
    for node in nodes.values():
        if node["id"] not in seen:
            ordered.append(node)

    trigger_label = "Manuel"
    actions: list[str] = []
    for node in ordered:
        label = str((node.get("data") or {}).get("label") or "Étape")
        if node.get("type") == "trigger" or (node.get("data") or {}).get("kind") == "trigger":
            trigger_label = label
        else:
            actions.append(label)
    return trigger_label, actions
