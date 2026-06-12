"""Deprecated compatibility shim.

The application does not support disabling all safety policies. Use
app.services.safety_override.SafetyOverrideService for test-only simulated sends.
"""

from enum import StrEnum


class SafetyBypassMode(StrEnum):
    STRICT = "strict"


class SafetyBypassState:
    @classmethod
    def is_active(cls) -> bool:
        return False

    @classmethod
    def current_mode(cls) -> SafetyBypassMode:
        return SafetyBypassMode.STRICT

    @classmethod
    def enable(cls, *args, **kwargs) -> None:
        raise RuntimeError("Full safety bypass is not supported")

    @classmethod
    def disable(cls) -> None:
        return None

    @classmethod
    def reset(cls) -> None:
        return None

    @classmethod
    def snapshot(cls) -> dict:
        return {
            "mode": SafetyBypassMode.STRICT.value,
            "active": False,
            "enabled_by": None,
            "reason": None,
            "enabled_at": None,
            "expires_at": None,
        }
