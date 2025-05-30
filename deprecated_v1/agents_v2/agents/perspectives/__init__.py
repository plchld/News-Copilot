"""Perspective agents for Phase 2: Multi-Perspective Deep Dive"""

from .greek_perspective import GreekPerspectiveAgent
from .international_perspective import InternationalPerspectiveAgent
from .opposing_view import OpposingViewAgent
from .fact_verification import FactVerificationAgent

__all__ = [
    "GreekPerspectiveAgent",
    "InternationalPerspectiveAgent", 
    "OpposingViewAgent",
    "FactVerificationAgent"
]