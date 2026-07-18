"""AI recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import RecommendationServiceDep
from app.schemas.ai import (
    RecommendationFeedback,
    RecommendationRead,
    RecommendationRequest,
    RecommendedOutfit,
)
from app.services.recommendation_service import RecommendationNotFoundError
from app.services.storage import storage_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendedOutfit)
async def generate_recommendation(
    payload: RecommendationRequest, service: RecommendationServiceDep
) -> RecommendedOutfit:
    """Generate an outfit suggestion (AI when configured, else rule-based).

    Always returns a result — the rule-based stylist guarantees a response even
    with no API key or network access.
    """
    outfit, _record = await service.generate(
        payload, enrich_url=storage_service.public_url
    )
    return outfit


@router.post("/{rec_id}/feedback", response_model=RecommendationRead)
async def submit_feedback(
    rec_id: int, payload: RecommendationFeedback, service: RecommendationServiceDep
) -> RecommendationRead:
    """Record the user's response so future suggestions improve."""
    try:
        record = await service.record_feedback(rec_id, payload.status)
    except RecommendationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RecommendationRead.model_validate(record)
