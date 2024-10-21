from dialoguekit.platforms.flask_socket_platform import FlaskSocketPlatform

from src.bot.music_agent import MusicAgent

platform = FlaskSocketPlatform(MusicAgent)
platform.start()
