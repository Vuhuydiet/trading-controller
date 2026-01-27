"""
Structure Learner - Persistent storage and learning for HTML patterns

This module:
1. Stores learned patterns in the database
2. Tracks extraction success/failure rates per domain
3. Provides pattern retrieval for the adaptive parser
4. Handles pattern versioning when sites change structure
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import Field, Session, SQLModel, col, select

logger = logging.getLogger(__name__)


class LearnedPattern(SQLModel, table=True):
    """Database model for storing learned HTML patterns"""

    __tablename__ = "learned_html_patterns"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(index=True, unique=True)

    # Selectors stored as JSON
    title_selectors: str = Field(default="[]")  # JSON array
    content_selectors: str = Field(default="[]")
    author_selectors: str = Field(default="[]")
    date_selectors: str = Field(default="[]")

    # Statistics
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None

    # Metadata
    extraction_method: str = Field(default="unknown")
    confidence: float = Field(default=0.0)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_title_selectors(self) -> List[str]:
        return json.loads(self.title_selectors)

    def get_content_selectors(self) -> List[str]:
        return json.loads(self.content_selectors)

    def get_author_selectors(self) -> List[str]:
        return json.loads(self.author_selectors)

    def get_date_selectors(self) -> List[str]:
        return json.loads(self.date_selectors)

    def set_selectors(
        self,
        title: List[str] = None,
        content: List[str] = None,
        author: List[str] = None,
        date: List[str] = None,
    ):
        if title is not None:
            self.title_selectors = json.dumps(title)
        if content is not None:
            self.content_selectors = json.dumps(content)
        if author is not None:
            self.author_selectors = json.dumps(author)
        if date is not None:
            self.date_selectors = json.dumps(date)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for the adaptive parser"""
        return {
            "domain": self.domain,
            "title_selectors": self.get_title_selectors(),
            "content_selectors": self.get_content_selectors(),
            "author_selectors": self.get_author_selectors(),
            "date_selectors": self.get_date_selectors(),
            "confidence": self.confidence,
            "version": self.version,
        }


class ExtractionLog(SQLModel, table=True):
    """Log of extraction attempts for analysis"""

    __tablename__ = "extraction_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(index=True)
    url: str
    success: bool
    extraction_method: str
    confidence: float
    content_length: int = Field(default=0)
    error_message: Optional[str] = None
    selectors_used: str = Field(default="{}")  # JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StructureLearner:
    """
    Manages learning and storage of HTML patterns.
    """

    def __init__(self, session: Session):
        self.session = session
        self._pattern_cache: Dict[str, Dict[str, Any]] = {}

    def get_patterns_for_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get learned patterns for a domain"""
        # Check cache first
        if domain in self._pattern_cache:
            return self._pattern_cache[domain]

        # Query database
        stmt = select(LearnedPattern).where(LearnedPattern.domain == domain)
        pattern = self.session.exec(stmt).first()

        if pattern:
            pattern_dict = pattern.to_dict()
            self._pattern_cache[domain] = pattern_dict
            return pattern_dict

        return None

    def get_all_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all learned patterns (for initializing parser)"""
        stmt = select(LearnedPattern)
        patterns = self.session.exec(stmt).all()

        return {p.domain: p.to_dict() for p in patterns}

    def save_pattern(
        self,
        domain: str,
        pattern_data: Dict[str, Any],
        success: bool = True,
    ) -> LearnedPattern:
        """Save or update a learned pattern"""
        # Find existing pattern
        stmt = select(LearnedPattern).where(LearnedPattern.domain == domain)
        existing = self.session.exec(stmt).first()

        if existing:
            # Update existing pattern
            self._update_pattern(existing, pattern_data, success)
            pattern = existing
        else:
            # Create new pattern
            pattern = LearnedPattern(
                domain=domain,
                extraction_method=pattern_data.get("extraction_method", "unknown"),
                confidence=pattern_data.get("confidence", 0.0),
            )
            pattern.set_selectors(
                title=pattern_data.get("title_selectors", []),
                content=pattern_data.get("content_selectors", []),
                author=pattern_data.get("author_selectors", []),
                date=pattern_data.get("date_selectors", []),
            )
            if success:
                pattern.success_count = 1
                pattern.last_success_at = datetime.now(timezone.utc)
            self.session.add(pattern)

        self.session.commit()
        self.session.refresh(pattern)

        # Update cache
        self._pattern_cache[domain] = pattern.to_dict()

        return pattern

    def _update_pattern(
        self,
        pattern: LearnedPattern,
        new_data: Dict[str, Any],
        success: bool,
    ):
        """Update existing pattern with new data"""
        now = datetime.now(timezone.utc)

        if success:
            pattern.success_count += 1
            pattern.last_success_at = now

            # Merge selectors (keep unique, limit to 5)
            for key in ["title", "content", "author", "date"]:
                new_selectors = new_data.get(f"{key}_selectors", [])
                if new_selectors:
                    existing = getattr(pattern, f"get_{key}_selectors")()
                    merged = list(dict.fromkeys(new_selectors + existing))[:5]
                    pattern.set_selectors(**{key: merged})

            # Update confidence (weighted average favoring new)
            new_conf = new_data.get("confidence", pattern.confidence)
            pattern.confidence = (pattern.confidence * 0.3 + new_conf * 0.7)

        else:
            pattern.failure_count += 1
            pattern.last_failure_at = now

            # Check if pattern might be stale
            if pattern.failure_count > pattern.success_count * 0.5:
                # Pattern is failing often, reduce confidence
                pattern.confidence *= 0.8
                logger.warning(
                    f"Pattern for {pattern.domain} has high failure rate, "
                    f"reducing confidence to {pattern.confidence:.2f}"
                )

        pattern.updated_at = now

    def log_extraction(
        self,
        domain: str,
        url: str,
        success: bool,
        method: str,
        confidence: float,
        content_length: int = 0,
        error: Optional[str] = None,
        selectors: Optional[Dict[str, Any]] = None,
    ):
        """Log an extraction attempt"""
        log = ExtractionLog(
            domain=domain,
            url=url,
            success=success,
            extraction_method=method,
            confidence=confidence,
            content_length=content_length,
            error_message=error,
            selectors_used=json.dumps(selectors or {}),
        )
        self.session.add(log)
        self.session.commit()

    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get extraction statistics for a domain"""
        stmt = select(LearnedPattern).where(LearnedPattern.domain == domain)
        pattern = self.session.exec(stmt).first()

        if not pattern:
            return {"domain": domain, "has_pattern": False}

        total = pattern.success_count + pattern.failure_count
        success_rate = pattern.success_count / total if total > 0 else 0

        return {
            "domain": domain,
            "has_pattern": True,
            "success_count": pattern.success_count,
            "failure_count": pattern.failure_count,
            "success_rate": success_rate,
            "confidence": pattern.confidence,
            "version": pattern.version,
            "last_success": pattern.last_success_at.isoformat() if pattern.last_success_at else None,
            "last_failure": pattern.last_failure_at.isoformat() if pattern.last_failure_at else None,
        }

    def invalidate_pattern(self, domain: str):
        """Mark a pattern as invalid (structure changed)"""
        stmt = select(LearnedPattern).where(LearnedPattern.domain == domain)
        pattern = self.session.exec(stmt).first()

        if pattern:
            pattern.version += 1
            pattern.confidence = 0.0
            pattern.updated_at = datetime.now(timezone.utc)
            self.session.commit()

            # Clear cache
            if domain in self._pattern_cache:
                del self._pattern_cache[domain]

            logger.info(f"Invalidated pattern for {domain}, version now {pattern.version}")

    def cleanup_old_logs(self, days: int = 30):
        """Remove old extraction logs"""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Using raw SQL for bulk delete
        stmt = select(ExtractionLog).where(ExtractionLog.created_at < cutoff)
        old_logs = self.session.exec(stmt).all()

        for log in old_logs:
            self.session.delete(log)

        self.session.commit()
        logger.info(f"Cleaned up {len(old_logs)} old extraction logs")


def get_structure_learner(session: Session) -> StructureLearner:
    """Factory function for structure learner"""
    return StructureLearner(session)
