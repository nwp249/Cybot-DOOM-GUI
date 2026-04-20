# How to run
Super easy to use with the VSCode python extension.

Run program on the cybot, start the gui whenever. It will work as long as you can actually communicate with the cybot.

## Python version:
3.12.0 (Microsoft Store)

## Necessary packages:
pygame, pyopengl, numpy, pillow

## Sources:
I took the main_opengl script and the engine_opengl from the following repository: https://github.com/jordansavant/doomengine.python

Any unmodified files are marked as such in the first line, others I commented my changes with 2 hashes. 
Took a little reverse engineering and refactoring but I was able to make it do the necessary things eventually. 
Wouldn't call it particularly thread safe but it has the capability to counteract that.

## Examples:
Included are text examples of the format of objects, object definitions, sensor scans, and game state.
These are also overwritten on every scan or event.

Video link: https://youtu.be/4BwXWBsaIUw?si=iwfoijSl9GdZOlE1

### Screenshots
This screenshot is our game state from the end of our demo, in the destination zone, after resetting the field to get a cleaner view.
The walls do not represent the test field boundaries.

<img src="./assets/screenshot.png">

#### Minimap cybot sprite

<img src="./assets/cybot_sprite.png" height="200dp" width="235dp">

#### Victory screen
<img src="./assets/success.jpg">