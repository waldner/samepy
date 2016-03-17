#!/usr/bin/python

# same.py: simple samegame implementation in pythpn + pygame.
# More an exercise to learn python better than anything else.

# Copyright Davide Brini, 16/07/2014
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


import random, time, pygame, sys, pprint, copy, getopt, os, pickle
from pygame.locals import *


def terminate(msg = None, usage = False, exitcode = 0):

  if msg:
    printErr(msg)
    if usage:
      printErr('')

  if usage:
    showUsage()

  pygame.quit()
  sys.exit(exitcode)


def printErr(msg):
  sys.stderr.write(msg + '\n')


def setPalette(pnumber):
  global COLORS
  COLORS = ()
  for color in PALETTE[pnumber - 1]:
    COLORS = COLORS + ( ( color, lighten(color, 0.2) ), )

# given a RGB tuple, returns a version
# that is lighter by a factor "factor"
def lighten(color, factor):
  return ( int((255 - color[0]) * factor + color[0]),
           int((255 - color[1]) * factor + color[1]),
           int((255 - color[2]) * factor + color[2]) )


# undocumented - ctrl+d
def dumpCurrentBoard():
  for line in map(lambda j: ''.join(map(str,j)), zip(*gameinfo['board'][gameinfo['curmove']])):
    print (line)


def saveGame():

  savefile = ('_samepy.%s-%s.sav' % (gameinfo['gameid'], gameinfo['curmove']))

  try:
    with open(savefile, mode = 'wb') as f:
      pickle.dump(gameinfo, f, protocol = 2)
  except Exception as e:
    printErr(('Error saving file: %s' % str(e)))
  else:
    print ('Saved game to file %s' % savefile)


def loadGame(savefile):

  global gameinfo

  try:
    with open(savefile, 'rb') as f:
      gameinfo = pickle.load(f)
  except Exception as e:
    terminate(msg = ('Error loading from file: %s' % str(e)), exitcode = 1) 
  else:
    pygame.display.set_caption('SamePy (#' + str(gameinfo['gameid']) + ')')


# adjust values according to user arguments, if needed
def calcBoard(overridecellsize, overridex, overridey):

  if overridecellsize == False:

    if overridex == True and overridey == False:

      # user wants a specific number of columns, recalculate cellsize
      # based on that, and number of rows based on cell size

      gameinfo['cellsize'] = int((WINDOWWIDTH - gameinfo['rightmargin']) / gameinfo['boardcols'])
      gameinfo['boardrows'] = int((WINDOWHEIGHT - gameinfo['topmargin']) / gameinfo['cellsize'])

      print ('x overridden, Recalculating cellsize to be %s, %s columns, %s rows' % (gameinfo['cellsize'], gameinfo['boardcols'], gameinfo['boardrows']))

    elif overridex == False and overridey == True:

      # user wants a specific number of rows, recalculate cellsize
      # based on that, and number of columns based on cell size

      gameinfo['cellsize'] = max(1, int((WINDOWHEIGHT - gameinfo['topmargin']) / gameinfo['boardrows']))
      gameinfo['boardcols'] = int((WINDOWWIDTH - gameinfo['rightmargin']) / gameinfo['cellsize'])

      print ('y overridden, Recalculating cellsize to be %s, %s columns, %s rows' % (gameinfo['cellsize'], gameinfo['boardcols'], gameinfo['boardrows']))

    elif overridex == True and overridey == True:

      # see which cellsize would result from x override
      cellsizex = max(1, int((WINDOWWIDTH - gameinfo['rightmargin']) / gameinfo['boardcols']))

      # see which cellsize would result from y override
      cellsizey = max(1, int((WINDOWHEIGHT - gameinfo['topmargin']) / gameinfo['boardrows']))

      # take the smallest
      gameinfo['cellsize'] = min(cellsizex, cellsizey)

      print ('both x and y overridden, cellsize is minimum between %s and %s (%s)' % (cellsizex, cellsizey, gameinfo['cellsize']))
 
    else:
      # nothing was overridden, keep default values
      pass


  # if user specified cellsize, recalculate rows and columns if possible
  # to fill board as much as possible
  else:

    if overridex == False:
      gameinfo['boardcols'] = int((WINDOWWIDTH - gameinfo['rightmargin']) / gameinfo['cellsize'])

    if overridey == False:
      gameinfo['boardrows'] = int((WINDOWHEIGHT - gameinfo['topmargin']) / gameinfo['cellsize'])

    # if everything is overridden, do nothing and hope user
    # specified sane values (checked later)


def getNewBoard(gameid = None):

  # if no gameid is given, generate a random one
  if gameid == None:
    gameid = random.randint(0, MAXGAMENO)

  random.seed(gameid)

  gameinfo['board'] = {}
  gameinfo['score'] = {}

  gameinfo['gameid'] = gameid

  # to support undo/redo
  gameinfo['curmove'] = 0
  gameinfo['maxmove'] = 0

  # actually fill the board
  board = []

  for c in range(gameinfo['boardcols']):
    col = []

    for r in range(gameinfo['boardrows']):
      colorNo = random.randint(0, gameinfo['ncolors'] - 1)
      col.append(colorNo)

    board.append(col)

  gameinfo['board'][gameinfo['curmove']] = board

  calculateAllGroups()

  gameinfo['score'][gameinfo['curmove']] = 0
  gameinfo['mousex'] = 0
  gameinfo['mousey'] = 0
  gameinfo['lastnremoved'] = 0

  pygame.display.set_caption('SamePy (#' + str(gameinfo['gameid']) + ')')


def gameWon():
  return gameinfo['cellsleft']['total'] == 0

def gameOver():
  return gameinfo['maxgroupsize'] < 2

# Convert the given xy board coordinates to
# on-screen xy coordinates
def log2PhysCoord(cellx, celly):
  return (cellx * gameinfo['cellsize'], (celly * gameinfo['cellsize']) + gameinfo['topmargin'])


# Convert the given physical xy coordinates to a specific cell
# (if applicable)
def phys2LogCoord(pixelx, pixely):
  if (pixelx < (WINDOWWIDTH - gameinfo['rightmargin'])) and (pixely >= gameinfo['topmargin']):
    return (int(pixelx / gameinfo['cellsize']), int((pixely - gameinfo['topmargin']) / gameinfo['cellsize']))
  else:
    return (None, None)


# draw a single cell at logical coordinates (cellx, celly)
def drawCell(cellx, celly, colorNo, highlight = False, pixelx = None, pixely = None, cellsize = None):

  if colorNo == BLANK:
    return

  if cellsize == None:
    cellsize = gameinfo['cellsize']

  color = COLORS[colorNo][0]
  if highlight == True:
    color = COLORS[colorNo][1]

  # calculate coords only if not overridden
  if (pixelx == None):
    pixelx, pixely = log2PhysCoord(cellx, celly)

  pygame.draw.rect(DISPLAYSURF, color, (pixelx, pixely, cellsize - 1, cellsize - 1))


def drawBoard(curgroup, animations = False):

  dohl = 0
  if animations and curgroup and len(curgroup) > 1:
    dohl = 1        # do not highlight groups of just one cell

  # draw the individual boxes on the board, highlight those belonging to current group
  for col in range(gameinfo['boardcols']):
    for row in range(gameinfo['boardrows']):
      drawCell(col, row, gameinfo['board'][gameinfo['curmove']][col][row], (dohl and (col, row) in curgroup))


def drawText(text, pixelx, pixely, where = 'topleft', color = None, font = 'basic'):

  if color == None:
    color = TEXTCOLOR

  if (font == 'basic'):
    textSurf = BASICFONT.render(text, True, color)
  else:
    textSurf = BIGFONT.render(text, True, color)
    
  textRect = textSurf.get_rect()

  if (where == 'topleft'):
    textRect.topleft = (pixelx, pixely)
  elif (where == 'center'):
    textRect.center = (pixelx, pixely)

  DISPLAYSURF.blit(textSurf, textRect)


# draws score and status/info bits in the space at the right
def drawScore():

  # common x for everything here
  x = WINDOWWIDTH - SCOREMARGIN + 15

  # draw the score text
  drawText('Score: %s' % gameinfo['score'][gameinfo['curmove']], x, 20)
  drawText('Last: %s (%s)' % (getPoints(gameinfo['lastnremoved']), gameinfo['lastnremoved']), x, 40)

  # draw the remaining cells status

  totcellsleft = 0
  totgroupsleft = 0

  for colorNo in range(0, gameinfo['ncolors']):
    yforcell = 90 + colorNo * (STATUSCELLSIZE + 10)
    drawCell(0, 0, colorNo, pixelx = x, pixely = yforcell, cellsize = STATUSCELLSIZE)
    drawText('x %s  (%s)' % (gameinfo['cellsleft'][colorNo], len(gameinfo['groupsleft'][colorNo])), x + STATUSCELLSIZE + 5, yforcell + 5)

  # tot remaining (cells and groups)
  drawText('Total :  %s  (%s)' % (gameinfo['cellsleft']['total'], len(gameinfo['groupsleft']['total'])), x, 90 + gameinfo['ncolors'] * (STATUSCELLSIZE + 10))

  # draw help, stupid trick to keep key order
  h = { '0u': 'undo', '1ctrl-r': 'redo', '2r': 'restart', '3n': 'new', '4q/ESC': 'exit', '5ctrl-s': 'save', '61-3': 'palette', '7a': ('hl (%s)' % ('On' if animations else 'Off')) }

  for item in sorted(h):
    n = int(item[0])
    drawText(item[1:], x,      320 + (15 * n), color = WHITE)
    drawText(h[item],  x + 42, 320 + (15 * n), color = GRAY)

  drawText('Pos: (%s,%s)' % (phys2LogCoord(gameinfo['mousex'], gameinfo['mousey'])), x, 450)



def waitForEvent(context):

  while True:
    event = pygame.event.wait()

    # window close/ESC/q always terminate, regardless of context
    if event.type == QUIT or (event.type == KEYDOWN and (event.key == K_ESCAPE or event.key == K_q)):
      terminate()

    if event.type == MOUSEMOTION:
      return event

    if (context == 'endgame'):
      # only "r", "u" and "n" allowed
      if (event.type == KEYDOWN) and (event.key == K_r or event.key == K_u or event.key == K_n):
        return event    
    else:
      return event


# informational text at the center of the window (eg game over)
def showTextScreen(text, context):

  # Draw the text drop shadow
  drawText(text, int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2), where = 'center', color = TEXTSHADOWCOLOR, font = 'big')
  drawText(text, int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3, where = 'center', color = TEXTCOLOR, font = 'big')

  pygame.display.update()


# implement whatever scoring algorithm here
def getPoints(nremoved):
  return nremoved ** 2


def undoMove():
  if gameinfo['curmove'] > 0:
    gameinfo['curmove'] -= 1
    calculateAllGroups()


def redoMove():
  if gameinfo['curmove'] < gameinfo['maxmove']:
    gameinfo['curmove'] += 1
    calculateAllGroups()



# return the neighbors of elem which are of its
# same color
def getImmediateNeighbors(cellx, celly):

  board = gameinfo['board'][gameinfo['curmove']]
  colorNo = board[cellx][celly]

  neighbors = []

  # left neighbor
  if cellx > 0 and board[cellx - 1][celly] == colorNo:
    neighbors.append( (cellx - 1, celly) )

  # right neighbor
  if cellx < gameinfo['boardcols'] - 1 and board[cellx + 1][celly] == colorNo:
    neighbors.append( (cellx + 1, celly) )

  # upper neighbor
  if celly > 0 and board[cellx][celly - 1] == colorNo:
    neighbors.append( (cellx, celly - 1) )

  # lower neighbor
  if celly < gameinfo['boardrows'] - 1 and board[cellx][celly + 1] == colorNo:
    neighbors.append( (cellx, celly + 1) )

  return neighbors


# computes the cell group to which the cell at (cellx, celly) belongs
def calculateGroup(cellx, celly):

  toprocess = set( [ (cellx, celly) ] )
  processed = set()

  while len(toprocess) > 0:
    # extract one element
    x, y = tuple(toprocess)[0]

    for n in getImmediateNeighbors(x, y):
      if not n in processed:
        toprocess.add(n)

    toprocess.remove((x, y))
    processed.add((x, y))

  return tuple(sorted(list(processed)))


def calculateAllGroups():

  allgroups = {}
  maxgroupsize = 0

  board = gameinfo['board'][gameinfo['curmove']]

  gameinfo['cellsleft'] = {}
  gameinfo['groupsleft'] = {}

  for colorNo in range(gameinfo['ncolors']):
    gameinfo['cellsleft'][colorNo] = 0
    gameinfo['groupsleft'][colorNo] = {}

  gameinfo['cellsleft']['total'] = 0
  gameinfo['groupsleft']['total'] = {}

  processedcells = {}

  for col in range(gameinfo['boardcols']):
    for row in range(gameinfo['boardrows']):

      colorNo = board[col][row]

      if colorNo != BLANK and not (col, row) in processedcells:

        group = calculateGroup(col, row)
        groupsize = len(group)

        # to avoid processing other cells belonging
        # to the same group
        for cell in group:
          processedcells[cell] = None

        if not group in gameinfo['groupsleft'][colorNo]:

          if groupsize > 1: gameinfo['groupsleft'][colorNo][group] = None
          gameinfo['cellsleft'][colorNo] += groupsize

          if groupsize > 1: gameinfo['groupsleft']['total'][group] = None
          gameinfo['cellsleft']['total'] += groupsize

          if groupsize > maxgroupsize:
            maxgroupsize = groupsize

  gameinfo['maxgroupsize'] = maxgroupsize


# assuming we already have the list of calculated groups,
# just return the group the given cell belongs to
def getGroup(cellx, celly):

  for group in gameinfo['groupsleft']['total']:
    if (cellx, celly) in group:
      return group
  return ( (cellx, celly), )


# Remove a group of cells of same color and compute the new board status.
# A copy of current status is made, and the copy is updated and saved.
# The algorithm used to recalculate is not the obvious one. Just because.
def removeGroup(group):

  # if the group is a single cell, do nothing
  if len(group) == 1:
    return

  nremoved = len(group)

  # consider the new move
    
  score = gameinfo['score'][gameinfo['curmove']]
  newstate = copy.deepcopy(gameinfo['board'][gameinfo['curmove']])
  gameinfo['curmove'] += 1
  gameinfo['board'][gameinfo['curmove']] = newstate    
  gameinfo['score'][gameinfo['curmove']] = score
  newstate = gameinfo['board'][gameinfo['curmove']]

  # to handle redo
  gameinfo['maxmove'] = gameinfo['curmove']

  # first, find which columns are affected by the removal.
  # at the same time, blank out the removed cells.
  affectedcols = {}

  for n in group:
    col, row = n
    newstate[col][row] = BLANK
    affectedcols[col] = None

  # second, fill the gaps in the affected columns
  # by moving down things

  for col in affectedcols:

    # create a column of empty cells
    occupiedrows = [ BLANK ] * gameinfo['boardrows']
      
    for row in range(0, gameinfo['boardrows']):
      if newstate[col][row] != BLANK:
        occupiedrows.append(newstate[col][row])

    # get last gameinfo['boardrows'] elements, which should
    # correspond to the actually used cells
    newstate[col] = occupiedrows[-gameinfo['boardrows']:]


  # third step: shift columns left if any column is empty
  # same logic as used for filling row gaps, but reversed

  occupiedcols = []
  for col in range(0, gameinfo['boardcols']):
    # if lowest cell is not blank, column is not empty
    if newstate[col][gameinfo['boardrows'] - 1] != BLANK:
      occupiedcols.append(newstate[col])

  occupiedcols.extend([ [ BLANK ] * gameinfo['boardrows'] for x in range(gameinfo['boardcols'])])

  newstate = occupiedcols[:gameinfo['boardcols']]

  # this becomes the current state
  gameinfo['board'][gameinfo['curmove']] = newstate

  # finally, recalculate group info
  calculateAllGroups()

  gameinfo['lastnremoved'] = nremoved
  gameinfo['score'][gameinfo['curmove']] += getPoints(gameinfo['lastnremoved'])


def showUsage():

  progname = sys.argv[0]

  printErr('Usage:')
  printErr(('%s [ -h|--help ]' % progname))
  printErr(('%s [ -l|--load f ] [ -g|--gameid n ] [ -c|--colors n ] [ -s|--cellsize n ] [ -x|--cols n ] [ -y|--rows n ]' % progname))

  printErr('')
  printErr('-h|--help        : this help')
  printErr('-l|--load f      : load saved game from file "f" (disables all options)')
  printErr(('-g|--gameid n    : play game #n (default: random betwen 0 and %s)' % MAXGAMENO))
  printErr(('-c|--colors n    : use "n" colors (default: %s)' % gameinfo['ncolors']))
  printErr(('-s|--cellsize n  : force a cellsize of "n" pixels (default: %s)' % gameinfo['cellsize']))
  printErr(('-x|--cols n      : force "n" columns (default: %s)' % gameinfo['boardcols']))
  printErr(('-y|--rows n      : force "n" rows (default: %s)' % gameinfo['boardrows']))



############# BEGIN

# set defaults

# these two do not change
WINDOWWIDTH = 640
WINDOWHEIGHT = 480

gameinfo = {}

# these may change depending on user-supplied rows/cols
gameinfo['topmargin'] = 5          # minimum
gameinfo['rightmargin'] = 130      # minimum

SCOREMARGIN = gameinfo['rightmargin']

MINCELLSIZE = 10

# these can change
gameinfo['cellsize'] = 30

gameinfo['boardcols'] = int((WINDOWWIDTH - gameinfo['rightmargin']) / gameinfo['cellsize'])
gameinfo['boardrows'] = int((WINDOWHEIGHT - gameinfo['topmargin']) / gameinfo['cellsize'])

# for sidebar display
STATUSCELLSIZE = 25

BLANK = '.'

# lots of colors.

#            R    G    B
BLACK   = (  0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (128, 128, 128)

RED     = (255,   0,   0)
GREEN   = (  0, 255,   0)
BLUE    = (  0,   0, 255)

CYAN    = (  0, 255, 255)
YELLOW  = (255, 255,   0)
MAGENTA = (255,   0, 255)

TEAL    = (  0, 128, 128)
OLIVE   = (128, 128,   0)
PURPLE  = (128,   0, 128)

MAROON  = (128,   0,   0)
DGREEN  = (  0, 128,   0)
NAVY    = (  0,   0, 128)

SILVER  = (192, 192, 192)

RED1    = (193,  28,  28)
GREEN1  = ( 29, 126,  29)
BLUE1   = ( 89,  59, 184)
BLUE2   = ( 41, 205, 231)
BROWN1  = (148, 132,  46)

BLUE3   = ( 51, 181, 229)
BLUE4   = (170, 102, 204)
GREEN2  = (153, 204,   0)
YELLOW1 = (255, 187,  51)
RED2    = (255,  68,  68)

GREEN3  = ( 60, 255,  62)
BLUE5   = ( 62, 147, 188)
YELLOW2 = (238, 184,   0)
RED3    = (219,  68,  65)
GRAY2   = ( 64,  64,  64)

# Make your own palettes if you don't like these.

PALETTE = ( ( RED1, GREEN1, BLUE1, BLUE2, BROWN1 ) ,
            ( BLUE3, BLUE4, GREEN2, YELLOW1, RED2 ),
            ( GREEN3, BLUE5, YELLOW2, RED3, GRAY2) )

COLORS = ()
setPalette(1)

gameinfo['ncolors'] = len(COLORS)

BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY

MAXGAMENO = 100000

try:
  opts, args = getopt.gnu_getopt(sys.argv[1:], 'hl:c:x:y:s:g:', [ 'help', 'load=', 'colors=', 'cols=', 'rows=', 'cellsize=', 'gameid=' ])

except getopt.GetoptError:
  terminate(msg = 'Error parsing arguments', usage = True, exitcode = 1)

if len(args) > 0:
  terminate(msg = 'Unknown argument(s) after options', usage = True, exitcode = 1)

gameid = None   # to generate a random game
overridecellsize = False
overridex = overridey = False
loadboard = False
animations = True

for opt, arg in opts:

  if opt in ('-h', '--help'):
    terminate(usage = True, exitcode = 1)

  elif opt in ('-c', '--colors'):
    if not str.isdigit(arg) or int(arg) > len(COLORS):
      terminate(msg = ('Invalid color number specified: %s' % arg), usage = True, exitcode = 1)
    gameinfo['ncolors'] = int(arg)

  elif opt in ('-x', '--cols'):
    if not str.isdigit(arg):
      terminate(msg = ('Invalid number of columns: %s' % arg), usage = True, exitcode = 1)
    overridex = True
    gameinfo['boardcols'] = int(arg)

  elif opt in ('-y', '--rows'):
    if not str.isdigit(arg):
      terminate(msg = ('Invalid number of rows: %s' % arg), usage = True, exitcode = 1)
    overridey = True
    gameinfo['boardrows'] = int(arg)

  elif opt in ('-s', '--cellsize'):
    if not str.isdigit(arg) or int(arg) < MINCELLSIZE:
      terminate(msg = ('Invalid cellsize: %s' % arg), usage = True, exitcode = 1)
    overridecellsize = True
    gameinfo['cellsize'] = int(arg)

  elif opt in ('-l', '--load'):
    savefile = arg
    loadboard = True

  elif opt in ('-g', '--gameid'):
    if not str.isdigit(arg) or int(arg) < 0 or int(arg) > MAXGAMENO:
      terminate(msg = ('Invalid game number: %s' % arg), usage = True, exitcode = 1)
    gameid = int(arg)


pygame.init()

if loadboard:
  print ('WARNING: loading a game disables any other option!')
  loadGame(savefile)
else:
  calcBoard(overridecellsize, overridex, overridey)

  # check whether we have too few rows or columns
  if gameinfo['boardrows'] < 2:
    terminate(msg = ('Too few resulting rows: %s' % gameinfo['boardrows']), exitcode = 1)

  if gameinfo['boardcols'] < 2:
    terminate(msg = ('Too few resulting columns: %s' % gameinfo['boardcols']), exitcode = 1)

  # check whether cellsize is too small
  if gameinfo['cellsize'] < MINCELLSIZE:
    terminate(msg = ('Resulting cell size too small: %s' % gameinfo['cellsize']), exitcode = 1)

  # finally, sanity check to see whether we fit

  if gameinfo['boardcols'] * gameinfo['cellsize'] > (WINDOWWIDTH - gameinfo['rightmargin']):
    terminate(msg = ('Width overflow with %s columns of size %s' % (gameinfo['boardcols'], gameinfo['cellsize'])), exitcode = 1)

  if gameinfo['boardrows'] * gameinfo['cellsize'] > (WINDOWHEIGHT - gameinfo['topmargin']):
    terminate(msg = ('Height overflow with %s rows of size %s' % (gameinfo['boardrows'], gameinfo['cellsize'])), exitcode = 1)

  # if all checks passed, generate board
  getNewBoard(gameid)


# recalculate margins
gameinfo['topmargin'] = WINDOWHEIGHT - (gameinfo['boardrows'] * gameinfo['cellsize'])
gameinfo['rightmargin'] = WINDOWWIDTH - (gameinfo['boardcols'] * gameinfo['cellsize'])

print ('Starting game with values: columns %s, rows %s, cellsize %s' % (gameinfo['boardcols'], gameinfo['boardrows'], gameinfo['cellsize']))

pygame.key.set_repeat(250, 100)

DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
BASICFONT = pygame.font.Font(None, 18)
BIGFONT = pygame.font.Font(None, 100)

context = 'game'
clicked = False

# main game loop
while True:

  cellx, celly = phys2LogCoord(gameinfo['mousex'], gameinfo['mousey'])

  curgroup = None

  if context == 'game':

    if cellx != None and cellx < gameinfo['boardcols'] and celly < gameinfo['boardrows'] and gameinfo['board'][gameinfo['curmove']][cellx][celly] != BLANK:

      # The mouse pointer is currently over a cell.
      if animations or clicked:
        curgroup = getGroup(cellx, celly)

      if clicked:
        # user clicked, remove
        removeGroup(curgroup)
        clicked = False
        # update current group after stuff has been removed
        if animations:
          curgroup = getGroup(cellx, celly)

    # redraw
    DISPLAYSURF.fill(BLACK)
    drawBoard(curgroup, animations)
    drawScore()
    pygame.display.update()

    if gameWon():
      context = 'endgame'
      showTextScreen("You won!", context)
    elif gameOver():
      context = 'endgame'
      showTextScreen("Game over", context)

  event = waitForEvent(context) 

  if event.type == KEYDOWN:
    if event.key == K_r:
      context = 'game'
      mods = pygame.key.get_mods()

      if mods & KMOD_RCTRL or mods & KMOD_LCTRL:
        redoMove()
      else:
        # restart same game
        gameinfo['curmove'] = 0
        gameinfo['maxmove'] = 0
        calculateAllGroups()
        print ('Restarting game %s' % gameinfo['gameid'])
        #getNewBoard(gameinfo['gameid'])

    elif event.key == K_n:
      # new game
      context = 'game'
      getNewBoard(None)
      print ('Starting new game %s' % gameinfo['gameid'])

    elif event.key == K_u:
      context = 'game'
      undoMove()

    elif event.key == K_a:
      animations = not animations

    elif event.key == K_d:
      mods = pygame.key.get_mods()
      if mods & KMOD_RCTRL or mods & KMOD_LCTRL:
        dumpCurrentBoard()

    elif event.key == K_1 or event.key == K_2 or event.key == K_3:
      setPalette(int(event.unicode))

    elif event.key == K_s:
      mods = pygame.key.get_mods()
      if mods & KMOD_RCTRL or mods & KMOD_LCTRL:
        saveGame()

  elif event.type == MOUSEMOTION:
    gameinfo['mousex'], gameinfo['mousey'] = event.pos

  elif event.type == MOUSEBUTTONUP:
    gameinfo['mousex'], gameinfo['mousey'] = event.pos
    clicked = True

