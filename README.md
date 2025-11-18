# Vocabulary Learner

A Home Assistant integration for learning vocabulary with spaced repetition, progress tracking, and notifications.

## Features

- 📚 **Multiple File Formats**: Support for CSV, JSON, TXT, and TSV vocabulary files
- 🔄 **Spaced Repetition**: SM-2 algorithm (Anki-style) for optimal learning
- 📊 **Progress Tracking**: Track known, learning, and unknown words
- 🔔 **Notifications**: Configurable notifications with quiet hours
- 🌐 **API Integration**: Fallback to Wiktionary and LibreTranslate APIs
- 📈 **Statistics**: Track your learning progress and streaks
- 🌍 **Multi-language**: Support for any language

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL
5. Search for "Vocabulary Learner" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `vocabulary_learner` folder to `custom_components/` in your Home Assistant config directory
2. Restart Home Assistant
3. Add the integration via Settings > Devices & Services > Add Integration

## Configuration

### Initial Setup

1. Go to Settings > Devices & Services > Add Integration
2. Search for "Vocabulary Learner"
3. Configure:
   - **Vocabulary File** (optional): Path to your vocabulary file relative to config directory
   - **Words Per Day**: Number of words to learn per day (1-100)
   - **Notification Frequency**: How often to receive notifications (in minutes)
   - **Target Language**: Language code (e.g., 'de' for German)
   - **Enable API**: Use API fallback if no vocabulary file
   - **Notification Entity**: Entity ID for notifications (e.g., `notify.mobile_app_phone`)
   - **Quiet Hours**: Time range when notifications are disabled

### Vocabulary File Formats

#### CSV Format
```csv
word,translation,example
der Tisch,the table,Der Tisch ist groß
das Buch,the book,Ich lese das Buch
```

#### JSON Format
```json
[
  {
    "word": "der Tisch",
    "translation": "the table",
    "example": "Der Tisch ist groß"
  }
]
```

#### Plain Text Format
```
der Tisch – the table
das Buch – the book
```

## Usage

### Services

The integration provides several services:

#### `vocabulary_learner.mark_known`
Mark a word as known.

```yaml
service: vocabulary_learner.mark_known
data:
  word: "der Tisch"
```

#### `vocabulary_learner.mark_unknown`
Mark a word as unknown.

```yaml
service: vocabulary_learner.mark_unknown
data:
  word: "der Tisch"
```

#### `vocabulary_learner.next_word`
Get the next word for review.

```yaml
service: vocabulary_learner.next_word
```

#### `vocabulary_learner.reset_progress`
Reset all learning progress.

```yaml
service: vocabulary_learner.reset_progress
```

#### `vocabulary_learner.export_progress`
Export your learning progress.

```yaml
service: vocabulary_learner.export_progress
```

### Sensor Attributes

The `sensor.vocabulary_learner` entity provides:

- **State**: Current word or "idle"
- **current_word**: Current word being reviewed
- **translation**: Translation of current word
- **example**: Example sentence (if available)
- **synonyms**: List of synonyms
- **etymology**: Etymology information
- **words_total**: Total number of words
- **words_known**: Number of known words
- **words_today**: Words reviewed today
- **progress_percent**: Learning progress percentage
- **streak_days**: Current learning streak
- **next_review**: Next review time

### Automations

Example automation to mark words as known:

```yaml
automation:
  - alias: "Mark word as known"
    trigger:
      - platform: state
        entity_id: input_boolean.vocab_known
        to: "on"
    action:
      - service: vocabulary_learner.mark_known
        data:
          word: "{{ states('sensor.vocabulary_learner') }}"
```

## API Integration

When no vocabulary file is provided and API is enabled, the integration can fetch word information from:

- **Wiktionary**: Word definitions, examples, etymology, synonyms
- **LibreTranslate**: Translations

Note: API integration requires internet connectivity and may have rate limits.

## Requirements

- Home Assistant 2023.1.0 or later
- Python packages (installed automatically):
  - `wiktionaryparser>=0.0.9`
  - `aiohttp>=3.8.0`
  - `requests>=2.28.0`

## Troubleshooting

### Vocabulary file not loading

- Ensure the file path is relative to your Home Assistant config directory
- Check file encoding (UTF-8 recommended)
- Verify file format matches one of the supported formats

### Notifications not working

- Verify the notification entity ID is correct
- Check that quiet hours are not active
- Ensure the notification service is available

### API errors

- Check internet connectivity
- Verify API endpoints are accessible
- Check rate limiting (may need to wait between requests)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.

## Credits

Inspired by vocabulary learning apps like Anki, Vopik, and OpenLinguify.

