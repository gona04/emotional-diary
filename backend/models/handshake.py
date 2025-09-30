from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class HandshakeResult:
    sample_rate: int
    simulate: bool
    recognizer: Optional[Any]
    mode: str
    chat: bool

class HandshakeError(Exception):
    """Raised when the initial client handshake fails."""
    pass
