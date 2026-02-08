# Quick Start: Organized Character Configuration

## Access the Configuration UI

1. **Start the server**:
   ```bash
   uv run python run_server.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:12393/character-config
   ```

## How to Use

### Change Avatar Only
1. Select a Live2D model from the **Avatar** dropdown
2. Leave **Character** and **Voice** as "-- Keep Current --"
3. Click **Apply Configuration**

### Change Character Personality Only
1. Leave **Avatar** as "-- Keep Current --"
2. Select a character YAML from the **Character** dropdown
3. Leave **Voice** as "-- Keep Current --"
4. Click **Apply Configuration**

### Change Voice Only
1. Leave **Avatar** and **Character** as "-- Keep Current --"
2. Select a TTS voice from the **Voice** dropdown
3. Click **Apply Configuration**

### Change Everything
1. Select an avatar from the **Avatar** dropdown
2. Select a character from the **Character** dropdown
3. Select a voice from the **Voice** dropdown
4. Click **Apply Configuration**

## Example Configurations

### Japanese Character Setup
- **Avatar**: `izumi`
- **Character**: `izumi.yaml`
- **Voice**: `ja-JP-NanamiNeural`

### English Supportive Character
- **Avatar**: `mao_pro`
- **Character**: `en_wholesome_supportive_waifu.yaml`
- **Voice**: `en-US-AvaMultilingualNeural`

### Chinese Character
- **Avatar**: `shizuku`
- **Character**: `zh_米粒.yaml`
- **Voice**: `zh-CN-XiaoxiaoNeural`

## Features

✅ **Independent Selection** - Change avatar, character, or voice separately
✅ **Partial Updates** - Only update what you select
✅ **Real-time Counts** - See how many options are available
✅ **Status Messages** - Get feedback on successful/failed updates
✅ **Auto-reset** - Form clears after successful update

## Troubleshooting

### UI doesn't load
- Make sure the server is running on port 12393
- Check that no firewall is blocking the connection

### Changes don't take effect
- Check the status message for errors
- Verify the server logs for any issues
- Make sure you clicked "Apply Configuration"

### Options not showing
- Ensure your `characters/` directory has YAML files
- Verify `model_dict.json` has Live2D model entries
- Check that your TTS provider is configured correctly

## API Endpoints (For Advanced Users)

If you prefer to use the API directly:

```bash
# List available characters
curl http://localhost:12393/api/characters/list

# List available voices
curl http://localhost:12393/api/voices/list

# Update configuration
curl -X POST http://localhost:12393/api/config/update-partial \
  -H "Content-Type: application/json" \
  -d '{"avatar": "shizuku", "voice": "en-US-EmmaMultilingualNeural"}'
```

## What's Next?

This standalone UI works independently. If you want to integrate it into the main React frontend:

1. Clone the `Open-LLM-VTuber-Web` repository
2. Add the configuration components to the React app
3. Use the API endpoints documented in `docs/api_organized_config.md`

Enjoy your organized character configuration! 🎭
