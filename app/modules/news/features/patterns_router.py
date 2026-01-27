"""
API Router for managing learned HTML patterns.

Provides endpoints to:
- View learned patterns
- Get extraction statistics
- Manually invalidate patterns
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.shared.infrastructure.db import get_session
from app.modules.news.infrastructure.structure_learner import (
    LearnedPattern,
    StructureLearner,
    get_structure_learner,
)

router = APIRouter()


class PatternResponse(BaseModel):
    """Response model for a learned pattern"""
    domain: str
    title_selectors: List[str]
    content_selectors: List[str]
    author_selectors: List[str]
    date_selectors: List[str]
    success_count: int
    failure_count: int
    confidence: float
    version: int
    extraction_method: str


class PatternStatsResponse(BaseModel):
    """Response model for pattern statistics"""
    domain: str
    has_pattern: bool
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    success_rate: Optional[float] = None
    confidence: Optional[float] = None
    version: Optional[int] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None


class AllPatternsResponse(BaseModel):
    """Response model for all patterns"""
    total: int
    patterns: List[PatternResponse]


@router.get(
    "/patterns",
    response_model=AllPatternsResponse,
    summary="Get All Learned Patterns",
    description="Get all learned HTML patterns from the database",
)
async def get_all_patterns(
    session: Session = Depends(get_session),
):
    """
    Get all learned HTML patterns.

    Returns patterns learned by the adaptive crawler for each domain.
    """
    learner = get_structure_learner(session)
    patterns_dict = learner.get_all_patterns()

    patterns = []
    for domain, pattern_data in patterns_dict.items():
        # Get full pattern from DB for statistics
        db_pattern = learner.get_patterns_for_domain(domain)
        if db_pattern:
            patterns.append(PatternResponse(
                domain=domain,
                title_selectors=pattern_data.get("title_selectors", []),
                content_selectors=pattern_data.get("content_selectors", []),
                author_selectors=pattern_data.get("author_selectors", []),
                date_selectors=pattern_data.get("date_selectors", []),
                success_count=0,  # Would need to query DB
                failure_count=0,
                confidence=pattern_data.get("confidence", 0.0),
                version=pattern_data.get("version", 1),
                extraction_method="adaptive",
            ))

    return AllPatternsResponse(total=len(patterns), patterns=patterns)


@router.get(
    "/patterns/{domain}",
    response_model=PatternStatsResponse,
    summary="Get Pattern Statistics",
    description="Get extraction statistics for a specific domain",
)
async def get_pattern_stats(
    domain: str,
    session: Session = Depends(get_session),
):
    """
    Get extraction statistics for a domain.

    - **domain**: The domain to get stats for (e.g., www.coindesk.com)
    """
    learner = get_structure_learner(session)
    stats = learner.get_domain_stats(domain)
    return PatternStatsResponse(**stats)


@router.delete(
    "/patterns/{domain}",
    summary="Invalidate Pattern",
    description="Invalidate a learned pattern (when structure changes)",
)
async def invalidate_pattern(
    domain: str,
    session: Session = Depends(get_session),
):
    """
    Invalidate a learned pattern for a domain.

    Use this when you know the website structure has changed
    and the learned pattern is no longer valid.
    """
    learner = get_structure_learner(session)
    learner.invalidate_pattern(domain)

    return {"message": f"Pattern for {domain} has been invalidated"}


@router.post(
    "/patterns/cleanup",
    summary="Cleanup Old Logs",
    description="Remove old extraction logs to save database space",
)
async def cleanup_logs(
    days: int = Query(default=30, ge=1, le=365, description="Keep logs newer than X days"),
    session: Session = Depends(get_session),
):
    """
    Clean up old extraction logs.

    - **days**: Keep logs newer than this many days (default: 30)
    """
    learner = get_structure_learner(session)
    learner.cleanup_old_logs(days=days)

    return {"message": f"Cleaned up extraction logs older than {days} days"}


@router.get(
    "/extraction-methods",
    summary="Get Extraction Methods",
    description="Get information about available extraction methods",
)
async def get_extraction_methods():
    """
    Get information about available content extraction methods.
    """
    return {
        "methods": [
            {
                "name": "learned_patterns",
                "description": "Uses previously learned CSS selectors for the domain",
                "confidence_range": "0.7-0.9",
                "speed": "fastest",
            },
            {
                "name": "semantic",
                "description": "Uses HTML5 semantic tags (article, main, etc.)",
                "confidence_range": "0.6-0.8",
                "speed": "fast",
            },
            {
                "name": "json_ld",
                "description": "Extracts from JSON-LD structured data",
                "confidence_range": "0.8-0.9",
                "speed": "fast",
            },
            {
                "name": "opengraph",
                "description": "Uses OpenGraph meta tags",
                "confidence_range": "0.5-0.7",
                "speed": "fast",
            },
            {
                "name": "density_analysis",
                "description": "Analyzes text density to find main content",
                "confidence_range": "0.3-0.7",
                "speed": "medium",
            },
            {
                "name": "basic_fallback",
                "description": "Collects all paragraph text",
                "confidence_range": "0.1-0.3",
                "speed": "fast",
            },
        ],
        "learning_enabled": True,
        "description": (
            "The adaptive parser tries methods in order of reliability, "
            "learning successful patterns for future use."
        ),
    }
