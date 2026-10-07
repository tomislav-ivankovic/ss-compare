Create a single page static web content website called "SS Compare".
The website is used to compare different sidesteps/sidewalks of different characters inside a fighting game.
Inside the static web content you have access to static `.json` files that contain the data that the website compares.
First you have `./catalog.json` that has the following shape:
```
[{
    game: string,
	game_version: string,
	character_id: number,
	character_name: string,
	move: string,
	file_name: string,
}]
```
This is the list of things that can be compared with each other. 
You can imagine the primary key of this data to be (game, version, character, move) and the actual value of that data to be
stored inside the file named with `file_name`.
The files behind the each element of the catalog can be found inside `./data/<file_name>`.
The `.json` file extension of these files is already included inside the `file_name`.
The files inside the data directory have the following shape:
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
The first dimension of the 2D array `frames` contains multiple recordings of the same move being performed.
Think of it as multiple samples of the same measurement so that the measurement error can be described.
Every sample has same number of frames and the frames on the same index are directly comparable to measure error.
The second dimension of the array contains the recorded frame where each element is a object that represents the frame.
On the website the user needs to be able to choose from catalog what N moves he wants to compare between each other.
Since there is a lot of options, the selection should be done using a fuzzy text search autosuggest style interface. 
The website should then compare these moves by visually rendering them inside the same 3D world.
Each move should be should be rendered with a different color that the user can change.
The things that need to be rendered are hurt cylinders, a skeleton and a rotation indicator.
Hurt cylinders should be rendered with a solid transparent color.
The cylinders are axis aligned meaning the bases of these cylinders point towards up and down (Z+ and Z-).
To render the skeleton, centers of specific hurt cylinders and or collision spheres need to be connected together.
`hurt_cylinders` object contains the following keys:
 - left_ankle 
 - right_ankle
 - left_hand
 - right_hand
 - left_knee
 - right_knee
 - left_elbow
 - right_elbow
 - head
 - left_shoulder
 - right_shoulder
 - upper_torso
 - left_pelvis
 - right_pelvis
`collision_spheres` object contains the following keys:
 - neck
 - left_elbow
 - right_elbow
 - lower_torso
 - left_knee
 - right_knee
 - left_ankle
 - right_ankle
To draw the skeleton, lines need to be drawn between the following:
 - head <-> neck
 - neck <-> upper_torso
 - upper_torso <-> left_shoulder
 - upper_torso <-> right_shoulder
 - left_shoulder <-> left_elbow
 - right_shoulder <-> right_elbow
 - left_elbow <-> left_hand
 - right_elbow <-> right_hand
 - upper_torso <-> lower_torso
 - lower_torso <-> left_pelvis
 - lower_torso <-> right_pelvis
 - left_pelvis <-> left_knee
 - right_pelvis <-> right_knee
 - left_knee <-> left_ankle
 - right_knee <-> right_ankle
When same body part exists on both hurt cylinders and collision spheres use hurt cylinders.
The rotation indicator is a line that starts from characters centroid and points towards the `rotation`.
The X and Y coordinate of the centroid is at the lower torso collision sphere center's X and Y and Z is 0.
Length of the line should be 100 units.
The `rotation` is defined in radians where 0 points towards X+ and pi/2 points towards Y+.
Since there are multiple samples of the same recording, visualize the average.
To visualize the error, draw a transparent skeleton on top of the average one and make it's thickness represent 3 standard deviations.
Independent of the compared moves, draw 2 grids, one on Z=0 plane and one on Y=0 plane.
The 3D render should display the same frame from all compared moves at once.
The user needs to have a slider that selects what frame is currently being displayed.
If the compared moves have different number of frames and the user selects a frame index that is outside some of the move's range,
the website should display the last available frame for the moves that have index outside range.
The user should also have a checkbox/toggle that mirrors the display of the toggled move on the Y axis.
This is so that moves that travel towards the left and the right can be compared as if they were traveling to the same direction.
Also a checkboxs/toggles that enable/disable display of hurt cylinders, skeleton and a rotation indicator are required.
On the legend, display the `animation_id`, `animation_frame` and `input` of the current frame for every compared move.
These values should be equal for all samples and if they are not display `?` as value.
Additionally, on the legend for every compared move, display a `Angle` value.
Calculate this value by calculating the angle between the [-1, 0, 0] vector with the vector that starts at origin and points towards the average samples centroid.
Display the angle in degrees.
Finally the user needs to have some basic controls of the camera so that she/he can inspect the visualization from whatever angle he/she chooses. 
When implementing all of this use plain HTML/JavaScript/CSS without using npm. 
For 3D visualization you can use a JavaScript library linked from a script tag but avoid libraries that have a lot of dependencies (including transitive dependencies).
All this data is provided inside the Unreal Engine's coordinating system, so configure the camera so that the axes are configured according to that fact.
 