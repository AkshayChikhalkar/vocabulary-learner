"""Constants for the Vocabulary Learner integration."""

from typing import Final

DOMAIN: Final = "vocabulary_learner"
DEFAULT_NAME: Final = "Vocabulary Learner"

# Configuration keys
CONF_VOCAB_FILE: Final = "vocab_file"
CONF_WORDS_PER_DAY: Final = "words_per_day"
CONF_NOTIFICATION_FREQUENCY: Final = "notification_frequency"
CONF_TARGET_LANGUAGE: Final = "target_language"
CONF_ENABLE_API: Final = "enable_api"
CONF_NOTIFICATION_ENTITY: Final = "notification_entity"
CONF_QUIET_HOURS_START: Final = "quiet_hours_start"
CONF_QUIET_HOURS_END: Final = "quiet_hours_end"

# Default values
DEFAULT_WORDS_PER_DAY: Final = 10
DEFAULT_NOTIFICATION_FREQUENCY: Final = 60  # minutes
DEFAULT_TARGET_LANGUAGE: Final = "de"  # German
DEFAULT_ENABLE_API: Final = True

# Storage keys
STORAGE_KEY: Final = "vocabulary_learner"
STORAGE_VERSION: Final = 1

# File format constants
FILE_FORMAT_CSV: Final = "csv"
FILE_FORMAT_JSON: Final = "json"
FILE_FORMAT_TXT: Final = "txt"
FILE_FORMAT_TSV: Final = "tsv"

# Word status
WORD_STATUS_UNKNOWN: Final = "unknown"
WORD_STATUS_LEARNING: Final = "learning"
WORD_STATUS_KNOWN: Final = "known"

# Spaced repetition constants
SM2_INITIAL_EASINESS: Final = 2.5
SM2_MIN_EASINESS: Final = 1.3
SM2_MIN_INTERVAL: Final = 1  # days
SM2_MAX_INTERVAL: Final = 365  # days

# API endpoints
LIBRETRANSLATE_PUBLIC_URL: Final = "https://libretranslate.com/translate"
WIKTIONARY_BASE_URL: Final = "https://en.wiktionary.org/wiki/"

# Attributes
ATTR_CURRENT_WORD: Final = "current_word"
ATTR_TRANSLATION: Final = "translation"
ATTR_EXAMPLE: Final = "example"
ATTR_SYNONYMS: Final = "synonyms"
ATTR_ETYMOLOGY: Final = "etymology"
ATTR_WORDS_KNOWN: Final = "words_known"
ATTR_WORDS_TOTAL: Final = "words_total"
ATTR_WORDS_TODAY: Final = "words_today"
ATTR_NEXT_REVIEW: Final = "next_review"
ATTR_PROGRESS_PERCENT: Final = "progress_percent"
ATTR_STREAK_DAYS: Final = "streak_days"

