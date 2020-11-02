import pygame
from .sockutils import *
from tools.loader import ONLINE, BACK, putLargeNum, putNum


# Shows a small popup when user requests game with wrong player
def showUpdateList(win):
    pygame.draw.rect(win, (0, 0, 0), (110, 220, 280, 60))
    pygame.draw.rect(win, (255, 255, 255), (110, 220, 280, 60), 4)
    win.blit(ONLINE.ERRCONN, (120, 240))
    pygame.display.update()
    for _ in range(50):
        pygame.time.delay(50)
        for _ in pygame.event.get():
            pass


# Shows the screen just before the lobby, displays error messages
def showLoading(win, errcode=0):
    pygame.draw.rect(win, (0, 0, 0), (100, 220, 300, 80))
    pygame.draw.rect(win, (255, 255, 255), (100, 220, 300, 80), 4)
    win.blit(ONLINE.ERR[errcode], (115, 240))
    if errcode == 0:
        pygame.display.update()
        return
    pygame.draw.rect(win, (255, 255, 255), (220, 270, 65, 20), 2)
    win.blit(ONLINE.GOBACK, (220, 270))
    pygame.display.update()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if 220 < event.pos[0] < 285 and 270 < event.pos[1] < 290:
                    return


# Show a popup message when user left, resigned or draw accepted
def popup(win, sock, typ):
    pygame.draw.rect(win, (0, 0, 0), (130, 220, 240, 80))
    pygame.draw.rect(win, (255, 255, 255), (130, 220, 240, 80), 4)
    win.blit(ONLINE.POPUP[typ], (145, 240))
    pygame.draw.rect(win, (255, 255, 255), (220, 270, 65, 20), 2)
    win.blit(ONLINE.GOBACK)
    pygame.display.update()

    ret = 3
    while True:
        if readable() and read() == "close":
            write(sock, "quit")
            ret = 2
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if 220 < event.pos[0] < 285 and 270 < event.pos[1] < 290:
                    write(sock, "end")
                    return ret


# Shows a popup message on screen.
# 1. Shows Waiting for opponent input for game request.
# 2. Shows Waiting for player input for game request.
def request(win, sock, key=None):
    if key is None:
        pygame.draw.rect(win, (0, 0, 0), (100, 210, 300, 100))
        pygame.draw.rect(win, (255, 255, 255), (100, 210, 300, 100), 4)
        win.blit(ONLINE.REQUEST1[0], (120, 220))
        win.blit(ONLINE.REQUEST1[1], (105, 245))
        win.blit(ONLINE.REQUEST1[2], (135, 270))
    else:
        pygame.draw.rect(win, (0, 0, 0), (100, 160, 300, 130))
        pygame.draw.rect(win, (255, 255, 255), (100, 160, 300, 130), 4)
        win.blit(ONLINE.REQUEST2[0], (110, 175))
        win.blit(ONLINE.REQUEST2[1], (200, 175))
        win.blit(ONLINE.REQUEST2[2], (105, 200))
        putNum(win, key, (160, 175))
        win.blit(ONLINE.OK, (145, 240))
        win.blit(ONLINE.NO, (305, 240))
        pygame.draw.rect(win, (255, 255, 255), (140, 240, 50, 28), 2)
        pygame.draw.rect(win, (255, 255, 255), (300, 240, 50, 28), 2)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if key is None and event.type == pygame.QUIT:
                write(sock, "quit")
                return 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if key is None:
                    if 460 < event.pos[0] < 500 and 0 < event.pos[1] < 50:
                        write(sock, "quit")
                        return 1
                elif 240 < event.pos[1] < 270:
                    if 140 < event.pos[0] < 190:
                        return 4
                    elif 300 < event.pos[0] < 350:
                        return 3
        if readable():
            msg = read()
            if msg == "close":
                return 2
            if msg == "quit":
                return 3

            if key is None:
                if msg == "nostart":
                    write(sock, "pass")
                    return 3
                if msg == "start":
                    write(sock, "ready")
                    return 4


# Shows a popup message on the screen with the following
# 1. Shows waiting for other players input for draw game
# 2. Shows waiting for players input for draw game
def draw(win, sock, requester=True):
    if requester:
        pygame.draw.rect(win, (0, 0, 0), (100, 220, 300, 60))
        pygame.draw.rect(win, (255, 255, 255), (100, 220, 300, 60), 4)
        win.blit(ONLINE.DRAW1[0], (110, 225))
        win.blit(ONLINE.DRAW1[1], (180, 250))
    else:
        pygame.draw.rect(win, (0, 0, 0), (100, 160, 300, 130))
        pygame.draw.rect(win, (255, 255, 255), (100, 160, 300, 130), 4)
        win.blit(ONLINE.DRAW2[0], (120, 170))
        win.blit(ONLINE.DRAW2[1], (170, 195))
        win.blit(ONLINE.OK, (145, 240))
        win.blit(ONLINE.NO, (305, 240))
        pygame.draw.rect(win, (255, 255, 255), (140, 240, 50, 28), 2)
        pygame.draw.rect(win, (255, 255, 255), (300, 240, 50, 28), 2)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                write(sock, "quit")
                return 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 240 < event.pos[1] < 270:
                    if 140 < event.pos[0] < 190:
                        write(sock, "draw")
                        return 3
                    elif 300 < event.pos[0] < 350:
                        write(sock, "nodraw")
                        return 4
        if readable():
            msg = read()
            if msg == "close":
                return 2
            if msg == "quit":
                return popup(win, sock, msg)
            if requester:
                if msg == "draw":
                    return popup(win, sock, msg)
                if msg == "nodraw":
                    return 4


# Shows the online lobby
def showLobby(win, key, playerlist):
    win.fill((0, 0, 0))
    win.blit(ONLINE.LOBBY, (100, 14))
    pygame.draw.rect(win, (255, 255, 255), (65, 10, 355, 68), 4)
    win.blit(BACK, (460, 0))
    win.blit(ONLINE.LIST, (20, 75))
    win.blit(ONLINE.REFRESH, (270, 85))
    pygame.draw.line(win, (255, 255, 255), (20, 114), (190, 114), 3)
    pygame.draw.line(win, (255, 255, 255), (210, 114), (265, 114), 3)

    if not playerlist:
        win.blit(ONLINE.EMPTY, (25, 130))

    for cnt, player in enumerate(playerlist):
        pkey, stat = int(player[:4]), player[4]
        yCord = 120 + cnt * 30
        putLargeNum(win, cnt + 1, (20, yCord))
        win.blit(ONLINE.DOT, (36, yCord))
        win.blit(ONLINE.PLAYER, (52, yCord))
        putLargeNum(win, pkey, (132, yCord))
        if stat == "a":
            win.blit(ONLINE.ACTIVE, (200, yCord))
        elif stat == "b":
            win.blit(ONLINE.BUSY, (200, yCord))
        pygame.draw.rect(win, (255, 255, 255), (300, yCord + 2, 175, 26), 2)
        win.blit(ONLINE.REQ, (300, yCord))
    win.blit(ONLINE.YOUARE, (100, 430))
    pygame.draw.rect(win, (255, 255, 255), (250, 435, 158, 40), 3)
    win.blit(ONLINE.PLAYER, (260, 440))
    putLargeNum(win, key, (340, 440))
    pygame.display.update()