#!/usr/bin/env python3

import csv
import json
import math
import sys
from pathlib import Path
from collections import defaultdict


RAW_DIR = Path("./raw")
CONVERTED_DIR = Path("./public/data")
CHARACTER_IDS_FILE = Path("./character_ids.csv")


# ---------------------------------------------------------------------------
# Character lookup
# ---------------------------------------------------------------------------

def load_character_names(path: Path):
    """
    Returns:
        {
            (game, character_id): character_name
        }
    """
    result = {}

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required_columns = {"game", "character_id", "character_name"}
        if not required_columns.issubset(reader.fieldnames or set()):
            raise ValueError(
                f"{path} must contain columns: "
                "game, character_id, character_name"
            )

        for row in reader:
            game = row["game"]
            character_id = int(row["character_id"])
            character_name = row["character_name"]

            result[(game, character_id)] = character_name

    return result


# ---------------------------------------------------------------------------
# Vector / coordinate-system helpers
# ---------------------------------------------------------------------------

def vec_sub(a, b):
    return [
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    ]


def vec_add(a, b):
    return [
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    ]


def vec_scale(v, scalar):
    return [
        v[0] * scalar,
        v[1] * scalar,
        v[2] * scalar,
    ]


def vec_length(v):
    return math.sqrt(
        v[0] * v[0] +
        v[1] * v[1] +
        v[2] * v[2]
    )


def vec_normalize(v):
    length = vec_length(v)

    if length == 0:
        raise ValueError("Cannot normalize a zero-length vector.")

    return vec_scale(v, 1.0 / length)


def vec_dot(a, b):
    return (
        a[0] * b[0] +
        a[1] * b[1] +
        a[2] * b[2]
    )


def vec_cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


# ---------------------------------------------------------------------------
# Coordinate transformation
# ---------------------------------------------------------------------------

class CoordinateSystem:
    """
    Defines the coordinate system for one recording.

    Output:
        origin = player 2 centroid

        +X = direction from player 1 centroid toward player 2 centroid

        +Z = original +Z

        +Y = +Z cross +X

    This produces a right-handed coordinate system and preserves scale
    and angles.
    """

    def __init__(self, player1, player2, floor_z):
        self.origin = self.player2_centroid(player2, floor_z)

        p1_centroid = self.player1_centroid(player1, floor_z)
        p2_centroid = self.origin

        # +X points from player 1 to player 2.
        x_axis = vec_sub(p2_centroid, p1_centroid)

        # Centroids should normally have the same Z, so this should be
        # horizontal. We explicitly construct the horizontal direction
        # because the requested X axis is the line between the players.
        x_axis[2] = 0.0
        self.x_axis = vec_normalize(x_axis)

        # Preserve the original world's +Z direction.
        self.z_axis = [0.0, 0.0, 1.0]

        # Right-handed coordinate system:
        # X cross Y = Z
        # therefore Y = Z cross X.
        self.y_axis = vec_cross(self.z_axis, self.x_axis)
        self.y_axis = vec_normalize(self.y_axis)

    @staticmethod
    def player1_centroid(player, floor_z):
        lower_torso = player["collision_spheres"]["lower_torso"]["center"]

        return [
            lower_torso[0],
            lower_torso[1],
            floor_z,
        ]

    @staticmethod
    def player2_centroid(player, floor_z):
        lower_torso = player["collision_spheres"]["lower_torso"]["center"]

        return [
            lower_torso[0],
            lower_torso[1],
            floor_z,
        ]

    def transform_point(self, point):
        """
        Convert a world-space point to the recording's output coordinate
        system.

        Since the output basis vectors are unit vectors, this transformation
        preserves scale and angles.
        """
        relative = vec_sub(point, self.origin)

        return [
            vec_dot(relative, self.x_axis),
            vec_dot(relative, self.y_axis),
            vec_dot(relative, self.z_axis),
        ]

    def transform_rotation(self, world_rotation):
        """
        Convert a world-space angle to the new XY coordinate system.

        Original:
            angle 0     = +X
            angle pi/2  = +Y

        We calculate the world-space direction represented by the angle,
        then project that direction into the new coordinate system and
        calculate its angle there.
        """
        world_direction = [
            math.cos(world_rotation),
            math.sin(world_rotation),
            0.0,
        ]

        output_x = vec_dot(world_direction, self.x_axis)
        output_y = vec_dot(world_direction, self.y_axis)

        return math.atan2(output_y, output_x)


# ---------------------------------------------------------------------------
# Input conversion
# ---------------------------------------------------------------------------

def compress_input(input_data):
    """
    Convert the input object into the requested compact string.

    Order is exactly the order specified in the question.
    """
    parts = []

    if input_data.get("forward"):
        parts.append("f")

    if input_data.get("back"):
        parts.append("b")

    if input_data.get("up"):
        parts.append("u")

    if input_data.get("down"):
        parts.append("d")

    if input_data.get("left"):
        parts.append("l")

    if input_data.get("right"):
        parts.append("r")

    if input_data.get("button_1"):
        parts.append("1")

    if input_data.get("button_2"):
        parts.append("2")

    if input_data.get("button_3"):
        parts.append("3")

    if input_data.get("button_4"):
        parts.append("4")

    if input_data.get("special_style"):
        parts.append("SS")

    if input_data.get("rage"):
        parts.append("R")

    if input_data.get("heat"):
        parts.append("H")

    return "".join(parts)


# ---------------------------------------------------------------------------
# Move identification
# ---------------------------------------------------------------------------

def identify_move(frames, source_path):
    """
    Determine the move from player 1's first three inputs.

    Expected sequences:

        up,   neutral, neutral -> SSL
        up,   neutral, up      -> SWL
        down, neutral, neutral -> SSR
        down, neutral, down    -> SWR
    """

    if len(frames) < 3:
        raise ValueError(
            f"{source_path}: recording contains fewer than 3 frames."
        )

    players = []

    for frame_index in range(3):
        frame = frames[frame_index]

        if len(frame.get("players", [])) < 2:
            raise ValueError(
                f"{source_path}: frame {frame_index} has fewer than "
                "two players."
            )

        players.append(frame["players"][0])

    inputs = [
        compress_input(player["input"])
        for player in players
    ]

    sequences = {
        ("u", "", ""): "SSL",
        ("u", "", "u"): "SWL",
        ("d", "", ""): "SSR",
        ("d", "", "d"): "SWR",
    }

    key = tuple(inputs)

    if key not in sequences:
        raise ValueError(
            f"{source_path}: unexpected first-three-frame input sequence: "
            f"{inputs!r}. Expected one of "
            f"['u,,', 'u,,u', 'd,,', 'd,,d']."
        )

    return sequences[key]


# ---------------------------------------------------------------------------
# Frame conversion
# ---------------------------------------------------------------------------

def convert_hurt_cylinders(player, coordinate_system):
    result = {}

    for name, value in player["hurt_cylinders"].items():
        cylinder = value["cylinder"]

        result[name] = {
            "center": coordinate_system.transform_point(cylinder["center"]),
            "radius": cylinder["radius"],
            "half_height": cylinder["half_height"],
        }

    return result


def convert_collision_spheres(player, coordinate_system):
    result = {}

    for name, value in player["collision_spheres"].items():
        result[name] = {
            "center": coordinate_system.transform_point(value["center"]),
            "radius": value["radius"],
        }

    return result


def convert_frame(frame, coordinate_system):
    player = frame["players"][0]

    return {
        "animation_id": player["animation_id"],
        "animation_frame": player["animation_frame"],
        "input": compress_input(player["input"]),
        "rotation": coordinate_system.transform_rotation(
            player["rotation"]
        ),
        "hurt_cylinders": convert_hurt_cylinders(
            player,
            coordinate_system,
        ),
        "collision_spheres": convert_collision_spheres(
            player,
            coordinate_system,
        ),
    }


# ---------------------------------------------------------------------------
# Recording conversion
# ---------------------------------------------------------------------------

def convert_recording(frames, source_path, character_names):
    if not frames:
        raise ValueError(f"{source_path}: JSON array is empty.")

    first_frame = frames[0]

    game = first_frame["game"]
    game_version = first_frame["game_version"]

    if len(first_frame.get("players", [])) < 2:
        raise ValueError(
            f"{source_path}: first frame has fewer than two players."
        )

    player1 = first_frame["players"][0]
    player2 = first_frame["players"][1]

    character_id = player1["character_id"]

    character_key = (game, character_id)

    if character_key not in character_names:
        raise ValueError(
            f"{source_path}: no character mapping found for "
            f"game={game!r}, character_id={character_id}."
        )

    character_name = character_names[character_key]

    move = identify_move(frames, source_path)

    floor_z = first_frame["floor_z"]

    if floor_z is None:
        raise ValueError(
            f"{source_path}: first frame has floor_z=null."
        )

    coordinate_system = CoordinateSystem(
        player1,
        player2,
        floor_z,
    )

    converted_frames = [
        convert_frame(frame, coordinate_system)
        for frame in frames
    ]

    return {
        "game": game,
        "game_version": game_version,
        "character_id": character_id,
        "character_name": character_name,
        "move": move,
        "frames": converted_frames,
    }


# ---------------------------------------------------------------------------
# File naming
# ---------------------------------------------------------------------------

def output_filename(game, game_version, character_name, move):
    name = f"{game}-{game_version}-{character_name}-{move}.json"

    # Replace spaces with underscores and lowercase everything.
    return name.replace(" ", "_").lower()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

    character_names = load_character_names(CHARACTER_IDS_FILE)

    json_files = sorted(RAW_DIR.glob("*.json"))

    if not json_files:
        print(f"No .json files found in {RAW_DIR}")
        return 1

    # Key:
    #   (game, game_version, character_id, move)
    #
    # Value:
    #   converted output object containing all samples.
    grouped = {}

    errors = 0

    for source_path in json_files:
        print(f"Processing {source_path}...")

        try:
            with source_path.open("r", encoding="utf-8") as f:
                frames = json.load(f)

            if not isinstance(frames, list):
                raise ValueError(
                    "top-level JSON value must be an array."
                )

            recording = convert_recording(
                frames,
                source_path,
                character_names,
            )

            key = (
                recording["game"],
                recording["game_version"],
                recording["character_id"],
                recording["move"],
            )

            if key not in grouped:
                grouped[key] = {
                    "game": recording["game"],
                    "game_version": recording["game_version"],
                    "character_id": recording["character_id"],
                    "character_name": recording["character_name"],
                    "move": recording["move"],
                    "frames": [],
                }

            # Each source recording becomes one sample.
            grouped[key]["frames"].append(recording["frames"])

        except Exception as exc:
            errors += 1
            print(
                f"ERROR: skipping {source_path}: {exc}",
                file=sys.stderr,
            )

    # Write one file per (game, version, character, move).
    for key, output in sorted(grouped.items()):
        filename = output_filename(
            output["game"],
            output["game_version"],
            output["character_name"],
            output["move"],
        )

        destination = CONVERTED_DIR / filename

        with destination.open("w", encoding="utf-8") as f:
            json.dump(
                output,
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            f.write("\n")

        print(
            f"Wrote {destination} "
            f"({len(output['frames'])} samples)"
        )

    print()
    print(f"Input files:  {len(json_files)}")
    print(f"Output files: {len(grouped)}")
    print(f"Skipped:      {errors}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())