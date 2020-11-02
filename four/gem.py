"""
The program has "gem data structures", which are basically dictionaries with the following keys:
'x' and 'y' - The location of the gem on the baord. 0,0 is the top left
            - There is also a ROWABOVEBOARD row that 'y' can be set to, to indicate that
            it is above the board.
'direction' - one of the four constant variables UP, DOWN, LEFT, RIGHT. This is the direction
            the gem is moving.
'imageNum' - The integer index into GEMIMAGES to denote which image this gem uses.
"""

import random, time, pygame, sys, copy
from pygame.locals import *

FPS = 30
WINDOWWIDTH, WINDOWHEIGHT = 600, 600

BOARDWIDTH, BOARDHEIGHT, GEMIMAGESIZE = 8, 8, 64

# Number of gem types
NUMGEMIMAGES = 7
assert NUMGEMIMAGES >= 5

NUMMATCHSOUNDS = 6

MOVERATE = 25  # 1 to 100, larger num means faster animations
DEDUCTSPEED = 0.8  # reduces score by 1 point every DEDUCTSPEED seconds

PURPLE = (255, 0, 255)
LIGHTBLUE = (170, 190, 255)
BLUE = (0, 0, 255)
RED = (255, 100, 100)
BLACK = (0, 0, 0)
BROWN = (85, 65, 0)
HIGHLIGHTCOLOR = PURPLE  # color of the selected gem's border
BGCOLOR = LIGHTBLUE  # bg color on the screen
GRIDCOLOR = BLUE  # color of the game board
GAMEOVERCOLOR = RED  # color of the "Game Over" text
GAMEOVERBGCOLOR = BLACK  # bg color of the "Game Over" text
SCORECOLOR = BROWN  # color of the text for the player's score

XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * BOARDHEIGHT) / 2)

UP, DOWN, LEFT, RIGHT = 'up', 'down', 'left', 'right'

EMPTY_SPACE = -1
ROWABOVEBOARD = 'row above board'


def main():
    global FPSCLOCK, DISPLAYSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS

    # Initial set up
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Gems')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 36)

    # Load images
    GEMIMAGES = []
    for i in range(1, NUMGEMIMAGES+1):
        gemImage = pygame.image.load('../res/gem%s.png' % i)
        if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
            gemImage = pygame.transform.smoothscale(gemImage, (GEMIMAGESIZE, GEMIMAGESIZE))
        GEMIMAGES.append(gemImage)

    # Load sounds
    GAMESOUNDS = {'bad swap': pygame.mixer.Sound('../res/badswap.wav'), 'match': []}
    for i in range(NUMMATCHSOUNDS):
        GAMESOUNDS['match'].append(pygame.mixer.Sound('../res/match%s.wav' % i))

    BOARDRECTS = []
    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDHEIGHT):
            r = pygame.Rect((XMARGIN + (x * GEMIMAGESIZE),
                             YMARGIN + (y * GEMIMAGESIZE),
                             GEMIMAGESIZE,
                             GEMIMAGESIZE))
            BOARDRECTS[x].append(r)
    while True:
        runGame()


def runGame():
    """ PLays through a single game. When the game is over, this function returns."""

    # Initialize the board
    gameBoard = getBlankBoard()
    score = 0
    fillBoardAndAnimate(gameBoard, [], score)

    # Initialize variables for the start of a new game
    firstSelectedGem, lastMouseDownX, lastMouseDownY, gameIsOver = None, None, None, False
    lastScoreDeduction = time.time()
    clickContinueTextSurf = None

    while True:
        clickedSpace = None
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_BACKSPACE:
                return
            elif event.type == MOUSEBUTTONUP:
                if gameIsOver:
                    return

                if event.pos == (lastMouseDownX, lastMouseDownY):
                    # This event is a mouse click, not the end of a mouse drag
                    clickedSpace = checkForGemCLick(event.pos)
                else:
                    # this is the end of a mouse drag
                    firstSelectedGem = checkForGemCLick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForGemCLick(event.pos)
                    if not firstSelectedGem or not clickedSpace:
                        # if not part of avalis drag, deselect both
                        firstSelectedGem = None
                        clickedSpace = None
            elif event.type == MOUSEBUTTONDOWN:
                lastMouseDownX, lastMouseDownY = event.pos
        if clickedSpace and not firstSelectedGem:
            # This was the first gem clicked on
            firstSelectedGem = clickedSpace
        elif clickedSpace and firstSelectedGem:
            # Two gems have been clicked on and selected. Swap the gems.
            firstSwappingGem, secondSwappingGem = getSwappingGems(gameBoard, firstSelectedGem, clickedSpace)
            if firstSwappingGem is None and secondSwappingGem is None:
                # If both are None, then the gems were not adjacent
                firstSelectedGem = None  # deselect the first gem
                continue

            # show the swap animation on the screen.
            boardCopy = getBoardCopyMinusGems(gameBoard, (firstSwappingGem, secondSwappingGem))
            animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)

            # swap the gems in the board on the creen
            gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = secondSwappingGem['imageNum']
            gameBoard[secondSwappingGem['x']][secondSwappingGem['y']] = firstSwappingGem['imageNum']

            # See if this is a matching move
            matchedGems = findMatchingGems(gameBoard)
            if not matchedGems:
                # was not a matching move; swap the gems back
                GAMESOUNDS['bad swap'].play()
                animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)
                gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = firstSwappingGem['imageNum']
                gameBoard[secondSwappingGem['x']][secondSwappingGem['y']] = secondSwappingGem['imageNum']
            else:
                # This was a mathcing move
                scoreAdd = 0
                while matchedGems:
                    """Remove matched gems, then pull down the board. 
                    
                    points is a list of dicts that tells fillBoardAndAnimate()
                    where on the screen to display text to show how many
                    points the player got. points is a list because if the player gets
                    multiple matches, then multiple points text shpuld appear.
                    """
                    points = []
                    for gemSet in matchedGems:
                        scoreAdd += (10 + (len(gemSet) - 3) * 10)
                        for gem in gemSet:
                            gameBoard[gem[0]][gem[1]] = EMPTY_SPACE
                        points.append({'points': scoreAdd, 'x': gem[0] * GEMIMAGESIZE + XMARGIN, 'y': gem[1] * GEMIMAGESIZE + YMARGIN})
                    random.choice(GAMESOUNDS['match']).play()
                    score += scoreAdd

                    # Drop the new gems.
                    fillBoardAndAnimate(gameBoard, points, score)

                    # Check if there are any new matches.
                    matchedGems = findMatchingGems(gameBoard)
            firstSelectedGem = None

            if not canMakeMove(gameBoard):
                gameIsOver = True

        # Draw the board
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(gameBoard)
        if firstSelectedGem is not None:
            highlightSpace(firstSelectedGem['x'], firstSelectedGem['y'])
        if gameIsOver:
            if clickContinueTextSurf is None:
                """ Only render the text once. In future iterations, just use
                the Surface object already in clickCOntinueTextSurf"""
                clickContinueTextSurf = BASICFONT.render('Final Score: %s (Click to continue)' % score, 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
                clickContinueTextRect = clickContinueTextSurf.get_rect()
                clickContinueTextRect.center = int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2)
            DISPLAYSURF.blit(clickContinueTextSurf, clickContinueTextRect)
        elif score > 0 and time.time() - lastScoreDeduction > DEDUCTSPEED:
            # score drops over time
            score -= 1
            lastScoreDeduction = time.time()
        drawScore(score)
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def getSwappingGems(board, firstXY, secondXY):
    """
    If the gems at (X,Y) coordinates of the two gems are adjacent, then their 'direction'
    keys are set to the appropriate direction value to be swapped with each other.
    Otherwise, (None, None) is returned.
    """
    firstGem = {'imageNum': board[firstXY['x']][firstXY['y']], 'x': firstXY['x'], 'y': firstXY['y']}
    secondGem = {'imageNum': board[secondXY['x']][secondXY['y']], 'x': secondXY['x'], 'y': secondXY['y']}
    highlightedGem = None
    if firstGem['x'] == secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = LEFT
        secondGem['direction'] = RIGHT
    elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['x']:
        firstGem['direction'] = RIGHT
        secondGem['direction'] = LEFT
    elif firstGem['y'] == secondGem['y'] + 1 and firstGem['x'] == secondGem['x']:
        firstGem['direction'] = UP
        secondGem['direction'] = DOWN
    elif firstGem['y'] == secondGem['y'] - 1 and firstGem['x'] == secondGem['x']:
        firstGem['direction'] = DOWN
        secondGem['direction'] = UP
    else:
        # Thse gems are not adjacent and can't be swapped.
        return None, None
    return firstGem, secondGem


def getBlankBoard():
    """Create and retrun a blank baord data structure"""
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)
    return board


def canMakeMove(board):
    """Return True if the board is in a state where a matching move
    can be made on it. Otherwise return False.

    The patterns in oneOffPatterns represent gems that are configured
    in a way where it only takes one move to make a triplet."""
    oneOffPatterns = (((0, 1), (1, 0), (2, 0)),
                      ((0, 1), (1, 1), (2, 0)),
                      ((0, 0), (1, 1), (2, 0)),
                      ((0, 1), (1, 0), (2, 1)),
                      ((0, 0), (1, 0), (2, 1)),
                      ((0, 0), (1, 1), (2, 1)),
                      ((0, 0), (0, 2), (0, 3)),
                      ((0, 0), (0, 1), (0, 3)))

    """The x and y variables iterate over each space on the board. 
    if we use + to represent the currently iterated space on the board, 
    then this pattern: ((0,1),(1,0),(2,0)) refers to identical gems being set up like this
            +A
            B
            C
    That us, gem A is offset from the + by (0,1), gem B is offset by (1,0), and 
    gem C is offset by (2,0). In this case, gem A can be swapped to the left to form a vertical three-in-a-row triplet.
    
    There are 8 possible ways for the gems to be one move away from forming a triple, hence oneOffPattern has 8 patterns.  
    """

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatterns:
                # check each possible patern of "match in next move" to see if a possible move can be made
                if(getGemAt(board, x+pat[0][0], y+pat[0][1]) == getGemAt(board, x+pat[1][0], y+pat[1][1]) == getGemAt(board, x+pat[2][0], y+pat[2][1]) is not None) or \
                        (getGemAt(board, x+pat[0][1], y+pat[0][0]) == getGemAt(board, x+pat[1][1], y+pat[1][0]) == getGemAt(board, x+pat[2][1], y+pat[2][0]) is not None):
                    return True
    return False


def drawMovingGem(gem, progress):
    """Draw a gem sliding in the direction that its 'direction' key
    indicates. The progress parameter is a number from 0 (just startung) to 100 (clide complete)."""
    movex, movey = 0, 0
    progress *= 0.01

    if gem['direction'] == UP:
        movey = -int(progress * GEMIMAGESIZE)
    elif gem['direction'] == DOWN:
        movey = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == RIGHT:
        movex = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == LEFT:
        movex = -int(progress * GEMIMAGESIZE)

    basex = gem['x']
    basey = gem['y']
    if basey == ROWABOVEBOARD:
        basey = -1

    pixelx = XMARGIN + (basex * GEMIMAGESIZE)
    pixely = YMARGIN + (basey * GEMIMAGESIZE)
    r = pygame.Rect((pixelx + movex, pixely + movey, GEMIMAGESIZE, GEMIMAGESIZE))
    DISPLAYSURF.blit(GEMIMAGES[gem['imageNum']], r)


def pullDownAllGems(board):
    # pulls down gems on the board to the bottom to fill in any gaps
    for x in range(BOARDWIDTH):
        gemsInColumn = []
        for y in range(BOARDHEIGHT):
            if board[x][y] != EMPTY_SPACE:
                gemsInColumn.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn


def getGemAt(board, x, y):
    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        return None
    else:
        return board[x][y]


def getDropSlots(board):
    """Creates a "drop-slot" for each column and fills the slot with a
    number of gems that that column is lacking. This function assumes that the
    gems have been gravity dropped already.
    """
    boardCopy = copy.deepcopy(board)
    pullDownAllGems(boardCopy)

    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    # Count the number of empty spaces in each column on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 1, -1, -1):
            if boardCopy[x][y] == EMPTY_SPACE:
                possibleGems = list(range(len(GEMIMAGES)))
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    """Narrow down the possible gems we should put it in the 
                    blank space so we don't end up putting and two of the 
                    same gems next to each other when they drop.
                    """
                    neighborGem = getGemAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborGem is not None and neighborGem in possibleGems:
                        possibleGems.remove(neighborGem)
                newGem = random.choice(possibleGems)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)
    return dropSlots


def findMatchingGems(board):
    gemsToRemove = []  # a list of lists of gems in matching triplets that should be removed
    boardCopy = copy.deepcopy(board)

    # loop through each space, checking for 3 adjacent identical gems
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            # look for horizontal matches
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x + 1, y) == getGemAt(boardCopy, x + 2, y) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x + offset, y) == targetGem:
                    # keep checking, in case there's more than 3 gems in a row.
                    removeSet.append((x + offset, y))
                    boardCopy[x + offset][y] = EMPTY_SPACE
                    offset += 1
                gemsToRemove.append(removeSet)

            # look for vertical matches
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x, y + 1) == getGemAt(boardCopy, x, y + 2) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x, y + offset) == targetGem:
                    # keep checking, in case there's more than 3 gems in a row.
                    removeSet.append((x, y + offset))
                    boardCopy[x][y + offset] = EMPTY_SPACE
                    offset += 1
                gemsToRemove.append(removeSet)
    return gemsToRemove


def highlightSpace(x, y):
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)


def getDroppingGems(board):
    """Finds all the gems that have an empty space below them"""
    boardCopy = copy.deepcopy(board)
    droppingGems = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y + 1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                # This space drops if not empty but the space below it is
                droppingGems.append({'imageNum': boardCopy[x][y], 'x': x, 'y': y, 'direction': DOWN})
                boardCopy[x][y] = EMPTY_SPACE
    return droppingGems


def animateMovingGems(board, gems, pointsText, score):
    # pointsText is a dictionary with keys 'x', 'y', and 'points'
    progress = 0  # progress at 0 represents beginning, 100 means finished.
    while progress < 100:
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        for gem in gems:
            drawMovingGem(gem, progress)
        drawScore(score)
        for pointText in pointsText:
            pointsSurf = BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
            pointsRect = pointsSurf.get_rect()
            pointsRect.center = (pointText['x'], pointText['y'])
            DISPLAYSURF.blit(pointsSurf, pointsRect)

        pygame.display.update()
        FPSCLOCK.tick(FPS)
        progress += MOVERATE  # progress the animation a little bit more for the next frame


def moveGems(board, movingGems):
    """movingGems is a list of dicts woth keys x,y,direction, imageNum"""
    for gem in movingGems:
        if gem['y'] != ROWABOVEBOARD:
            board[gem['x']][gem['y']] = EMPTY_SPACE
            movex, movey = 0, 0
            if gem['direction'] == LEFT:
                movex = -1
            elif gem['direction'] == RIGHT:
                movex = 1
            elif gem['direction'] == DOWN:
                movey = 1
            elif gem['direction'] == UP:
                movey = -1
            board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
        else:
            # gem is located above the board (where new gems come from)
            board[gem['x']][0] = gem['imageNum']  # move to top row


def fillBoardAndAnimate(board, points, score):
    dropSlots = getDropSlots(board)
    while dropSlots != [[]] * BOARDWIDTH:
        # do the dropping animation as long as there are more gems to drop
        movingGems = getDroppingGems(board)
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                #  cause the lowest gem in each slot to begin moving in the DOWN direction
                movingGems.append({'imageNum':  dropSlots[x][0], 'x': x, 'y': ROWABOVEBOARD, 'direction': DOWN})

        boardCopy = getBoardCopyMinusGems(board, movingGems)
        animateMovingGems(boardCopy, movingGems, points, score)
        moveGems(board, movingGems)

        # Make the next row of gems from the drop slots the lowest
        # by deleting the previous lowest gems.
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]


def checkForGemCLick(pos):
    # See if the mouse click was on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0], pos[1]):
                return {'x': x, 'y': y}
    return None


def drawBoard(board):
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            gemToDraw = board[x][y]
            if gemToDraw != EMPTY_SPACE:
                DISPLAYSURF.blit(GEMIMAGES[gemToDraw], BOARDRECTS[x][y])


def getBoardCopyMinusGems(board, gems):
    """
    Creates and returns a copy of the passed board data structure,
    with the gems in the "gems" list removed from it.
    Gems is a list of dicts, with keys x, y, direction, imageNum
    """

    boardCopy = copy.deepcopy(board)

    # Remove some of the gems from this board data structure copy
    for gem in gems:
        if gem['y'] != ROWABOVEBOARD:
            boardCopy[gem['x']][gem['y']] = EMPTY_SPACE
    return boardCopy


def drawScore(score):
    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR)
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 6)
    DISPLAYSURF.blit(scoreImg, scoreRect)


if __name__ == '__main__':
    main()
