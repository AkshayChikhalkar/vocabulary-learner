# Vocabulary Learner - Examples

## Example Vocabulary Files

### CSV Example (German)

```csv
word,translation,example
der Tisch,the table,Der Tisch ist groß
das Buch,the book,Ich lese das Buch
die Tür,the door,Die Tür ist offen
das Fenster,the window,Das Fenster ist geschlossen
der Stuhl,the chair,Der Stuhl ist bequem
```

### JSON Example

```json
[
  {
    "word": "der Tisch",
    "translation": "the table",
    "example": "Der Tisch ist groß"
  },
  {
    "word": "das Buch",
    "translation": "the book",
    "example": "Ich lese das Buch"
  },
  {
    "word": "die Tür",
    "translation": "the door",
    "example": "Die Tür ist offen"
  }
]
```

### Plain Text Example

```
der Tisch – the table
das Buch – the book
die Tür – the door
das Fenster – the window
der Stuhl – the chair
```

## Example Automations

### Mark Word as Known via Button

```yaml
automation:
  - alias: "Mark Vocabulary Word as Known"
    trigger:
      - platform: state
        entity_id: input_button.vocab_known
        to: "pressed"
    action:
      - service: vocabulary_learner.mark_known
        data:
          word: "{{ states('sensor.vocabulary_learner') }}"
      - service: vocabulary_learner.next_word
```

### Daily Vocabulary Reminder

```yaml
automation:
  - alias: "Daily Vocabulary Reminder"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: state
        entity_id: sensor.vocabulary_learner
        state: "idle"
    action:
      - service: vocabulary_learner.next_word
      - delay: "00:00:05"
      - service: notify.mobile_app_phone
        data:
          message: "Time to learn: {{ state_attr('sensor.vocabulary_learner', 'current_word') }}"
          title: "Vocabulary Learner"
```

### Show Word on Display

```yaml
automation:
  - alias: "Update Vocabulary Display"
    trigger:
      - platform: state
        entity_id: sensor.vocabulary_learner
    action:
      - service: input_text.set_value
        target:
          entity_id: input_text.vocab_display
        data:
          value: >
            {{ state_attr('sensor.vocabulary_learner', 'current_word') }}
            -
            {{ state_attr('sensor.vocabulary_learner', 'translation') }}
```

### Weekly Progress Report

```yaml
automation:
  - alias: "Weekly Vocabulary Progress"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: time
        weekday:
          - mon
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Weekly Vocabulary Progress"
          message: >
            Words Known: {{ state_attr('sensor.vocabulary_learner', 'words_known') }}/{{ state_attr('sensor.vocabulary_learner', 'words_total') }}
            Progress: {{ state_attr('sensor.vocabulary_learner', 'progress_percent') }}%
            Streak: {{ state_attr('sensor.vocabulary_learner', 'streak_days') }} days
```

## Example Scripts

### Review Session

```yaml
script:
  vocab_review_session:
    alias: "Vocabulary Review Session"
    sequence:
      - service: vocabulary_learner.next_word
      - delay: "00:00:10"
      - service: vocabulary_learner.next_word
      - delay: "00:00:10"
      - service: vocabulary_learner.next_word
```

### Mark Multiple Words

```yaml
script:
  mark_words_known:
    alias: "Mark Words as Known"
    sequence:
      - repeat:
          count: 5
          sequence:
            - service: vocabulary_learner.mark_known
              data:
                word: "{{ states('sensor.vocabulary_learner') }}"
            - service: vocabulary_learner.next_word
            - delay: "00:00:02"
```

## Example Lovelace Card

```yaml
type: entities
title: Vocabulary Learner
entities:
  - entity: sensor.vocabulary_learner
    name: Current Word
  - type: attribute
    entity: sensor.vocabulary_learner
    attribute: translation
    name: Translation
  - type: attribute
    entity: sensor.vocabulary_learner
    attribute: words_known
    name: Words Known
  - type: attribute
    entity: sensor.vocabulary_learner
    attribute: words_total
    name: Total Words
  - type: attribute
    entity: sensor.vocabulary_learner
    attribute: progress_percent
    name: Progress
    unit: "%"
```

## Example Input Helpers

```yaml
input_boolean:
  vocab_learning_mode:
    name: Vocabulary Learning Mode
    icon: mdi:book-open-variant

input_button:
  vocab_known:
    name: Mark as Known
    icon: mdi:check-circle

input_button:
  vocab_unknown:
    name: Mark as Unknown
    icon: mdi:close-circle

input_button:
  vocab_next:
    name: Next Word
    icon: mdi:arrow-right-circle
```

## Example Dashboard Card with Buttons

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # Vocabulary Learner
      **Current Word:** {{ states('sensor.vocabulary_learner') }}
      **Translation:** {{ state_attr('sensor.vocabulary_learner', 'translation') }}
      
      Progress: {{ state_attr('sensor.vocabulary_learner', 'progress_percent') }}%
      Known: {{ state_attr('sensor.vocabulary_learner', 'words_known') }}/{{ state_attr('sensor.vocabulary_learner', 'words_total') }}
  
  - type: horizontal-stack
    cards:
      - type: button
        entity: input_button.vocab_known
        name: Known
        tap_action:
          action: call-service
          service: vocabulary_learner.mark_known
          service_data:
            word: "{{ states('sensor.vocabulary_learner') }}"
      - type: button
        entity: input_button.vocab_unknown
        name: Unknown
        tap_action:
          action: call-service
          service: vocabulary_learner.mark_unknown
          service_data:
            word: "{{ states('sensor.vocabulary_learner') }}"
      - type: button
        entity: input_button.vocab_next
        name: Next
        tap_action:
          action: call-service
          service: vocabulary_learner.next_word
```

