"""Spaced repetition algorithm (SM-2) for vocabulary learning."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

_LOGGER = logging.getLogger(__name__)

# SM-2 Algorithm constants
INITIAL_EASINESS = 2.5
MIN_EASINESS = 1.3
MIN_INTERVAL = 1  # days
MAX_INTERVAL = 365  # days


class SpacedRepetition:
    """Implements SM-2 spaced repetition algorithm."""

    @staticmethod
    def calculate_next_review(
        quality: int,
        easiness: float,
        interval: int,
        review_count: int,
    ) -> tuple[float, int, datetime]:
        """
        Calculate next review parameters using SM-2 algorithm.

        Args:
            quality: Quality of recall (0-5)
                    0-1: Incorrect response
                    2: Incorrect response after hesitation
                    3: Correct response with difficulty
                    4: Correct response after hesitation
                    5: Perfect recall
            easiness: Current easiness factor
            interval: Current interval in days
            review_count: Number of times word has been reviewed

        Returns:
            Tuple of (new_easiness, new_interval, next_review_date)
        """
        # Update easiness factor
        new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_easiness = max(MIN_EASINESS, new_easiness)

        # Calculate new interval
        if quality < 3:
            # Incorrect response - reset interval
            new_interval = MIN_INTERVAL
        else:
            # Correct response
            if review_count == 0:
                new_interval = 1
            elif review_count == 1:
                new_interval = 6
            else:
                new_interval = int(interval * new_easiness)

        # Clamp interval
        new_interval = max(MIN_INTERVAL, min(MAX_INTERVAL, new_interval))

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)

        return new_easiness, new_interval, next_review

    @staticmethod
    def is_due_for_review(next_review: datetime | None) -> bool:
        """Check if a word is due for review."""
        if next_review is None:
            return True
        return datetime.now() >= next_review

    @staticmethod
    def get_priority_score(
        next_review: datetime | None,
        review_count: int,
        easiness: float,
        status: str,
    ) -> float:
        """
        Calculate priority score for word selection.

        Higher score = higher priority for review.
        """
        score = 0.0

        # Never reviewed words get highest priority
        if review_count == 0:
            return 1000.0

        # Overdue words get high priority
        if next_review and SpacedRepetition.is_due_for_review(next_review):
            days_overdue = (datetime.now() - next_review).days
            score += 100.0 + (days_overdue * 10.0)

        # Lower easiness (harder words) get slightly higher priority
        score += (3.0 - easiness) * 5.0

        # Status-based priority
        if status == "unknown":
            score += 50.0
        elif status == "learning":
            score += 25.0

        # Words with more reviews get slightly lower priority
        score -= review_count * 0.1

        return score

    @staticmethod
    def update_word_progress(
        word_progress: dict[str, Any],
        quality: int,
    ) -> dict[str, Any]:
        """
        Update word progress after a review.

        Args:
            word_progress: Current word progress dictionary
            quality: Quality of recall (0-5)

        Returns:
            Updated word progress dictionary
        """
        easiness = word_progress.get("easiness", INITIAL_EASINESS)
        interval = word_progress.get("interval", MIN_INTERVAL)
        review_count = word_progress.get("review_count", 0)

        new_easiness, new_interval, next_review = SpacedRepetition.calculate_next_review(
            quality=quality,
            easiness=easiness,
            interval=interval,
            review_count=review_count,
        )

        # Update progress
        word_progress["easiness"] = new_easiness
        word_progress["interval"] = new_interval
        word_progress["next_review"] = next_review.isoformat()
        word_progress["last_review"] = datetime.now().isoformat()
        word_progress["review_count"] = review_count + 1

        # Update consecutive counts
        if quality >= 3:
            word_progress["consecutive_correct"] = word_progress.get("consecutive_correct", 0) + 1
            word_progress["consecutive_incorrect"] = 0
        else:
            word_progress["consecutive_incorrect"] = word_progress.get("consecutive_incorrect", 0) + 1
            word_progress["consecutive_correct"] = 0

        # Update status based on quality and review count
        if quality >= 4 and review_count >= 3:
            word_progress["status"] = "known"
        elif quality >= 3:
            word_progress["status"] = "learning"
        elif quality < 3:
            word_progress["status"] = "unknown"

        return word_progress

    @staticmethod
    def get_words_for_review(
        all_words: list[dict[str, Any]],
        max_words: int,
    ) -> list[dict[str, Any]]:
        """
        Get words that should be reviewed, sorted by priority.

        Args:
            all_words: List of all words with their progress
            max_words: Maximum number of words to return

        Returns:
            List of words sorted by review priority
        """
        # Calculate priority for each word
        words_with_priority = []
        for word_data in all_words:
            progress = word_data.get("progress", {})
            next_review_str = progress.get("next_review")
            next_review = None
            if next_review_str:
                try:
                    next_review = datetime.fromisoformat(next_review_str)
                except (ValueError, TypeError):
                    pass

            priority = SpacedRepetition.get_priority_score(
                next_review=next_review,
                review_count=progress.get("review_count", 0),
                easiness=progress.get("easiness", INITIAL_EASINESS),
                status=progress.get("status", "unknown"),
            )

            words_with_priority.append((priority, word_data))

        # Sort by priority (highest first)
        words_with_priority.sort(key=lambda x: x[0], reverse=True)

        # Return top words
        return [word_data for _, word_data in words_with_priority[:max_words]]

