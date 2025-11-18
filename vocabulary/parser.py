"""Vocabulary file parser supporting multiple formats."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from .const import FILE_FORMAT_CSV, FILE_FORMAT_JSON, FILE_FORMAT_TXT, FILE_FORMAT_TSV

_LOGGER = logging.getLogger(__name__)


class VocabularyEntry:
    """Represents a single vocabulary entry."""

    def __init__(
        self,
        word: str,
        translation: str,
        example: str | None = None,
        synonyms: list[str] | None = None,
        etymology: str | None = None,
    ) -> None:
        """Initialize vocabulary entry."""
        self.word = word.strip()
        self.translation = translation.strip()
        self.example = example.strip() if example else None
        self.synonyms = synonyms or []
        self.etymology = etymology

    def __repr__(self) -> str:
        """String representation."""
        return f"VocabularyEntry(word='{self.word}', translation='{self.translation}')"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "word": self.word,
            "translation": self.translation,
            "example": self.example,
            "synonyms": self.synonyms,
            "etymology": self.etymology,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VocabularyEntry:
        """Create from dictionary."""
        return cls(
            word=data.get("word", ""),
            translation=data.get("translation", ""),
            example=data.get("example"),
            synonyms=data.get("synonyms"),
            etymology=data.get("etymology"),
        )


class VocabularyParser:
    """Parser for vocabulary files in various formats."""

    def __init__(self) -> None:
        """Initialize parser."""
        self.supported_formats = [FILE_FORMAT_CSV, FILE_FORMAT_JSON, FILE_FORMAT_TXT, FILE_FORMAT_TSV]

    def detect_format(self, file_path: str | Path) -> str:
        """Detect file format from extension or content."""
        path = Path(file_path)
        extension = path.suffix.lower().lstrip(".")

        if extension in ["csv"]:
            return FILE_FORMAT_CSV
        if extension in ["json"]:
            return FILE_FORMAT_JSON
        if extension in ["tsv"]:
            return FILE_FORMAT_TSV
        if extension in ["txt", "text"]:
            return FILE_FORMAT_TXT

        # Try to detect from content
        try:
            with open(path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                # Check if it's JSON
                if first_line.startswith("["):
                    return FILE_FORMAT_JSON
                # Check if it's CSV (has commas)
                if "," in first_line and not first_line.startswith("#"):
                    return FILE_FORMAT_CSV
                # Check if it's TSV (has tabs)
                if "\t" in first_line:
                    return FILE_FORMAT_TSV
        except Exception:
            pass

        # Default to TXT
        return FILE_FORMAT_TXT

    async def parse_file(
        self, file_path: str | Path, encoding: str = "utf-8"
    ) -> list[VocabularyEntry]:
        """Parse vocabulary file and return list of entries."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Vocabulary file not found: {file_path}")

        file_format = self.detect_format(path)

        _LOGGER.info("Parsing vocabulary file %s as %s format", file_path, file_format)

        try:
            if file_format == FILE_FORMAT_CSV:
                return await self._parse_csv(path, encoding)
            if file_format == FILE_FORMAT_JSON:
                return await self._parse_json(path, encoding)
            if file_format == FILE_FORMAT_TSV:
                return await self._parse_tsv(path, encoding)
            if file_format == FILE_FORMAT_TXT:
                return await self._parse_txt(path, encoding)
        except Exception as exc:
            _LOGGER.error("Error parsing vocabulary file: %s", exc)
            raise ValueError(f"Failed to parse vocabulary file: {exc}") from exc

        raise ValueError(f"Unsupported file format: {file_format}")

    async def _parse_csv(
        self, file_path: Path, encoding: str
    ) -> list[VocabularyEntry]:
        """Parse CSV file."""
        entries: list[VocabularyEntry] = []

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # Try different column name variations
                word = (
                    row.get("word")
                    or row.get("Word")
                    or row.get("WORD")
                    or row.get("original")
                    or row.get("source")
                    or list(row.values())[0] if row.values() else ""
                )
                translation = (
                    row.get("translation")
                    or row.get("Translation")
                    or row.get("TRANSLATION")
                    or row.get("target")
                    or row.get("meaning")
                    or list(row.values())[1] if len(row.values()) > 1 else ""
                )
                example = (
                    row.get("example")
                    or row.get("Example")
                    or row.get("EXAMPLE")
                    or row.get("sentence")
                    or (list(row.values())[2] if len(row.values()) > 2 else None)
                )

                if word and translation:
                    entries.append(
                        VocabularyEntry(
                            word=word, translation=translation, example=example
                        )
                    )

        return entries

    async def _parse_json(
        self, file_path: Path, encoding: str
    ) -> list[VocabularyEntry]:
        """Parse JSON file."""
        entries: list[VocabularyEntry] = []

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    entries.append(VocabularyEntry.from_dict(item))
        elif isinstance(data, dict):
            # Could be a dict with a list of words
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            entries.append(VocabularyEntry.from_dict(item))
                elif isinstance(value, dict):
                    entries.append(VocabularyEntry.from_dict(value))

        return entries

    async def _parse_tsv(
        self, file_path: Path, encoding: str
    ) -> list[VocabularyEntry]:
        """Parse TSV (tab-separated) file."""
        entries: list[VocabularyEntry] = []

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                word = row.get("word") or list(row.values())[0] if row.values() else ""
                translation = (
                    row.get("translation")
                    or (list(row.values())[1] if len(row.values()) > 1 else "")
                )
                example = (
                    row.get("example")
                    or (list(row.values())[2] if len(row.values()) > 2 else None)
                )

                if word and translation:
                    entries.append(
                        VocabularyEntry(
                            word=word, translation=translation, example=example
                        )
                    )

        return entries

    async def _parse_txt(
        self, file_path: Path, encoding: str
    ) -> list[VocabularyEntry]:
        """Parse plain text file."""
        entries: list[VocabularyEntry] = []

        # Try different encodings
        encodings = [encoding, "utf-8", "utf-16", "latin-1", "cp1252"]

        content = None
        used_encoding = None

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc, errors="replace") as f:
                    content = f.read()
                    used_encoding = enc
                    break
            except Exception:
                continue

        if content is None:
            raise ValueError(f"Could not read file with any encoding: {file_path}")

        _LOGGER.debug("Read file with encoding: %s", used_encoding)

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Try different separators
            # Format: "word – translation" or "word|translation" or "word:translation"
            word = None
            translation = None
            example = None

            # Try em dash, en dash, pipe, colon, comma
            for separator in [" – ", " — ", " | ", ":", ",", "\t"]:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        word = parts[0].strip()
                        rest = parts[1].strip()

                        # Check if there's an example (usually in parentheses or after a semicolon)
                        if "(" in rest and ")" in rest:
                            translation = rest.split("(")[0].strip()
                            example = rest.split("(")[1].split(")")[0].strip()
                        elif ";" in rest:
                            parts2 = rest.split(";", 1)
                            translation = parts2[0].strip()
                            example = parts2[1].strip()
                        else:
                            translation = rest

                        break

            # If no separator found, treat entire line as word (translation will come from API)
            if not word:
                word = line
                translation = ""

            if word:
                entries.append(
                    VocabularyEntry(
                        word=word, translation=translation, example=example
                    )
                )

        return entries

