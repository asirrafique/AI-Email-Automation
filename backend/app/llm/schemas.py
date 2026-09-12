
from typing import Optional

from pydantic import BaseModel, Field


class LeadClassification(BaseModel):
    """Structured result returned by the email classifier."""

    is_sales_lead: bool = Field(
        description=(
            "Whether the email represents a genuine sales lead "
            "or business opportunity."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1.",
    )

    lead_name: Optional[str] = Field(
        default=None,
        description="Name of the potential lead if identifiable.",
    )

    company: Optional[str] = Field(
        default=None,
        description=(
            "Company or organization associated with the lead "
            "if identifiable."
        ),
    )

    intent: str = Field(
        description="Short description of what the sender wants.",
    )

    requirements: Optional[str] = Field(
        default=None,
        description=(
            "Specific requirements, services, products, budget, "
            "timeline, or needs mentioned by the sender."
        ),
    )

    reason: str = Field(
        description=(
            "Brief explanation for why the email was or was not "
            "classified as a sales lead."
        ),
    )


class GeneratedReply(BaseModel):
    """Structured reply generated for a sales lead."""

    subject: str = Field(
        description="Email subject for the reply.",
    )

    body: str = Field(
        description="Professional and personalized email reply.",
    )


class SendDraftRequest(BaseModel):
    """Request body used to send an existing Gmail draft."""

    draft_id: str = Field(
        min_length=1,
        description="The Gmail draft ID that should be sent.",
    )