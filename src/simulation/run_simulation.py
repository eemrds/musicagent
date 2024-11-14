"""Command line tool to run simulations with the MusicCRS agent."""

import argparse
import logging

from src.bot.music_agent import MusicAgent
from src.simulation.naive_user_simulator import NaiveUserSimulator
from src.simulation.simulation_platform import SimulationPlatform


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Simulation.")
    parser.add_argument(
        "--num_simulations",
        type=int,
        default=1,
        help="Number of simulations to run. Defaults to 1.",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="steve",
        help="User name. Defaults to 'steve'.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    platform = SimulationPlatform(MusicAgent)
    logging.info(f"Running {args.num_simulations} simulations")
    for i in range(1, args.num_simulations + 1):
        # Note: This creates a new agent each time to avoid state issues.
        # Ideally, platform.start() could be called outside the loop, but then # the agent needs to be reset between simulations.
        platform.start()
        print(f"\n--- Staring simulation {i} ---\n")
        platform.connect(args.user, NaiveUserSimulator)
        platform.disconnect(args.user)
        print(f"\n--- Finished simulation {i} ---\n")
    logging.info("All simulations finished")
