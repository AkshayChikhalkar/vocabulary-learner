"""Config flow for Vocabulary Learner integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_ENABLE_API,
    CONF_NOTIFICATION_ENTITY,
    CONF_NOTIFICATION_FREQUENCY,
    CONF_QUIET_HOURS_END,
    CONF_QUIET_HOURS_START,
    CONF_TARGET_LANGUAGE,
    CONF_VOCAB_FILE,
    CONF_WORDS_PER_DAY,
    DEFAULT_ENABLE_API,
    DEFAULT_NOTIFICATION_FREQUENCY,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_WORDS_PER_DAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Common language codes
LANGUAGE_CODES = {
    "German": "de",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Chinese": "zh",
    "Korean": "ko",
    "Arabic": "ar",
    "Dutch": "nl",
    "Polish": "pl",
    "Turkish": "tr",
    "Swedish": "sv",
    "Norwegian": "no",
    "Danish": "da",
    "Finnish": "fi",
    "Greek": "el",
    "Hebrew": "he",
    "Hindi": "hi",
    "Czech": "cs",
    "Romanian": "ro",
    "Hungarian": "hu",
    "Thai": "th",
    "Vietnamese": "vi",
}


class VocabularyLearnerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vocabulary Learner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate the configuration
                await self._validate_config(user_input)

                # Create unique ID
                await self.async_set_unique_id(f"{DOMAIN}_{user_input.get(CONF_NAME, DOMAIN)}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, "Vocabulary Learner"),
                    data=user_input,
                )
            except InvalidVocabFile:
                errors["base"] = "invalid_vocab_file"
            except Exception as exc:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
                raise

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default="Vocabulary Learner"): str,
                    vol.Optional(CONF_VOCAB_FILE): str,
                    vol.Optional(
                        CONF_WORDS_PER_DAY, default=DEFAULT_WORDS_PER_DAY
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_NOTIFICATION_FREQUENCY,
                        default=DEFAULT_NOTIFICATION_FREQUENCY,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                    vol.Required(
                        CONF_TARGET_LANGUAGE, default=DEFAULT_TARGET_LANGUAGE
                    ): vol.In(list(LANGUAGE_CODES.values())),
                    vol.Optional(CONF_ENABLE_API, default=DEFAULT_ENABLE_API): bool,
                    vol.Optional(CONF_NOTIFICATION_ENTITY): str,
                    vol.Optional(CONF_QUIET_HOURS_START, default="22:00"): str,
                    vol.Optional(CONF_QUIET_HOURS_END, default="08:00"): str,
                }
            ),
            errors=errors,
        )

    async def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate the configuration."""
        vocab_file = config.get(CONF_VOCAB_FILE)
        enable_api = config.get(CONF_ENABLE_API, DEFAULT_ENABLE_API)

        # If vocab file is provided, validate it exists and is readable
        if vocab_file:
            try:
                from .vocabulary.parser import VocabularyParser

                parser = VocabularyParser()
                # Try to parse the file to validate format
                # Note: In actual implementation, we'd need to read from hass.config.config_dir
                # For now, we'll just check if the path is provided
                if not vocab_file.strip():
                    raise InvalidVocabFile("Vocabulary file path cannot be empty")
            except Exception as exc:
                _LOGGER.error("Error validating vocab file: %s", exc)
                raise InvalidVocabFile(f"Invalid vocabulary file: {exc}") from exc

        # If no vocab file and API is disabled, that's an error
        if not vocab_file and not enable_api:
            raise InvalidVocabFile(
                "Either a vocabulary file must be provided or API must be enabled"
            )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VocabularyLearnerOptionsFlowHandler:
        """Get the options flow for this handler."""
        return VocabularyLearnerOptionsFlowHandler(config_entry)


class VocabularyLearnerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Vocabulary Learner."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            self.hass.config_entries.async_update_entry(
                self._config_entry, options=user_input
            )
            return self.async_create_entry(title="", data=user_input)

        # Get current options or use data as fallback
        config_entry = self._config_entry
        options = config_entry.options or config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_VOCAB_FILE,
                        default=options.get(CONF_VOCAB_FILE, ""),
                    ): str,
                    vol.Optional(
                        CONF_WORDS_PER_DAY,
                        default=options.get(
                            CONF_WORDS_PER_DAY, DEFAULT_WORDS_PER_DAY
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_NOTIFICATION_FREQUENCY,
                        default=options.get(
                            CONF_NOTIFICATION_FREQUENCY,
                            DEFAULT_NOTIFICATION_FREQUENCY,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                    vol.Required(
                        CONF_TARGET_LANGUAGE,
                        default=options.get(
                            CONF_TARGET_LANGUAGE, DEFAULT_TARGET_LANGUAGE
                        ),
                    ): vol.In(list(LANGUAGE_CODES.values())),
                    vol.Optional(
                        CONF_ENABLE_API,
                        default=options.get(CONF_ENABLE_API, DEFAULT_ENABLE_API),
                    ): bool,
                    vol.Optional(
                        CONF_NOTIFICATION_ENTITY,
                        default=options.get(CONF_NOTIFICATION_ENTITY, ""),
                    ): str,
                    vol.Optional(
                        CONF_QUIET_HOURS_START,
                        default=options.get(CONF_QUIET_HOURS_START, "22:00"),
                    ): str,
                    vol.Optional(
                        CONF_QUIET_HOURS_END,
                        default=options.get(CONF_QUIET_HOURS_END, "08:00"),
                    ): str,
                }
            ),
        )


class InvalidVocabFile(HomeAssistantError):
    """Error to indicate invalid vocabulary file."""

