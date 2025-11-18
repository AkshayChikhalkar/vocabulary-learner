"""Data update coordinator for Vocabulary Learner."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ENABLE_API,
    CONF_NOTIFICATION_ENTITY,
    CONF_NOTIFICATION_FREQUENCY,
    CONF_QUIET_HOURS_END,
    CONF_QUIET_HOURS_START,
    CONF_TARGET_LANGUAGE,
    CONF_VOCAB_FILE,
    CONF_WORDS_PER_DAY,
    DEFAULT_NOTIFICATION_FREQUENCY,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_WORDS_PER_DAY,
)
from .storage import VocabularyLearnerStorage
from .vocabulary.api_client import VocabularyAPIClient
from .vocabulary.parser import VocabularyParser
from .vocabulary.spaced_repetition import SpacedRepetition
from .vocabulary.word_manager import WordManager

_LOGGER = logging.getLogger(__name__)


class VocabularyLearnerCoordinator(DataUpdateCoordinator):
    """Coordinator for Vocabulary Learner integration."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, storage: VocabularyLearnerStorage
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Vocabulary Learner",
            update_interval=timedelta(minutes=5),  # Update every 5 minutes
        )
        self.hass = hass
        self.entry = entry
        self.storage = storage
        self.word_manager = WordManager(storage)
        self.api_client = VocabularyAPIClient()
        self.parser = VocabularyParser()
        self.spaced_repetition = SpacedRepetition()

        self.current_word: dict[str, Any] | None = None
        self._notification_timer: Any = None
        self._last_notification: datetime | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from storage and update current word."""
        try:
            # Load vocabulary and progress
            await self.word_manager.load_vocabulary()

            # If no vocabulary loaded, try to load it
            vocabulary = self.word_manager.get_vocabulary()
            if not vocabulary:
                await self._load_vocabulary()
                await self.word_manager.load_vocabulary()
                vocabulary = self.word_manager.get_vocabulary()

            # Get configuration
            config = self.entry.data
            words_per_day = config.get(CONF_WORDS_PER_DAY, DEFAULT_WORDS_PER_DAY)
            target_lang = config.get(CONF_TARGET_LANGUAGE, DEFAULT_TARGET_LANGUAGE)

            # Get next word for review
            next_word = await self._get_next_word(words_per_day)

            if next_word:
                self.current_word = next_word
            else:
                self.current_word = None

            # Update statistics
            stats = self.word_manager.get_statistics()
            self.storage.set_statistics(stats)
            await self.storage.async_save()

            return {
                "current_word": self.current_word,
                "statistics": stats,
            }

        except Exception as exc:
            _LOGGER.error("Error updating vocabulary data: %s", exc)
            raise UpdateFailed(f"Error updating vocabulary data: {exc}") from exc

    async def _get_next_word(self, max_words: int) -> dict[str, Any] | None:
        """Get next word for review using spaced repetition."""
        vocabulary = self.word_manager.get_vocabulary()

        if not vocabulary:
            # Try to load vocabulary from file or API
            await self._load_vocabulary()
            vocabulary = self.word_manager.get_vocabulary()

        if not vocabulary:
            return None

        # Prepare words with progress for spaced repetition
        words_with_progress = []
        for entry in vocabulary:
            progress = self.word_manager.get_progress(entry.word)
            if progress:
                word_data = {
                    "word": entry.word,
                    "translation": entry.translation,
                    "example": entry.example,
                    "synonyms": entry.synonyms,
                    "etymology": entry.etymology,
                    "progress": progress.to_dict(),
                }
            else:
                word_data = {
                    "word": entry.word,
                    "translation": entry.translation,
                    "example": entry.example,
                    "synonyms": entry.synonyms,
                    "etymology": entry.etymology,
                    "progress": {
                        "status": "unknown",
                        "review_count": 0,
                        "easiness": 2.5,
                        "interval": 1,
                    },
                }
            words_with_progress.append(word_data)

        # Get words for review using spaced repetition
        review_words = self.spaced_repetition.get_words_for_review(
            words_with_progress, max_words
        )

        if review_words:
            return review_words[0]

        return None

    async def _load_vocabulary(self) -> None:
        """Load vocabulary from file or API."""
        config = self.entry.data
        vocab_file = config.get(CONF_VOCAB_FILE)
        enable_api = config.get(CONF_ENABLE_API, True)
        target_lang = config.get(CONF_TARGET_LANGUAGE, DEFAULT_TARGET_LANGUAGE)

        vocabulary_entries = []

        # Try to load from user-provided file first
        if vocab_file and vocab_file.strip():
            try:
                # Resolve file path relative to config directory
                config_dir = Path(self.hass.config.config_dir)
                file_path = config_dir / vocab_file

                if file_path.exists():
                    entries = await self.parser.parse_file(file_path)
                    vocabulary_entries.extend(entries)
                    _LOGGER.info("Loaded %d words from user file: %s", len(entries), file_path)
                else:
                    _LOGGER.warning("Vocabulary file not found: %s", file_path)
            except Exception as exc:
                _LOGGER.error("Error loading vocabulary file: %s", exc)

        # If no vocabulary loaded, try default file
        if not vocabulary_entries:
            try:
                # Get path to integration directory
                integration_dir = Path(__file__).parent
                default_file = integration_dir / "vocab_default.csv"
                
                if default_file.exists():
                    entries = await self.parser.parse_file(default_file)
                    vocabulary_entries.extend(entries)
                    _LOGGER.info("Loaded %d words from default vocabulary file", len(entries))
                else:
                    _LOGGER.warning("Default vocabulary file not found: %s", default_file)
            except Exception as exc:
                _LOGGER.error("Error loading default vocabulary file: %s", exc)

        # If no vocabulary loaded and API is enabled, fetch from API
        if not vocabulary_entries and enable_api:
            _LOGGER.info("No vocabulary file provided, API fallback not implemented for automatic word fetching")
            # Note: API would need a word list source - this could be implemented
            # with a predefined word list or user-provided initial words

        if vocabulary_entries:
            await self.word_manager.save_vocabulary(vocabulary_entries)

    async def mark_word_known(self, word: str) -> None:
        """Mark a word as known."""
        self.word_manager.mark_known(word)
        progress = self.word_manager.get_progress(word)
        if progress:
            # Update with spaced repetition
            updated_progress = self.spaced_repetition.update_word_progress(
                progress.to_dict(), quality=5  # Perfect recall
            )
            self.word_manager.update_progress(word, updated_progress)
        await self.word_manager.save_progress()
        await self.async_request_refresh()

    async def mark_word_unknown(self, word: str) -> None:
        """Mark a word as unknown."""
        self.word_manager.mark_unknown(word)
        progress = self.word_manager.get_progress(word)
        if progress:
            # Update with spaced repetition
            updated_progress = self.spaced_repetition.update_word_progress(
                progress.to_dict(), quality=0  # Incorrect
            )
            self.word_manager.update_progress(word, updated_progress)
        await self.word_manager.save_progress()
        await self.async_request_refresh()

    async def get_next_word(self) -> dict[str, Any] | None:
        """Get next word for review."""
        config = self.entry.data
        words_per_day = config.get(CONF_WORDS_PER_DAY, DEFAULT_WORDS_PER_DAY)
        return await self._get_next_word(words_per_day)

    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics."""
        return self.word_manager.get_statistics()

    async def reset_progress(self) -> None:
        """Reset all learning progress."""
        await self.word_manager.reset_progress()
        await self.async_request_refresh()

    async def export_progress(self) -> dict[str, Any]:
        """Export progress data."""
        return await self.storage.async_export()

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and set up notifications."""
        await super().async_config_entry_first_refresh()
        await self._setup_notifications()

    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        config = self.entry.data
        quiet_start = config.get(CONF_QUIET_HOURS_START, "22:00")
        quiet_end = config.get(CONF_QUIET_HOURS_END, "08:00")

        try:
            now = dt_util.now().time()
            start_time = datetime.strptime(quiet_start, "%H:%M").time()
            end_time = datetime.strptime(quiet_end, "%H:%M").time()

            # Handle quiet hours that span midnight
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:
                return now >= start_time or now <= end_time
        except Exception as exc:
            _LOGGER.error("Error checking quiet hours: %s", exc)
            return False

    async def _setup_notifications(self) -> None:
        """Set up notification scheduling."""
        config = self.entry.data
        frequency = config.get(CONF_NOTIFICATION_FREQUENCY, DEFAULT_NOTIFICATION_FREQUENCY)
        notification_entity = config.get(CONF_NOTIFICATION_ENTITY)

        if not notification_entity:
            _LOGGER.debug("No notification entity configured")
            return

        # Schedule periodic notifications
        async def send_notification():
            """Send vocabulary notification."""
            # Check quiet hours
            if self._is_quiet_hours():
                _LOGGER.debug("Skipping notification during quiet hours")
                return

            if self.current_word:
                word = self.current_word.get("word", "")
                translation = self.current_word.get("translation", "")
                example = self.current_word.get("example", "")

                message = f"📚 {word}\n{translation}"
                if example:
                    message += f"\n\nExample: {example}"

                try:
                    # Extract service name from entity (e.g., "mobile_app_phone" -> "mobile_app_phone")
                    service_name = notification_entity
                    if "." in notification_entity:
                        service_name = notification_entity.split(".")[-1]

                    await self.hass.services.async_call(
                        "notify",
                        service_name,
                        {
                            "message": message,
                            "title": "Vocabulary Learner",
                            "data": {
                                "word": word,
                                "translation": translation,
                                "example": example,
                            },
                        },
                    )
                    self._last_notification = datetime.now()
                    _LOGGER.debug("Sent vocabulary notification: %s", word)
                except Exception as exc:
                    _LOGGER.error("Error sending notification: %s", exc)

        # Schedule first notification
        async def schedule_next():
            """Schedule next notification."""
            await send_notification()
            # Schedule next one
            self.hass.loop.call_later(
                frequency * 60,  # Convert minutes to seconds
                lambda: self.hass.async_create_task(schedule_next()),
            )

        # Start notification loop after a short delay
        self.hass.loop.call_later(
            60,  # Wait 1 minute before first notification
            lambda: self.hass.async_create_task(schedule_next()),
        )
        _LOGGER.info("Notification system initialized (frequency: %d minutes)", frequency)

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and close API clients."""
        await self.api_client.close()
        await super().async_shutdown()

