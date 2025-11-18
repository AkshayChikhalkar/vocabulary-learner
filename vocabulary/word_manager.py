"""Word management for tracking known/unknown words and metadata."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

# Word status constants
WORD_STATUS_UNKNOWN = "unknown"
WORD_STATUS_LEARNING = "learning"
WORD_STATUS_KNOWN = "known"
from .parser import VocabularyEntry

_LOGGER = logging.getLogger(__name__)


class WordProgress:
    """Tracks progress for a single word."""

    def __init__(
        self,
        word: str,
        status: str = WORD_STATUS_UNKNOWN,
        review_count: int = 0,
        last_review: datetime | None = None,
        next_review: datetime | None = None,
        easiness: float = 2.5,
        interval: int = 1,
        consecutive_correct: int = 0,
        consecutive_incorrect: int = 0,
    ) -> None:
        """Initialize word progress."""
        self.word = word
        self.status = status
        self.review_count = review_count
        self.last_review = last_review
        self.next_review = next_review
        self.easiness = easiness
        self.interval = interval
        self.consecutive_correct = consecutive_correct
        self.consecutive_incorrect = consecutive_incorrect

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "word": self.word,
            "status": self.status,
            "review_count": self.review_count,
            "last_review": (
                self.last_review.isoformat() if self.last_review else None
            ),
            "next_review": (
                self.next_review.isoformat() if self.next_review else None
            ),
            "easiness": self.easiness,
            "interval": self.interval,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_incorrect": self.consecutive_incorrect,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WordProgress:
        """Create from dictionary."""
        last_review = None
        if data.get("last_review"):
            try:
                last_review = datetime.fromisoformat(data["last_review"])
            except (ValueError, TypeError):
                pass

        next_review = None
        if data.get("next_review"):
            try:
                next_review = datetime.fromisoformat(data["next_review"])
            except (ValueError, TypeError):
                pass

        return cls(
            word=data.get("word", ""),
            status=data.get("status", WORD_STATUS_UNKNOWN),
            review_count=data.get("review_count", 0),
            last_review=last_review,
            next_review=next_review,
            easiness=data.get("easiness", 2.5),
            interval=data.get("interval", 1),
            consecutive_correct=data.get("consecutive_correct", 0),
            consecutive_incorrect=data.get("consecutive_incorrect", 0),
        )


class WordManager:
    """Manages vocabulary words and their progress."""

    def __init__(self, storage: Any) -> None:
        """Initialize word manager."""
        self.storage = storage
        self._vocabulary: list[VocabularyEntry] = []
        self._progress: dict[str, WordProgress] = {}

    async def load_vocabulary(self) -> None:
        """Load vocabulary from storage."""
        vocab_data = self.storage.get_vocabulary()
        self._vocabulary = [
            VocabularyEntry.from_dict(entry) for entry in vocab_data
        ]

        progress_data = self.storage.get_progress()
        self._progress = {
            word: WordProgress.from_dict(data)
            for word, data in progress_data.items()
        }

        _LOGGER.info("Loaded %d vocabulary words", len(self._vocabulary))

    async def save_vocabulary(self, vocabulary: list[VocabularyEntry]) -> None:
        """Save vocabulary to storage."""
        self._vocabulary = vocabulary
        vocab_data = [entry.to_dict() for entry in vocabulary]
        self.storage.set_vocabulary(vocab_data)
        await self.storage.async_save()

        # Initialize progress for new words
        for entry in vocabulary:
            if entry.word not in self._progress:
                self._progress[entry.word] = WordProgress(word=entry.word)

        await self._save_progress()

    async def _save_progress(self) -> None:
        """Save progress to storage."""
        progress_data = {
            word: progress.to_dict()
            for word, progress in self._progress.items()
        }
        self.storage.set_progress(progress_data)
        self.storage.update_statistics()
        await self.storage.async_save()

    def get_vocabulary(self) -> list[VocabularyEntry]:
        """Get all vocabulary entries."""
        return self._vocabulary

    def get_word(self, word: str) -> VocabularyEntry | None:
        """Get a specific vocabulary entry."""
        for entry in self._vocabulary:
            if entry.word == word:
                return entry
        return None

    def get_progress(self, word: str) -> WordProgress | None:
        """Get progress for a word."""
        return self._progress.get(word)

    def mark_known(self, word: str) -> None:
        """Mark a word as known."""
        if word not in self._progress:
            self._progress[word] = WordProgress(word=word)

        progress = self._progress[word]
        progress.status = WORD_STATUS_KNOWN
        progress.last_review = datetime.now()
        progress.consecutive_correct += 1
        progress.consecutive_incorrect = 0

        _LOGGER.debug("Marked word as known: %s", word)

    def mark_unknown(self, word: str) -> None:
        """Mark a word as unknown."""
        if word not in self._progress:
            self._progress[word] = WordProgress(word=word)

        progress = self._progress[word]
        progress.status = WORD_STATUS_UNKNOWN
        progress.last_review = datetime.now()
        progress.consecutive_incorrect += 1
        progress.consecutive_correct = 0

        _LOGGER.debug("Marked word as unknown: %s", word)

    def mark_learning(self, word: str) -> None:
        """Mark a word as learning."""
        if word not in self._progress:
            self._progress[word] = WordProgress(word=word)

        progress = self._progress[word]
        if progress.status == WORD_STATUS_UNKNOWN:
            progress.status = WORD_STATUS_LEARNING
            progress.last_review = datetime.now()

        _LOGGER.debug("Marked word as learning: %s", word)

    def update_progress(
        self, word: str, progress_data: dict[str, Any]
    ) -> None:
        """Update progress for a word."""
        if word not in self._progress:
            self._progress[word] = WordProgress(word=word)

        progress = self._progress[word]
        for key, value in progress_data.items():
            if hasattr(progress, key):
                setattr(progress, key, value)

    async def save_progress(self) -> None:
        """Save all progress to storage."""
        await self._save_progress()

    def get_known_words(self) -> list[str]:
        """Get list of known words."""
        return [
            word
            for word, progress in self._progress.items()
            if progress.status == WORD_STATUS_KNOWN
        ]

    def get_unknown_words(self) -> list[str]:
        """Get list of unknown words."""
        return [
            word
            for word, progress in self._progress.items()
            if progress.status == WORD_STATUS_UNKNOWN
        ]

    def get_learning_words(self) -> list[str]:
        """Get list of words being learned."""
        return [
            word
            for word, progress in self._progress.items()
            if progress.status == WORD_STATUS_LEARNING
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics."""
        total = len(self._vocabulary)
        known = len(self.get_known_words())
        learning = len(self.get_learning_words())
        unknown = len(self.get_unknown_words())

        return {
            "total_words": total,
            "known_words": known,
            "learning_words": learning,
            "unknown_words": unknown,
            "progress_percent": (known / total * 100) if total > 0 else 0,
        }

    async def reset_progress(self) -> None:
        """Reset all progress."""
        self._progress = {}
        for entry in self._vocabulary:
            self._progress[entry.word] = WordProgress(word=entry.word)
        await self._save_progress()

