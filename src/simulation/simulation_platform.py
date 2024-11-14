"""Simulation platform to connect simulator and agent."""

import logging
import sys
from typing import Any, Dict, Type

from dialoguekit.connector import DialogueConnector
from dialoguekit.core import Utterance
from dialoguekit.participant import Agent
from dialoguekit.participant.user import User
from dialoguekit.platforms import Platform


class SimulationPlatform(Platform):
    def __init__(self, agent_class: Type[Agent]) -> None:
        """Initializes the simulation platform.

        Args:
            agent_class: Agent class.
            agent_config: Configuration of the agent. Defaults to empty
              dictionary.
        """
        super().__init__(agent_class)

    def start(self) -> None:
        """Starts the simulation platform.

        It creates the agent.
        """
        self.agent = self.get_new_agent()

    def connect(
        self,
        user_id: str,
        simulator_class: Type[User],
        simulator_config: Dict[str, Any] = {},
    ) -> None:
        """Connects a user simulator to an agent.

        Args:
            user_id: User ID.
            simulator_class: User simulator class.
            simulator_config: Configuration of the user simulator. Defaults to
              empty dictionary.

        Raises:
            Exception: If an error occurs during the dialogue.
        """
        self._active_users[user_id] = simulator_class(
            user_id, **simulator_config
        )
        dialogue_connector = DialogueConnector(
            agent=self.agent,
            user=self._active_users[user_id],
            platform=self,
        )

        try:
            dialogue_connector.start()
        except Exception as e:
            print(e)
            logging.error(e, exc_info=True)
            tb = sys.exc_info()
            dialogue_connector._dialogue_history._metadata.update(
                {
                    "error": {
                        "error_type": type(e).__name__,
                        "trace": str(e.with_traceback(tb[2])),
                    }
                }
            )
            return

    def display_agent_utterance(
        self, utterance: Utterance, agent_id: str, user_id: str
    ) -> None:
        """Displays an agent utterance.

        Args:
            utterance: An instance of Utterance.
            agent_id: Agent ID.
            user_id: User ID. Defaults to None.
        """
        print(f"\033[1m {agent_id}\033[0m: {utterance.text}")

    def display_user_utterance(
        self, utterance: Utterance, user_id: str
    ) -> None:
        """Displays a user utterance.

        Args:
            utterance: An instance of Utterance.
            user_id: User ID.
        """
        print(f"\033[1m {user_id}\033[0m: {utterance.text}")
