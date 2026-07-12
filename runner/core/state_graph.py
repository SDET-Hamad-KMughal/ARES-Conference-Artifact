"""Lightweight state graph for the ARES conference artifact."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StateNode:
    """
    Represents one observed application state.
    """

    state_id: str
    url: str
    title: str
    timestamp: str
    dom_summary: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateEdge:
    """
    Represents one transition between two application states.
    """

    source_state_id: str
    target_state_id: str
    action_type: str
    action_target: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateGraph:
    """
    Stores application states and transitions between them.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, StateNode] = {}
        self._edges: List[StateEdge] = []

    @staticmethod
    def _generate_state_id(
        url: str,
        title: str,
        dom_summary: Dict[str, Any],
    ) -> str:
        """
        Create a deterministic state identifier.

        The identifier is based on the URL, title, and DOM summary.
        """

        state_signature = {
            "url": url,
            "title": title,
            "dom_summary": dom_summary,
        }

        serialized_signature = json.dumps(
            state_signature,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            serialized_signature.encode("utf-8")
        ).hexdigest()[:16]

    def add_state(
        self,
        analysis: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateNode:
        """
        Add a DOM analysis result as a graph state.

        Existing states with the same deterministic identifier are reused.
        """

        url = analysis.get("url", "")
        title = analysis.get("title", "")
        dom_summary = analysis.get("summary", {})

        state_id = self._generate_state_id(
            url=url,
            title=title,
            dom_summary=dom_summary,
        )

        if state_id in self._nodes:
            return self._nodes[state_id]

        node = StateNode(
            state_id=state_id,
            url=url,
            title=title,
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
            dom_summary=dom_summary,
            metadata=metadata or {},
        )

        self._nodes[state_id] = node
        return node

    def add_transition(
        self,
        source_state_id: str,
        target_state_id: str,
        action_type: str,
        action_target: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateEdge:
        """
        Add a directed transition between two existing states.
        """

        if source_state_id not in self._nodes:
            raise ValueError(
                f"Unknown source state: {source_state_id}"
            )

        if target_state_id not in self._nodes:
            raise ValueError(
                f"Unknown target state: {target_state_id}"
            )

        edge = StateEdge(
            source_state_id=source_state_id,
            target_state_id=target_state_id,
            action_type=action_type,
            action_target=action_target,
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
            metadata=metadata or {},
        )

        self._edges.append(edge)
        return edge

    def get_state(
        self,
        state_id: str,
    ) -> Optional[StateNode]:
        """
        Return a state by identifier.
        """

        return self._nodes.get(state_id)

    def summary(self) -> Dict[str, int]:
        """
        Return basic graph metrics.
        """

        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the graph into a JSON-serializable dictionary.
        """

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "summary": self.summary(),
            "nodes": [
                asdict(node)
                for node in self._nodes.values()
            ],
            "edges": [
                asdict(edge)
                for edge in self._edges
            ],
        }

    def save_json(
        self,
        output_path: str | Path,
    ) -> Path:
        """
        Save the state graph as formatted JSON.
        """

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                self.to_dict(),
                output_file,
                indent=2,
                ensure_ascii=False,
            )

        return path