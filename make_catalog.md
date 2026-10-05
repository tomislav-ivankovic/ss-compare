Inside `./public/data` directory there are many `.json` files with this shape:
```
{
	game: string,
	game_version: string,
	character_id: number,
	character_name: string,
	move: string,
	frames: [[{
		animation_id: number,
		animation_frame: number,
		input: string,
		rotation: number,
		hurt_cylinders: { <name>: {
			center: [x: number, y: number, z: number],
			radius: number,
			half_height: number
		}},
		collision_spheres: { <name>: {
		    center: [x: number, y: number, z: number],
			radius: number,
		}},
	}]]
}
```
I need you to write a python script that reads all the json files inside that directory and produces a file `./public/catalog.json`.
This fille needs to catalog all these files so its content needs to be a array of objects where each object represents one file.
The object needs to have the following shape: 
```
{
    game: string,
	game_version: string,
	character_id: number,
	character_name: string,
	move: string,
	file_name: string,
}
```
Copy the values of `game`, `game_version`, `character_id`, `character_name` and `move` from the individual files.
Use just the name of the file with extension (no absolute or relative paths to the file) as the value of `file_name`.