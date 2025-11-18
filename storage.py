"""Storage handler for Vocabulary Learner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


class VocabularyLearnerStorage:
    """Handle storage for Vocabulary Learner."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize storage."""
        self.hass = hass
        self.entry_id = entry_id
        self.store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        self.data: dict[str, Any] = {}

    async def async_load(self) -> dict[str, Any]:
        """Load data from storage."""
        try:
            self.data = await self.store.async_load() or {}
            _LOGGER.debug("Loaded storage data: %s", list(self.data.keys()))
            return self.data
        except Exception as exc:
            _LOGGER.error("Error loading storage: %s", exc)
            self.data = {}
            return self.data

    async def async_save(self) -> None:
        """Save data to storage."""
        try:
            await self.store.async_save(self.data)
            _LOGGER.debug("Saved storage data")
        except Exception as exc:
            _LOGGER.error("Error saving storage: %s", exc)
            raise

    def get_vocabulary(self) -> list[dict[str, Any]]:
        """Get vocabulary list."""
        return self.data.get("vocabulary", [])

    def set_vocabulary(self, vocabulary: list[dict[str, Any]]) -> None:
        """Set vocabulary list."""
        self.data["vocabulary"] = vocabulary

    def get_progress(self) -> dict[str, Any]:
        """Get learning progress."""
        return self.data.get("progress", {})

    def set_progress(self, progress: dict[str, Any]) -> None:
        """Set learning progress."""
        self.data["progress"] = progress

    def get_word_progress(self, word: str) -> dict[str, Any] | None:
        """Get progress for a specific word."""
        progress = self.get_progress()
        return progress.get(word)

    def set_word_progress(self, word: str, word_data: dict[str, Any]) -> None:
        """Set progress for a specific word."""
        if "progress" not in self.data:
            self.data["progress"] = {}
        self.data["progress"][word] = word_data

    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics."""
        return self.data.get("statistics", {
            "total_words": 0,
            "known_words": 0,
            "learning_words": 0,
            "unknown_words": 0,
            "words_today": 0,
            "streak_days": 0,
            "last_study_date": None,
        })

    def set_statistics(self, statistics: dict[str, Any]) -> None:
        """Set learning statistics."""
        self.data["statistics"] = statistics

    def update_statistics(self) -> None:
        """Update statistics from current progress."""
        vocabulary = self.get_vocabulary()
        progress = self.get_progress()

        total_words = len(vocabulary)
        known_words = 0
        learning_words = 0
        unknown_words = 0

        for word_entry in vocabulary:
            word = word_entry.get("word", "")
            word_progress = progress.get(word, {})
            status = word_progress.get("status", "unknown")

            if status == "known":
                known_words += 1
            elif status == "learning":
                learning_words += 1
            else:
                unknown_words += 1

        stats = self.get_statistics()
        stats["total_words"] = total_words
        stats["known_words"] = known_words
        stats["learning_words"] = learning_words
        stats["unknown_words"] = unknown_words

        self.set_statistics(stats)

    def get_settings(self) -> dict[str, Any]:
        """Get user settings."""
        return self.data.get("settings", {})

    def set_settings(self, settings: dict[str, Any]) -> None:
        """Set user settings."""
        self.data["settings"] = settings

    async def async_export(self) -> dict[str, Any]:
        """Export all data for backup."""
        await self.async_load()
        return {
            "vocabulary": self.get_vocabulary(),
            "progress": self.get_progress(),
            "statistics": self.get_statistics(),
            "settings": self.get_settings(),
        }

    async def async_import(self, data: dict[str, Any]) -> None:
        """Import data from backup."""
        if "vocabulary" in data:
            self.set_vocabulary(data["vocabulary"])
        if "progress" in data:
            self.set_progress(data["progress"])
        if "statistics" in data:
            self.set_statistics(data["statistics"])
        if "settings" in data:
            self.set_settings(data["settings"])
        await self.async_save()

    async def async_reset_progress(self) -> None:
        """Reset all learning progress."""
        self.data["progress"] = {}
        stats = self.get_statistics()
        stats["known_words"] = 0
        stats["learning_words"] = 0
        stats["unknown_words"] = stats["total_words"]
        stats["words_today"] = 0
        self.set_statistics(stats)
        await self.async_save()

