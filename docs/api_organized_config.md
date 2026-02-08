# Organized Character Configuration API

This document describes the new API endpoints for organized character configuration in Open-LLM-VTuber.

## Overview

The organized character configuration system allows you to independently select:
- **Avatar** - Live2D model
- **Character** - Personality/behavior preset from YAML files
- **Voice** - TTS voice

## API Endpoints

### 1. List Available Characters

**Endpoint:** `GET /api/characters/list`

**Description:** Returns a list of all available character configuration files from the `characters/` directory.

**Response:**
```json
{
  "status": "success",
  "count": 19,
  "characters": [
    {
      "filename": "conf.yaml",
      "name": "mao_pro",
      "conf_uid": "mao_pro_001"
    },
    {
      "filename": "shizuku.yaml",
      "name": "Shizuku Character",
      "conf_uid": "shizuku_001"
    }
  ]
}
```

**Fields:**
- `filename`: The actual YAML filename
- `name`: Display name from the `conf_name` field in the YAML
- `conf_uid`: Unique identifier for the character configuration

---

### 2. List Available Voices

**Endpoint:** `GET /api/voices/list`

**Description:** Returns a list of available TTS voices for the currently active TTS provider.

**Response:**
```json
{
  "status": "success",
  "provider": "edge_tts",
  "count": 10,
  "voices": [
    {
      "id": "en-US-AvaMultilingualNeural",
      "name": "Ava (English US, Multilingual)",
      "language": "en-US"
    },
    {
      "id": "en-US-EmmaMultilingualNeural",
      "name": "Emma (English US, Multilingual)",
      "language": "en-US"
    }
  ]
}
```

**Fields:**
- `provider`: Current TTS provider (e.g., `edge_tts`, `azure_tts`, `melo_tts`)
- `voices`: Array of available voices
  - `id`: Voice identifier to use in configuration
  - `name`: Human-readable voice name
  - `language`: Language/locale code

**Supported Providers:**
- `edge_tts`: 10 voices (English, Chinese, Japanese)
- `azure_tts`: 3 voices
- `melo_tts`: 5 voices
- Others: Generic default voice

---

### 3. Update Partial Configuration

**Endpoint:** `POST /api/config/update-partial`

**Description:** Updates specific aspects of the character configuration independently. You can update just the avatar, just the character, just the voice, or any combination.

**Request Body:**
```json
{
  "avatar": "shizuku",
  "character": "shizuku.yaml",
  "voice": "en-US-EmmaMultilingualNeural"
}
```

**Request Fields (all optional):**
- `avatar`: Live2D model name (must exist in `model_dict.json`)
- `character`: Character YAML filename (from `characters/` directory or `conf.yaml`)
- `voice`: TTS voice ID (must be valid for current TTS provider)

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "applied": {
    "avatar": "shizuku",
    "character": "shizuku.yaml",
    "voice": "en-US-EmmaMultilingualNeural"
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description here"
}
```

---

## Usage Examples

### Example 1: Change Only the Avatar

```bash
curl -X POST http://localhost:12393/api/config/update-partial \
  -H "Content-Type: application/json" \
  -d '{"avatar": "mao_pro"}'
```

This switches the Live2D model to `mao_pro` while keeping the current character personality and voice.

### Example 2: Change Character and Voice Together

```bash
curl -X POST http://localhost:12393/api/config/update-partial \
  -H "Content-Type: application/json" \
  -d '{
    "character": "en_wholesome_supportive_waifu.yaml",
    "voice": "en-US-AvaMultilingualNeural"
  }'
```

This loads the wholesome supportive waifu personality and uses Ava's voice, while keeping the current Live2D model.

### Example 3: Complete Configuration Switch

```bash
curl -X POST http://localhost:12393/api/config/update-partial \
  -H "Content-Type: application/json" \
  -d '{
    "avatar": "izumi",
    "character": "izumi.yaml",
    "voice": "ja-JP-NanamiNeural"
  }'
```

This switches everything: Izumi model, Izumi personality, and Japanese voice.

---

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
// Fetch available options
async function loadOptions() {
  const [characters, voices, models] = await Promise.all([
    fetch('/api/characters/list').then(r => r.json()),
    fetch('/api/voices/list').then(r => r.json()),
    fetch('/live2d-models/info').then(r => r.json())
  ]);

  return {
    characters: characters.characters,
    voices: voices.voices,
    models: models.characters
  };
}

// Apply configuration
async function updateConfig(config: {
  avatar?: string;
  character?: string;
  voice?: string;
}) {
  const response = await fetch('/api/config/update-partial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });

  const result = await response.json();
  
  if (result.status === 'success') {
    console.log('Configuration updated!', result.applied);
    return true;
  } else {
    console.error('Update failed:', result.message);
    return false;
  }
}

// Usage
const success = await updateConfig({
  avatar: 'shizuku',
  voice: 'en-US-EmmaMultilingualNeural'
});
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function CharacterConfigurator() {
  const [characters, setCharacters] = useState([]);
  const [voices, setVoices] = useState([]);
  const [models, setModels] = useState([]);
  
  const [selectedAvatar, setSelectedAvatar] = useState('');
  const [selectedCharacter, setSelectedCharacter] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');

  useEffect(() => {
    // Load options on mount
    Promise.all([
      fetch('/api/characters/list').then(r => r.json()),
      fetch('/api/voices/list').then(r => r.json()),
      fetch('/live2d-models/info').then(r => r.json())
    ]).then(([chars, vcs, mdls]) => {
      setCharacters(chars.characters);
      setVoices(vcs.voices);
      setModels(mdls.characters);
    });
  }, []);

  const handleApply = async () => {
    const response = await fetch('/api/config/update-partial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar: selectedAvatar,
        character: selectedCharacter,
        voice: selectedVoice
      })
    });

    const result = await response.json();
    if (result.status === 'success') {
      alert('Configuration updated successfully!');
    }
  };

  return (
    <div>
      <h3>Avatar (Live2D Model)</h3>
      <select value={selectedAvatar} onChange={e => setSelectedAvatar(e.target.value)}>
        {models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
      </select>

      <h3>Character (Personality)</h3>
      <select value={selectedCharacter} onChange={e => setSelectedCharacter(e.target.value)}>
        {characters.map(c => <option key={c.filename} value={c.filename}>{c.name}</option>)}
      </select>

      <h3>Voice</h3>
      <select value={selectedVoice} onChange={e => setSelectedVoice(e.target.value)}>
        {voices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
      </select>

      <button onClick={handleApply}>Apply Configuration</button>
    </div>
  );
}
```

---

## Notes

- All three parameters in `/api/config/update-partial` are optional
- If a parameter is not provided, that aspect of the configuration remains unchanged
- The server will reinitialize necessary components (Live2D, TTS, Agent) when configuration changes
- Voice IDs must match the current TTS provider's supported voices
- Character YAML files are loaded from the `characters/` directory specified in `system_config.config_alts_dir`

---

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request body
- `404 Not Found`: Resource not found (e.g., invalid character file)
- `500 Internal Server Error`: Server-side error

Always check the `status` field in the JSON response:
- `"success"`: Operation completed successfully
- `"error"`: Operation failed, check `message` field for details
