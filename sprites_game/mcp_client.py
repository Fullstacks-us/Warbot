from typing import Any, Dict, List, Tuple

class MCPClient:
    """Minimal interface to a master control program (MCP)."""

    def __init__(self) -> None:
        self.log: List[Tuple[str, Any]] = []

    def register_npc(self, name: str, data: Dict[str, Any]) -> None:
        self.log.append(("npc", name, data))

    def register_environment(self, env_id: str, data: Dict[str, Any]) -> None:
        self.log.append(("environment", env_id, data))

    def register_pathway(self, path_id: str, points: List[Tuple[int, int]]) -> None:
        self.log.append(("pathway", path_id, points))

    def trigger_event(self, event: str, data: Dict[str, Any]) -> None:
        self.log.append(("trigger", event, data))
