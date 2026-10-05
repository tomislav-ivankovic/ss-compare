# SS Compare

A slop coded single page web application that enables users to compare sideways movement between different characters and different (T7 and T8) games.
While the code inside this repository is quickly slop coded using AI, the raw data used by the application is captured using [Irony](https://github.com/tomislav-ivankovic/Irony), a fully handcrafted application.

Currently, only the non-DLC character's sidesteps and sidewalks in both directions are supported.
If you want to add support for DLC characters, feel free to record the DLC character's sidesteps/sidewalks and do a pull request.

## How it works

### Raw recordings

Using [Irony](https://github.com/tomislav-ivankovic/Irony) sidesteps and sidewalks are recorded and saved in JSON format.
These recordings are placed in the `raw` directory of this repository.
For each supported character of each game, 5 recordings of SSL, SSR, SWL and SWR are saved.
The moves are executed with perfect input using the Tool Assisted Input feature of Irony.
Since all that data is around 1GB in size, most of it is gitignored.
Only a few files are left on Git as a reference to others on how to record raw data for additional characters.
T8 recordings are done on the Coloseum stage and T7 recordings on Infinite Azure.
Player 1 is the character that is always sidestepping / sidewalking and player 2 is always a idle Jin.
Recordings are done in practice mode, before each recording the characters are restarted to the default restart position of the practice mode.
Tool assisted input feature of Irony automatically clears the old recording, starts a new recording, executes frame perfect inputs and stops the recording.
The recording is then saved in JSON format using whatever file name Irony chooses by default.

### Renaming raw recordings

The files are then renamed to match the format `<game>-<version>-<character_name>-<move_name>-<index>.json`.
This is done by running the python script:
```bash
python3 rename_files.py
```
The script uses `character_ids.csv` to figure out the names of characters.

### Converting raw recordings to data files

The raw recordings are then combined and converted into files that only store data that this application needs, in the shape that this application prefers.
This is done by running the python script:
```bash
python3 convert_files.py
```
This script creates the files inside `./public/data`.

### Creating a catalog

The next step is to create a catalog that the application can use to enumerate files inside `./public/data`.
This is done by running the python script:
```bash
python3 make_catalog.py
```
This script creates the `./public/catalog.json` file.

### Deploy to Web

Finally the contents of the `./public` directory are deployed to Web as static Web content.

## Adding new characters

To add support for additional characters first open the nonignored files from `./raw` directory with Irony and figure out what inputs are used to record them.
You can use the "Import From Recording" feature of "Tool Assisted Input" to populate the table with the same inputs as the recording.
Record and save 5 recordings of SSL, SSR, SWL and SWR and place them into the `./raw` directory.
Add the new character name(s) to `./character_ids.csv`.
Finally, run the python scripts:
```bash
python3 rename_files.py
python3 convert_files.py
python3 make_catalog.py
```
After the scripts are done executing, the code inside `./public/index.html` should have no problems using the new characters.