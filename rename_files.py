#!/usr/bin/env python3

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


RAW_DIR = Path("./raw")
CHARACTER_IDS_FILE = Path("./character_ids.csv")


def load_character_names():
    """Return {(game, character_id): character_name}."""
    characters = {}

    with CHARACTER_IDS_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            game = row["game"]
            character_id = int(row["character_id"])
            character_name = row["character_name"]

            characters[(game, character_id)] = character_name

    return characters


def sanitize_character_name(name):
    """Convert character name to lowercase and replace spaces with underscores."""
    return name.replace(" ", "_").lower()


def get_move_name(frames):
    """Determine the move from player 1's input during the first 3 frames."""

    inputs = []

    for frame in frames[:3]:
        player = frame["players"][0]
        inputs.append(player["input"])

    # We need at least three frames.
    if len(inputs) < 3:
        raise ValueError("Recording contains fewer than 3 frames")

    def is_up(inp):
        return inp["up"] and not inp["down"]

    def is_down(inp):
        return inp["down"] and not inp["up"]

    def is_neutral(inp):
        return not any(
            inp[key]
            for key in (
                "forward",
                "back",
                "up",
                "down",
                "left",
                "right",
                "button_1",
                "button_2",
                "button_3",
                "button_4",
                "special_style",
                "rage",
                "heat",
            )
        )

    first, second, third = inputs

    if is_up(first) and is_neutral(second) and is_neutral(third):
        return "ssl"

    if is_up(first) and is_neutral(second) and is_up(third):
        return "swl"

    if is_down(first) and is_neutral(second) and is_neutral(third):
        return "ssr"

    if is_down(first) and is_neutral(second) and is_down(third):
        return "swr"

    raise ValueError(
        "Unknown move input sequence in first 3 frames"
    )


def get_frames(path):
    """
    Read a recording.

    The recording is expected to contain a JSON array of frame objects.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_existing_filename(path):
    """
    Parse a correctly named recording filename.

    Expected:
        <game>-<version>-<character>-<move>-<index>.json

    Returns:
        (game, version, character, move, index)
        or None if the filename doesn't match.
    """

    pattern = re.compile(
        r"^(.+)-(.+)-(.+)-(ssl|swl|ssr|swr)-(\d+)\.json$"
    )

    match = pattern.match(path.name)

    if not match:
        return None

    game, version, character, move, index = match.groups()

    return game, version, character, move, int(index)


def main():
    character_names = load_character_names()

    # Track which indices are already occupied by correctly named files.
    #
    # Key:
    #   (game, version, character, move)
    #
    # Value:
    #   set of used indices
    used_indices = defaultdict(set)

    json_files = sorted(RAW_DIR.glob("*.json"))

    # First pass:
    # Find files that are already correctly named.
    #
    # This is important because these files must keep their existing
    # indices when the script is run again.
    for path in json_files:
        parsed = parse_existing_filename(path)

        if parsed is None:
            continue

        game, version, character, move, index = parsed
        key = (game, version, character, move)

        used_indices[key].add(index)

    # Second pass:
    # Process only files that aren't already correctly named.
    for path in json_files:
        if parse_existing_filename(path) is not None:
            continue

        try:
            frames = get_frames(path)

            if not frames:
                raise ValueError("Recording contains no frames")

            first_frame = frames[0]

            game = first_frame["game"]
            version = first_frame["game_version"]

            # Player 1 is the first player in the players array.
            player_1 = first_frame["players"][0]
            character_id = player_1["character_id"]

            try:
                character_name = character_names[(game, character_id)]
            except KeyError:
                raise ValueError(
                    f"No character mapping found for "
                    f"game={game!r}, character_id={character_id}"
                )

            character_name = sanitize_character_name(character_name)

            move_name = get_move_name(frames)

            key = (game, version, character_name, move_name)

            # Find the first unused index.
            index = 1
            while index in used_indices[key]:
                index += 1

            new_name = (
                f"{game}-{version}-{character_name}-"
                f"{move_name}-{index}.json"
            )

            destination = path.with_name(new_name)

            # In the unlikely event that the destination already exists,
            # keep searching rather than overwriting it.
            while destination.exists():
                used_indices[key].add(index)
                index += 1

                new_name = (
                    f"{game}-{version}-{character_name}-"
                    f"{move_name}-{index}.json"
                )
                destination = path.with_name(new_name)

            path.rename(destination)

            used_indices[key].add(index)

            print(f"{path.name} -> {destination.name}")

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"Skipping {path.name}: {exc}")


if __name__ == "__main__":
    main()