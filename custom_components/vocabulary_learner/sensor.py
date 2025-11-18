"""Sensor platform for Vocabulary Learner."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CURRENT_WORD,
    ATTR_ETYMOLOGY,
    ATTR_EXAMPLE,
    ATTR_NEXT_REVIEW,
    ATTR_PROGRESS_PERCENT,
    ATTR_STREAK_DAYS,
    ATTR_SYNONYMS,
    ATTR_TRANSLATION,
    ATTR_WORDS_KNOWN,
    ATTR_WORDS_TODAY,
    ATTR_WORDS_TOTAL,
    DOMAIN,
)
from .coordinator import VocabularyLearnerCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTION = SensorEntityDescription(
    key="vocabulary_learner",
    name="Vocabulary Learner",
    icon="mdi:book-open-variant",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vocabulary Learner sensor from a config entry."""
    coordinator: VocabularyLearnerCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    async_add_entities([VocabularyLearnerSensor(coordinator, entry)])


class VocabularyLearnerSensor(
    CoordinatorEntity[VocabularyLearnerCoordinator], SensorEntity
):
    """Vocabulary Learner sensor entity."""

    def __init__(
        self, coordinator: VocabularyLearnerCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = SENSOR_DESCRIPTION
        self._attr_unique_id = f"{entry.entry_id}_vocabulary_learner"
        self._attr_name = entry.data.get("name", "Vocabulary Learner")

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        current_word = self.coordinator.current_word
        if current_word:
            return current_word.get("word", "idle")
        return "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        current_word = self.coordinator.current_word
        stats = self.coordinator.get_statistics()

        attrs: dict[str, Any] = {
            ATTR_WORDS_TOTAL: stats.get("total_words", 0),
            ATTR_WORDS_KNOWN: stats.get("known_words", 0),
            ATTR_WORDS_TODAY: stats.get("words_today", 0),
            ATTR_PROGRESS_PERCENT: stats.get("progress_percent", 0),
            ATTR_STREAK_DAYS: stats.get("streak_days", 0),
        }

        if current_word:
            attrs[ATTR_CURRENT_WORD] = current_word.get("word", "")
            attrs[ATTR_TRANSLATION] = current_word.get("translation", "")
            attrs[ATTR_EXAMPLE] = current_word.get("example")
            attrs[ATTR_SYNONYMS] = current_word.get("synonyms", [])
            attrs[ATTR_ETYMOLOGY] = current_word.get("etymology")

            # Next review time
            next_review = current_word.get("next_review")
            if next_review:
                try:
                    if isinstance(next_review, str):
                        next_review_dt = datetime.fromisoformat(next_review)
                    else:
                        next_review_dt = next_review
                    attrs[ATTR_NEXT_REVIEW] = next_review_dt.isoformat()
                except (ValueError, TypeError):
                    attrs[ATTR_NEXT_REVIEW] = None
            else:
                attrs[ATTR_NEXT_REVIEW] = None
        else:
            attrs[ATTR_CURRENT_WORD] = None
            attrs[ATTR_TRANSLATION] = None
            attrs[ATTR_EXAMPLE] = None
            attrs[ATTR_SYNONYMS] = []
            attrs[ATTR_ETYMOLOGY] = None
            attrs[ATTR_NEXT_REVIEW] = None

        return attrs

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:book-open-variant"

