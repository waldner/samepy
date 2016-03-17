# samepy

#### Simple samegame implementation in python+pygame for learning purposes

Writing a game is a good way to learn and/or practice a new language, so here it is: a [samegame](https://en.wikipedia.org/wiki/SameGame) implementation written in [Python](https://www.python.org/) using the good [pygame library](http://www.pygame.org/).

The only dependency is the pygame library. The game should work with python2 and python3, on all the platforms where python is available (tested on Linux and Windows).

Screenshot:

![same.py screenshot](https://github.com/waldner/samepy/blob/master/same-screenshot.png "same.py screenshot")

Running the program with **-h** or **--help** shows the supported options:

```
$ ./same.py -h
Usage:
same.py [ -h|--help ]
same.py [ -l|--load f ] [ -g|--gameid n ] [ -c|--colors n ] [ -s|--cellsize n ] [ -x|--cols n ] [ -y|--rows n ]

-h|--help        : this help
-l|--load f      : load saved game from file "f" (disables all options)
-g|--gameid n    : play game #n (default: random betwen 0 and 100000)
-c|--colors n    : use "n" colors (default: 5)
-s|--cellsize n  : force a cellsize of "n" pixels (default: 30)
-x|--cols n      : force "n" columns (default: 17)
-y|--rows n      : force "n" rows (default: 15)
```

During the game, the following keybindings are supported:

```
u       undo move
ctrl-r  redo move
r       restart current game (same number)
n       start new game (different number)
q/ESC   exit the game
ctrl-s  save the current state of the game (for later retrieval with --load)
1-3     change the color scheme
a       toggle highlighting of current cell group
```

#### Some random notes:

* At any time, the current state of the game is held in a big dictionary called gameinfo. When saving the game, this data structure is serialized to a file using version 2 of the pickle protocol (so it can be read both from python2 and python3). Games are saved in the current directory using a filename like "_samepy.64622-20.sav" where the two numbers indicate respectively the game number and the current move at the time of saving.
* It would have been nice to use some more standard format (eg JSON), but the data structures used here cannot be serialized into JSON (eg dictionaries with tuples as keys). (Ok, I cheated: with some work it is in fact possible using custom encoders and decoders, but here it's probably not worth the effort.)
* It is possible to override the default values for cellsize, rows and column, even all three at the same time (within reason). If overriding one or more of these values results in too small/big cells, or too few/many rows or columns, an error is printed.
* The game number that can be specified with -g is used to seed the random number generator before (randomly) populating the game board, so, on the same machine and with the same python version, the same number will always produce the same game layout. If the python major version changes, that is no longer true: game #100 with python2 is different from game #100 with python3. It might even change between, say, python3.3 and python3.4 (although it seems not to), or when using the same python version on different machines; more information is welcome, as usual.
* By default 5 colors are used; this can be changed with the -c command line switch. The fewer the colors, the easier it is to solve the game; with two colors success is practically certain. There are three different palettes (ie, color schemes), that can be activated during the game with the keys 1-3. If you don't like them (I don't like them too much, but I'm also too lazy), or want to add more palettes, it's easy to find the place in the code where they can be changed.
* There is more than one way to keep game history for undo/redo purposes. One could just remember the moves made by the player (ie the groups of cells that were removed at each turn), and upon undo/redo go backwards/forwards in this history, each time readding/removing a group of cells and recalculating the resulting board after the insertion or removal. This needs little memory to save the game history, but needs some calculation for each undo and redo. It's true that one of those two functions (the one that removes the cells) must be written anyway, to allow the player to actually play. However, the approach followed here is to separately save each board layout in sequence, and designate one of those states as "current" using an index into the sequence. This way, undo and redo are as simple as updating this index to point to the previous or the next saved state respectively (ie, subtracting or adding 1 to it). Restarting the game is (almost) just a matter of setting the pointer to move 0. So undo/redo/restart are very simple, but more memory is used to store all the information (this is also apparent by the size of the serialized saved game). In retrospective, if I were to rewrite it, I wold probably use the first approach.
* The scoring system is quite simple: removing a group of N cells scores N^2 points. This differs slightly from other implementations of the game.
* For some reason, the game is slow on machines with few resources. The highlighting of the current cell group, for example, has a certain lag, and so has the removal of cells following a click. It is possible to toggle highlighting on/off using the a key during the game, which makes it a bit better. The algorithms are certainly not optimal, however I think that alone doesn't explain these delays. Is it really all redrawing overhead? More info welcome.
