import uuid
from dataclasses import dataclass


@dataclass
class MockPaymentResult:
    id: int
    provider_ref: str
    status: str


class MockPaymentProvider:
    """Mock external payment provider to simulate create/confirm/status."""

    # PUBLIC_INTERFACE
    def create(self, amount: float) -> str:
        """Create a payment intent and return provider reference."""
        return f"mock_{uuid.uuid4()}"

    # PUBLIC_INTERFACE
    def status(self, provider_ref: str) -> str:
        """Return mocked status (always pending or succeeded randomly could be implemented)."""
        return "pending"

    # PUBLIC_INTERFACE
    def confirm(self, provider_ref: str) -> str:
        """Confirm mocked payment (always succeeded)."""
        return "succeeded"
