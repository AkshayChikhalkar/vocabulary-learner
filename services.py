"""Services for Vocabulary Learner integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import VocabularyLearnerCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_MARK_KNOWN = "mark_known"
SERVICE_MARK_UNKNOWN = "mark_unknown"
SERVICE_NEXT_WORD = "next_word"
SERVICE_RESET_PROGRESS = "reset_progress"
SERVICE_EXPORT_PROGRESS = "export_progress"

SERVICE_SCHEMA_MARK_WORD = vol.Schema(
    {
        vol.Required("word"): cv.string,
    }
)

SERVICE_SCHEMA_NEXT_WORD = vol.Schema({})

SERVICE_SCHEMA_RESET = vol.Schema({})

SERVICE_SCHEMA_EXPORT = vol.Schema({})


async def async_setup_services(
    hass: HomeAssistant, entry: Any, coordinator: VocabularyLearnerCoordinator
) -> None:
    """Set up services for Vocabulary Learner."""

    async def handle_mark_known(call: ServiceCall) -> None:
        """Handle mark_known service call."""
        word = call.data.get("word")
        if not word:
            _LOGGER.error("Word parameter is required")
            return

        await coordinator.mark_word_known(word)
        _LOGGER.info("Marked word as known: %s", word)

    async def handle_mark_unknown(call: ServiceCall) -> None:
        """Handle mark_unknown service call."""
        word = call.data.get("word")
        if not word:
            _LOGGER.error("Word parameter is required")
            return

        await coordinator.mark_word_unknown(word)
        _LOGGER.info("Marked word as unknown: %s", word)

    async def handle_next_word(call: ServiceCall) -> None:
        """Handle next_word service call."""
        next_word = await coordinator.get_next_word()
        if next_word:
            coordinator.current_word = next_word
            await coordinator.async_request_refresh()
            _LOGGER.info("Retrieved next word: %s", next_word.get("word"))
        else:
            _LOGGER.warning("No words available for review")

    async def handle_reset_progress(call: ServiceCall) -> None:
        """Handle reset_progress service call."""
        await coordinator.reset_progress()
        _LOGGER.info("Reset all learning progress")

    async def handle_export_progress(call: ServiceCall) -> None:
        """Handle export_progress service call."""
        data = await coordinator.export_progress()

        # Store export data in a file or return it
        # For now, log it (in production, you might want to write to a file)
        _LOGGER.info("Exported progress data: %d words, %d known", 
                    len(data.get("vocabulary", [])),
                    data.get("statistics", {}).get("known_words", 0))

        # You could also fire an event with the data
        hass.bus.async_fire(
            f"{DOMAIN}_progress_exported",
            {"data": data},
        )

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_KNOWN,
        handle_mark_known,
        schema=SERVICE_SCHEMA_MARK_WORD,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_UNKNOWN,
        handle_mark_unknown,
        schema=SERVICE_SCHEMA_MARK_WORD,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_NEXT_WORD,
        handle_next_word,
        schema=SERVICE_SCHEMA_NEXT_WORD,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_PROGRESS,
        handle_reset_progress,
        schema=SERVICE_SCHEMA_RESET,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_PROGRESS,
        handle_export_progress,
        schema=SERVICE_SCHEMA_EXPORT,
    )

    _LOGGER.info("Registered Vocabulary Learner services")

