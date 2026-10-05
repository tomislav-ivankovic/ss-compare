import json
from pathlib import Path


DATA_DIR = Path("./public/data")
CATALOG_FILE = Path("./public/catalog.json")


def main():
    catalog = []

    for json_file in sorted(DATA_DIR.glob("*.json")):
        with json_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        catalog.append({
            "game": data["game"],
            "game_version": data["game_version"],
            "character_id": data["character_id"],
            "character_name": data["character_name"],
            "move": data["move"],
            "file_name": json_file.name,
        })

    with CATALOG_FILE.open("w", encoding="utf-8") as file:
        json.dump(catalog, file, separators=(",", ":"), ensure_ascii=False)
        file.write("\n")


if __name__ == "__main__":
    main()