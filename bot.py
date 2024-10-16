from dialoguekit.platforms.terminal_platform import TerminalPlatform

from src.bot.music_agent import MusicAgent

platform = TerminalPlatform(MusicAgent)
platform.start()
