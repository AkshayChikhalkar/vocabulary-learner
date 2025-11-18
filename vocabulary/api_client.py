"""API clients for vocabulary services (Wiktionary, LibreTranslate)."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WiktionaryClient:
    """Client for Wiktionary API."""

    def __init__(self) -> None:
        """Initialize Wiktionary client."""
        self.base_url = "https://en.wiktionary.org/api/rest_v1/page/definition"
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self) -> None:
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_word_info(self, word: str, language: str = "en") -> dict[str, Any] | None:
        """
        Get word information from Wiktionary.

        Args:
            word: Word to look up
            language: Language code (e.g., 'de' for German)

        Returns:
            Dictionary with word information or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{language}/{word.lower()}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_wiktionary_response(data, word)
                elif response.status == 404:
                    _LOGGER.debug("Word not found in Wiktionary: %s", word)
                    return None
                else:
                    _LOGGER.warning(
                        "Wiktionary API returned status %d for word %s",
                        response.status,
                        word,
                    )
                    return None
        except aiohttp.ClientError as exc:
            _LOGGER.error("Error fetching from Wiktionary: %s", exc)
            return None
        except Exception as exc:
            _LOGGER.error("Unexpected error in Wiktionary client: %s", exc)
            return None

    def _parse_wiktionary_response(
        self, data: dict[str, Any], word: str
    ) -> dict[str, Any]:
        """Parse Wiktionary API response."""
        result: dict[str, Any] = {
            "word": word,
            "definitions": [],
            "examples": [],
            "etymology": None,
            "synonyms": [],
        }

        try:
            # Wiktionary API returns definitions by language
            for lang_data in data.values():
                if isinstance(lang_data, list):
                    for entry in lang_data:
                        if isinstance(entry, dict):
                            # Extract definitions
                            if "definitions" in entry:
                                for def_entry in entry["definitions"]:
                                    if "definition" in def_entry:
                                        result["definitions"].append(
                                            def_entry["definition"]
                                        )
                                    if "examples" in def_entry:
                                        for example in def_entry["examples"]:
                                            if "text" in example:
                                                result["examples"].append(
                                                    example["text"]
                                                )

                            # Extract etymology
                            if "etymology" in entry and not result["etymology"]:
                                result["etymology"] = entry["etymology"]

                            # Extract synonyms
                            if "synonyms" in entry:
                                for synonym in entry["synonyms"]:
                                    if isinstance(synonym, str):
                                        result["synonyms"].append(synonym)
                                    elif isinstance(synonym, dict) and "text" in synonym:
                                        result["synonyms"].append(synonym["text"])

        except Exception as exc:
            _LOGGER.error("Error parsing Wiktionary response: %s", exc)

        return result


class LibreTranslateClient:
    """Client for LibreTranslate API."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize LibreTranslate client."""
        self.base_url = base_url or "https://libretranslate.com"
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self) -> None:
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> str | None:
        """
        Translate text using LibreTranslate.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'de')
            target_lang: Target language code (e.g., 'en')

        Returns:
            Translated text or None if translation failed
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/translate"

            payload = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text",
            }

            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("translatedText")
                else:
                    _LOGGER.warning(
                        "LibreTranslate API returned status %d",
                        response.status,
                    )
                    return None
        except aiohttp.ClientError as exc:
            _LOGGER.error("Error translating with LibreTranslate: %s", exc)
            return None
        except Exception as exc:
            _LOGGER.error("Unexpected error in LibreTranslate client: %s", exc)
            return None

    async def get_languages(self) -> list[dict[str, str]] | None:
        """Get list of supported languages."""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/languages"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as exc:
            _LOGGER.error("Error fetching languages: %s", exc)
            return None


class VocabularyAPIClient:
    """Combined API client with fallback logic."""

    def __init__(self) -> None:
        """Initialize combined API client."""
        self.wiktionary = WiktionaryClient()
        self.libretranslate = LibreTranslateClient()

    async def get_word_info(
        self, word: str, source_lang: str, target_lang: str = "en"
    ) -> dict[str, Any] | None:
        """
        Get word information with fallback logic.

        Tries Wiktionary first, then LibreTranslate for translation.

        Args:
            word: Word to look up
            source_lang: Source language code
            target_lang: Target language code (default: 'en')

        Returns:
            Dictionary with word information
        """
        result: dict[str, Any] = {
            "word": word,
            "translation": None,
            "example": None,
            "synonyms": [],
            "etymology": None,
        }

        # Try Wiktionary first
        wiktionary_info = await self.wiktionary.get_word_info(word, source_lang)
        if wiktionary_info:
            # Use first definition as translation if available
            if wiktionary_info.get("definitions"):
                result["translation"] = wiktionary_info["definitions"][0]
            if wiktionary_info.get("examples"):
                result["example"] = wiktionary_info["examples"][0]
            if wiktionary_info.get("synonyms"):
                result["synonyms"] = wiktionary_info["synonyms"]
            if wiktionary_info.get("etymology"):
                result["etymology"] = wiktionary_info["etymology"]

        # If no translation from Wiktionary, try LibreTranslate
        if not result["translation"] and source_lang != target_lang:
            translation = await self.libretranslate.translate(
                word, source_lang, target_lang
            )
            if translation:
                result["translation"] = translation

        return result if result.get("translation") else None

    async def close(self) -> None:
        """Close all client sessions."""
        await self.wiktionary.close()
        await self.libretranslate.close()

