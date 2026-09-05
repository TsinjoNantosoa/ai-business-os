"""Validation and ordered traversal helpers for React Flow definitions."""

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
        position = node.get("position") if isinstance(node.get("position"), dict) else {}
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        clean_nodes.append(
            {
                "id": str(node["id"]),
                "type": str(node.get("type") or "action"),
                "position": {"x": float(position.get("x") or 0), "y": float(position.get("y") or 0)},
                "data": {
                    "label": str(data.get("label") or "Étape"),
                    "kind": str(data.get("kind") or node.get("type") or "action"),
                    "config": data.get("config") if isinstance(data.get("config"), dict) else {},
                },
            }
        )
    node_ids = {node["id"] for node in clean_nodes}
    clean_edges = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source, target = str(edge.get("source") or ""), str(edge.get("target") or "")
        if source in node_ids and target in node_ids and source != target:
            clean_edges.append({"id": str(edge.get("id") or f"e-{source}-{target}"), "source": source, "target": target})
    return {"nodes": clean_nodes, "edges": clean_edges}


def definition_from_legacy(trigger: str, actions: list[str] | None) -> dict[str, Any]:
    nodes = [{"id": "trigger-1", "type": "trigger", "position": {"x": 80, "y": 120}, "data": {"label": trigger or "Déclencheur manuel", "kind": "trigger", "config": {}}}]
    edges = []
    previous = "trigger-1"
    for index, action in enumerate(actions or []):
        node_id = f"action-{index + 1}"
        nodes.append({"id": node_id, "type": "action", "position": {"x": 80 + (index + 1) * 220, "y": 120}, "data": {"label": action, "kind": "action", "config": {}}})
        edges.append({"id": f"e-{previous}-{node_id}", "source": previous, "target": node_id})
        previous = node_id
    return {"nodes": nodes, "edges": edges}


def _ordered_nodes(definition: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = normalize_definition(definition)
    nodes = {node["id"]: node for node in normalized["nodes"]}
    outgoing: dict[str, list[str]] = {}
    incoming: set[str] = set()
    for edge in normalized["edges"]:
        outgoing.setdefault(edge["source"], []).append(edge["target"])
        incoming.add(edge["target"])
    trigger = next((node for node in nodes.values() if node["type"] == "trigger" or node["data"]["kind"] == "trigger"), None)
    current = trigger["id"] if trigger else next((node_id for node_id in nodes if node_id not in incoming), None)
    ordered, seen = [], set()
    while current and current in nodes and current not in seen:
        ordered.append(nodes[current])
        seen.add(current)
        targets = outgoing.get(current) or []
        current = targets[0] if targets else None
    ordered.extend(node for node_id, node in nodes.items() if node_id not in seen)
    return ordered


def derive_trigger_actions(definition: dict[str, Any]) -> tuple[str, list[str]]:
    trigger = "Manuel"
    actions: list[str] = []
    for node in _ordered_nodes(definition):
        if node["type"] == "trigger" or node["data"]["kind"] == "trigger":
            trigger = node["data"]["label"]
        else:
            actions.append(node["data"]["label"])
    return trigger, actions


def derive_action_steps(definition: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"key": node["id"], "action": node["data"]["label"], "config": node["data"]["config"]}
        for node in _ordered_nodes(definition)
        if node["type"] != "trigger" and node["data"]["kind"] != "trigger"
    ]
