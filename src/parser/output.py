from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class RCAReport(BaseModel):
    root_cause: str = Field(description="The identified root cause of the incident")
    contributing_factors: list[str] = Field(description="List of contributing factors")
    impact: str = Field(description="Business and technical impact summary")
    timeline: str = Field(description="Brief sequence of events leading to the incident")
    immediate_actions: list[str] = Field(description="Steps already taken or needed immediately")
    prevention: list[str] = Field(description="Long-term prevention recommendations")
    confidence: str = Field(description="Confidence level: HIGH, MEDIUM, or LOW, with reason")


class FallbackReport(BaseModel):
    """Returned when the vector store returns 0 relevant results."""
    message: str = "No similar incidents or runbooks found in the knowledge base."
    raw_analysis: str = Field(description="Best-effort analysis based on the incident text alone")
    recommendation: str = "Add relevant runbooks or past incidents to the knowledge base."


def get_rca_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=RCAReport)


def get_fallback_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=FallbackReport)
