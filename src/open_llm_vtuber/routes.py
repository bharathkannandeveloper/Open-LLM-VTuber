import os
import json
from uuid import uuid4
from typing import Optional
import numpy as np
from datetime import datetime
from fastapi import APIRouter, WebSocket, UploadFile, File, Response
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from .service_context import ServiceContext
from .websocket_handler import WebSocketHandler
from .proxy_handler import ProxyHandler


class PartialConfigUpdate(BaseModel):
    """Request model for partial configuration updates"""

    avatar: Optional[str] = None
    character: Optional[str] = None
    voice: Optional[str] = None


def init_client_ws_route(default_context_cache: ServiceContext) -> APIRouter:
    """
    Create and return API routes for handling the `/client-ws` WebSocket connections.

    Args:
        default_context_cache: Default service context cache for new sessions.

    Returns:
        APIRouter: Configured router with WebSocket endpoint.
    """

    router = APIRouter()
    ws_handler = WebSocketHandler(default_context_cache)

    @router.websocket("/client-ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for client connections"""
        await websocket.accept()
        client_uid = str(uuid4())

        try:
            await ws_handler.handle_new_connection(websocket, client_uid)
            await ws_handler.handle_websocket_communication(websocket, client_uid)
        except WebSocketDisconnect:
            await ws_handler.handle_disconnect(client_uid)
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
            await ws_handler.handle_disconnect(client_uid)
            raise

    return router


def init_proxy_route(server_url: str) -> APIRouter:
    """
    Create and return API routes for handling proxy connections.

    Args:
        server_url: The WebSocket URL of the actual server

    Returns:
        APIRouter: Configured router with proxy WebSocket endpoint
    """
    router = APIRouter()
    proxy_handler = ProxyHandler(server_url)

    @router.websocket("/proxy-ws")
    async def proxy_endpoint(websocket: WebSocket):
        """WebSocket endpoint for proxy connections"""
        try:
            await proxy_handler.handle_client_connection(websocket)
        except Exception as e:
            logger.error(f"Error in proxy connection: {e}")
            raise

    return router


def init_webtool_routes(default_context_cache: ServiceContext) -> APIRouter:
    """
    Create and return API routes for handling web tool interactions.

    Args:
        default_context_cache: Default service context cache for new sessions.

    Returns:
        APIRouter: Configured router with WebSocket endpoint.
    """

    router = APIRouter()

    @router.get("/web-tool")
    async def web_tool_redirect():
        """Redirect /web-tool to /web_tool/index.html"""
        return Response(status_code=302, headers={"Location": "/web-tool/index.html"})

    @router.get("/web_tool")
    async def web_tool_redirect_alt():
        """Redirect /web_tool to /web_tool/index.html"""
        return Response(status_code=302, headers={"Location": "/web-tool/index.html"})

    @router.get("/character-config")
    async def character_config_page():
        """Serve the character configuration UI page"""
        from fastapi.responses import FileResponse

        return FileResponse("frontend/character-config.html")


    @router.get("/live2d-models/info")
    async def get_live2d_folder_info():
        """Get information about available Live2D models"""
        live2d_dir = "live2d-models"
        if not os.path.exists(live2d_dir):
            return JSONResponse(
                {"error": "Live2D models directory not found"}, status_code=404
            )

        valid_characters = []
        supported_extensions = [".png", ".jpg", ".jpeg"]

        for entry in os.scandir(live2d_dir):
            if entry.is_dir():
                folder_name = entry.name.replace("\\", "/")
                model3_file = os.path.join(
                    live2d_dir, folder_name, f"{folder_name}.model3.json"
                ).replace("\\", "/")

                if os.path.isfile(model3_file):
                    # Find avatar file if it exists
                    avatar_file = None
                    for ext in supported_extensions:
                        avatar_path = os.path.join(
                            live2d_dir, folder_name, f"{folder_name}{ext}"
                        )
                        if os.path.isfile(avatar_path):
                            avatar_file = avatar_path.replace("\\", "/")
                            break

                    valid_characters.append(
                        {
                            "name": folder_name,
                            "avatar": avatar_file,
                            "model_path": model3_file,
                        }
                    )
        return JSONResponse(
            {
                "type": "live2d-models/info",
                "count": len(valid_characters),
                "characters": valid_characters,
            }
        )

    @router.get("/api/characters/list")
    async def get_characters_list():
        """Get list of available character configuration files"""
        from .config_manager.utils import scan_config_alts_directory, read_yaml

        try:
            config_alts_dir = default_context_cache.system_config.config_alts_dir
            config_files = scan_config_alts_directory(config_alts_dir)

            # Enhance with conf_uid for each character
            enhanced_configs = []
            for config_info in config_files:
                try:
                    if config_info["filename"] == "conf.yaml":
                        config_data = read_yaml("conf.yaml")
                    else:
                        config_path = os.path.join(
                            config_alts_dir, config_info["filename"]
                        )
                        config_data = read_yaml(config_path)

                    conf_uid = config_data.get("character_config", {}).get(
                        "conf_uid", ""
                    )
                    enhanced_configs.append(
                        {
                            "filename": config_info["filename"],
                            "name": config_info["name"],
                            "conf_uid": conf_uid,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Error reading config {config_info['filename']}: {e}"
                    )
                    continue

            return JSONResponse(
                {
                    "status": "success",
                    "count": len(enhanced_configs),
                    "characters": enhanced_configs,
                }
            )
        except Exception as e:
            logger.error(f"Error listing characters: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @router.get("/api/voices/list")
    async def get_voices_list():
        """Get list of available TTS voices for current provider"""
        try:
            tts_config = default_context_cache.character_config.tts_config
            tts_model = tts_config.tts_model

            voices = []

            # Define common voices for different TTS providers
            if tts_model == "edge_tts":
                voices = [
                    {
                        "id": "en-US-AvaMultilingualNeural",
                        "name": "Ava (English US, Multilingual)",
                        "language": "en-US",
                    },
                    {
                        "id": "en-US-AndrewMultilingualNeural",
                        "name": "Andrew (English US, Multilingual)",
                        "language": "en-US",
                    },
                    {
                        "id": "en-US-EmmaMultilingualNeural",
                        "name": "Emma (English US, Multilingual)",
                        "language": "en-US",
                    },
                    {
                        "id": "en-US-BrianMultilingualNeural",
                        "name": "Brian (English US, Multilingual)",
                        "language": "en-US",
                    },
                    {
                        "id": "en-GB-SoniaNeural",
                        "name": "Sonia (English UK)",
                        "language": "en-GB",
                    },
                    {
                        "id": "en-GB-RyanNeural",
                        "name": "Ryan (English UK)",
                        "language": "en-GB",
                    },
                    {
                        "id": "zh-CN-XiaoxiaoNeural",
                        "name": "Xiaoxiao (Chinese)",
                        "language": "zh-CN",
                    },
                    {
                        "id": "zh-CN-YunxiNeural",
                        "name": "Yunxi (Chinese)",
                        "language": "zh-CN",
                    },
                    {
                        "id": "ja-JP-NanamiNeural",
                        "name": "Nanami (Japanese)",
                        "language": "ja-JP",
                    },
                    {
                        "id": "ja-JP-KeitaNeural",
                        "name": "Keita (Japanese)",
                        "language": "ja-JP",
                    },
                ]
            elif tts_model == "azure_tts":
                voices = [
                    {
                        "id": "en-US-AshleyNeural",
                        "name": "Ashley (English US)",
                        "language": "en-US",
                    },
                    {
                        "id": "en-US-BrandonNeural",
                        "name": "Brandon (English US)",
                        "language": "en-US",
                    },
                    {
                        "id": "zh-CN-XiaoxiaoNeural",
                        "name": "Xiaoxiao (Chinese)",
                        "language": "zh-CN",
                    },
                ]
            elif tts_model == "melo_tts":
                voices = [
                    {"id": "EN-Default", "name": "English Default", "language": "EN"},
                    {"id": "EN-US", "name": "English US", "language": "EN"},
                    {"id": "EN-BR", "name": "English British", "language": "EN"},
                    {"id": "EN-AU", "name": "English Australian", "language": "EN"},
                    {"id": "ZH", "name": "Chinese", "language": "ZH"},
                ]
            else:
                # For other TTS providers, return a generic response
                voices = [
                    {
                        "id": "default",
                        "name": f"Default {tts_model} voice",
                        "language": "auto",
                    }
                ]

            return JSONResponse(
                {
                    "status": "success",
                    "provider": tts_model,
                    "count": len(voices),
                    "voices": voices,
                }
            )
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @router.post("/api/config/update-partial")
    async def update_partial_config(request: PartialConfigUpdate):
        """Update specific aspects of character configuration"""
        try:
            from .config_manager.utils import read_yaml
            from .config_manager.main import Config

            avatar = request.avatar
            character = request.character
            voice = request.voice

            logger.info(
                f"Partial config update request - Avatar: {avatar}, Character: {character}, Voice: {voice}"
            )

            # Start with current config
            current_config = default_context_cache.character_config.model_copy(
                deep=True
            )

            # Load character YAML if specified
            if character:
                config_alts_dir = default_context_cache.system_config.config_alts_dir
                if character == "conf.yaml":
                    config_data = read_yaml("conf.yaml")
                else:
                    config_path = os.path.join(config_alts_dir, character)
                    config_data = read_yaml(config_path)

                # Merge character config
                if "character_config" in config_data:
                    char_config = config_data["character_config"]
                    for key, value in char_config.items():
                        if hasattr(current_config, key):
                            setattr(current_config, key, value)

            # Override avatar if specified
            if avatar:
                current_config.live2d_model_name = avatar
                logger.info(f"Updated Live2D model to: {avatar}")

            # Override voice if specified
            if voice:
                tts_model = current_config.tts_config.tts_model
                if tts_model == "edge_tts":
                    current_config.tts_config.edge_tts.voice = voice
                elif tts_model == "azure_tts":
                    current_config.tts_config.azure_tts.voice = voice
                elif tts_model == "melo_tts":
                    current_config.tts_config.melo_tts.speaker = voice
                logger.info(f"Updated TTS voice to: {voice}")

            # Apply the updated configuration
            full_config = Config(
                system_config=default_context_cache.system_config,
                character_config=current_config,
            )

            await default_context_cache.load_from_config(full_config)

            return JSONResponse(
                {
                    "status": "success",
                    "message": "Configuration updated successfully",
                    "applied": {
                        "avatar": avatar,
                        "character": character,
                        "voice": voice,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Error updating partial config: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @router.post("/asr")
    async def transcribe_audio(file: UploadFile = File(...)):
        """
        Endpoint for transcribing audio using the ASR engine
        """
        logger.info(f"Received audio file for transcription: {file.filename}")

        try:
            contents = await file.read()

            # Validate minimum file size
            if len(contents) < 44:  # Minimum WAV header size
                raise ValueError("Invalid WAV file: File too small")

            # Decode the WAV header and get actual audio data
            wav_header_size = 44  # Standard WAV header size
            audio_data = contents[wav_header_size:]

            # Validate audio data size
            if len(audio_data) % 2 != 0:
                raise ValueError("Invalid audio data: Buffer size must be even")

            # Convert to 16-bit PCM samples to float32
            try:
                audio_array = (
                    np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                    / 32768.0
                )
            except ValueError as e:
                raise ValueError(
                    f"Audio format error: {str(e)}. Please ensure the file is 16-bit PCM WAV format."
                )

            # Validate audio data
            if len(audio_array) == 0:
                raise ValueError("Empty audio data")

            text = await default_context_cache.asr_engine.async_transcribe_np(
                audio_array
            )
            logger.info(f"Transcription result: {text}")
            return {"text": text}

        except ValueError as e:
            logger.error(f"Audio format error: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=400,
                media_type="application/json",
            )
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return Response(
                content=json.dumps(
                    {"error": "Internal server error during transcription"}
                ),
                status_code=500,
                media_type="application/json",
            )

    @router.websocket("/tts-ws")
    async def tts_endpoint(websocket: WebSocket):
        """WebSocket endpoint for TTS generation"""
        await websocket.accept()
        logger.info("TTS WebSocket connection established")

        try:
            while True:
                data = await websocket.receive_json()
                text = data.get("text")
                if not text:
                    continue

                logger.info(f"Received text for TTS: {text}")

                # Split text into sentences
                sentences = [s.strip() for s in text.split(".") if s.strip()]

                try:
                    # Generate and send audio for each sentence
                    for sentence in sentences:
                        sentence = sentence + "."  # Add back the period
                        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
                        audio_path = (
                            await default_context_cache.tts_engine.async_generate_audio(
                                text=sentence, file_name_no_ext=file_name
                            )
                        )
                        logger.info(
                            f"Generated audio for sentence: {sentence} at: {audio_path}"
                        )

                        await websocket.send_json(
                            {
                                "status": "partial",
                                "audioPath": audio_path,
                                "text": sentence,
                            }
                        )

                    # Send completion signal
                    await websocket.send_json({"status": "complete"})

                except Exception as e:
                    logger.error(f"Error generating TTS: {e}")
                    await websocket.send_json({"status": "error", "message": str(e)})

        except WebSocketDisconnect:
            logger.info("TTS WebSocket client disconnected")
        except Exception as e:
            logger.error(f"Error in TTS WebSocket connection: {e}")
            await websocket.close()

    return router
