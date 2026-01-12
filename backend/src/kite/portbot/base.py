import abc
from typing import Any, Dict, Optional


class Agent(abc.ABC):
    """Abstract base class for all agents.

    Agents encapsulate a single responsibility (login, portfolio, chat, etc.)
    and expose a simple async API the orchestrator can call.
    """

    name: str = "agent"

    def __init__(self, shared_state: Optional[Dict[str, Any]] = None) -> None:
        self.shared_state: Dict[str, Any] = shared_state or {}

    @abc.abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Run the agent's main action."""
        raise NotImplementedError

class RequiresLoginError(Exception):
    """Raised when a Zerodha/Kite session is required but not available/valid."""
    pass





# # src/portbot/base.py

# class RequiresLoginError(Exception):
#     """Raised when a session is missing or invalid and login is required."""
#     pass