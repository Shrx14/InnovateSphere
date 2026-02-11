"""
Schemas for evidence-anchored idea generation (Segment 3.1)

Research-grade, citation-consistent, hallucination-resistant.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator



# ----------------------------
# Core Sections
# ----------------------------

class ProblemFormulation(BaseModel):
    context: str
    why_this_problem_matters: str
    evidence_basis: List[str]

    @field_validator("evidence_basis")
    def must_have_evidence(cls, v):
        if not v:
            raise ValueError("problem_formulation requires evidence")
        return v



class RelatedWorkSynthesis(BaseModel):
    common_approaches: str
    observed_limitations: str
    evidence_basis: List[str]

    @field_validator("evidence_basis")
    def must_have_evidence(cls, v):
        if not v:
            raise ValueError("related_work_synthesis requires evidence")
        return v



class ProposedContribution(BaseModel):
    core_idea: str
    what_is_new: str
    why_it_is_plausible: str
    evidence_basis: List[str]

    @field_validator("evidence_basis")
    def must_have_evidence(cls, v):
        if not v:
            raise ValueError("proposed_contribution requires evidence")
        return v



# ----------------------------
# Design & Tech
# ----------------------------

class Module(BaseModel):
    name: str
    responsibility: str
    justification: str


class SystemDesign(BaseModel):
    modules: List[Module]


class TechnologyChoice(BaseModel):
    technology: str
    role: str
    justification: str


class NoveltyPositioning(BaseModel):
    novelty_score: float = Field(..., ge=0, le=100)
    interpretation: str
    tradeoffs: str


# ----------------------------
# Evidence
# ----------------------------

class EvidenceSource(BaseModel):
    source_id: str
    title: str
    url: str
    source_type: str
    used_for: str

    @field_validator("source_type")
    def validate_source_type(cls, v):
        allowed = {"arxiv", "github", "web"}
        if v not in allowed:
            raise ValueError(f"Invalid source_type: {v}")
        return v



# ----------------------------
# Root Output
# ----------------------------

class GeneratedIdea(BaseModel):
    title: str
    problem_formulation: ProblemFormulation
    related_work_synthesis: RelatedWorkSynthesis
    proposed_contribution: ProposedContribution
    system_or_project_design: SystemDesign
    technology_choices: List[TechnologyChoice]
    novelty_positioning: NoveltyPositioning
    limitations_and_risks: List[str]
    evidence_sources: List[EvidenceSource]

    @field_validator("evidence_sources")
    def validate_sources(cls, v):
        if len(v) < 4:
            raise ValueError("At least 4 evidence sources required")
        if len({s.source_type for s in v}) < 2:
            raise ValueError("At least 2 distinct source types required")
        return v

    @model_validator(mode='after')
    def check_evidence_references(self):
        sources = self.evidence_sources or []
        source_ids = {s.source_id for s in sources}

        for section_name in (
            "problem_formulation",
            "related_work_synthesis",
            "proposed_contribution",
        ):
            section = getattr(self, section_name, None)
            if not section:
                continue
            for sid in section.evidence_basis:
                if sid not in source_ids:
                    raise ValueError(
                        f"Invalid evidence reference '{sid}' in {section_name}"
                    )
        return self



def validate_generated_idea(data: Dict[str, Any]) -> GeneratedIdea:
    return GeneratedIdea(**data)
