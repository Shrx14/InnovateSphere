"""
Idea generation module.
Provides functionality for generating project ideas with constraints and validation.
"""

from .generator import (
    generate_idea,
    check_evidence_sufficiency,
    check_hitl_guardrails,
)

from .schemas import (
    GeneratedIdea as GeneratedIdeaSchema,
    validate_generated_idea,
)
from .constraints import (
    build_hitl_constraints,
    is_rejected_pattern,
)

__all__ = [
    # Generator
    "generate_idea",
    "check_evidence_sufficiency",
    "check_hitl_guardrails",
    # Schemas
    "GeneratedIdeaSchema",
    "validate_generated_idea",
    # Constraints
    "build_hitl_constraints",
    "is_rejected_pattern",
]
