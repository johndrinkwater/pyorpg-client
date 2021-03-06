#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import getopt
import time
import pygame
from pygame.locals import *

from pgu import gui

from twisted.internet import reactor, error

import global_vars as g

from gamelogic import *
from graphics import *
from gameeditors import *
from gui.gui import *
from gui.pygUI import *
from menu.menulogin import menuLogin
from menu.menuregister import menuRegister
from menu.menuchar import menuCharacters
from menu.menunewchar import menuNewCharacter
from sprites import *
from objects import *
from network.CClientTCP import *
from network.database import *

class Engine:
    #################
    # GAME SPECIFIC #
    #################
    
    def __init__(self):
        self.FRAMES_PER_SECOND = 20 
        
        #INIT SETTINGS
        if not pygame.mixer: print "Warning, sounds are disabled!"

        # menus
        self.menuLogin = menuLogin(g.screenSurface)
        self.menuRegister = menuRegister(g.screenSurface)
        self.menuChar = menuCharacters(g.screenSurface)
        self.menuNewChar = menuNewCharacter(g.screenSurface)

        self.graphicsEngine = GraphicsEngine()
        self.gameEditor = GameEditor(self.graphicsEngine)

        self.tmr25 = 0
        self.tmr1000 = 0
        self.walkTimer = 0
        self.clockTick = 0

        
    def init(self):        
        pygame.display.flip()
        
        # initialize connection
        connectionProtocol = startConnection()
        g.tcpConn = TCPConnection(connectionProtocol)
        self.gameLoop()
        reactor.run()
        
    def gameLoop(self, FPS = 25):
        # TODO: DIRTY AREAS
        if g.gameState == MENU_LOGIN:
            self.menuLogin.draw()

        elif g.gameState == MENU_REGISTER:
            self.menuRegister.draw()

        elif g.gameState == MENU_CHAR:
            self.menuChar.draw()

        elif g.gameState == MENU_NEWCHAR:
            self.menuNewChar.draw()

        elif g.gameState == MENU_INGAME:
            # todo: dirty areas

            if g.inGame:
                self.clockTick = time.time() * 1000 # conver to ms

                if self.tmr25 < self.clockTick:
                    self.checkInputKeys()

                    if g.canMoveNow:
                        checkMovement()

                    self.tmr25 = self.clockTick + 25

                # process movements
                if self.walkTimer < self.clockTick:
                    for i in range(0, len(g.playersOnMap)):
                        if Player[g.playersOnMap[i]].moving > 0:
                            processMovement(g.playersOnMap[i])

                    self.walkTimer = self.clockTick + 30

                self.graphicsEngine.renderGraphics()

            # flip graphics
            pygame.display.update()

        pygame.event.pump()
        for event in pygame.event.get():
            # todo: organize this better...wd
            if g.gameState == MENU_LOGIN:
                self.menuLogin._handleEvents(event)

            elif g.gameState == MENU_REGISTER:
                self.menuRegister._handleEvents(event)

            elif g.gameState == MENU_CHAR:
                self.menuChar._handleEvents(event)

            elif g.gameState == MENU_NEWCHAR:
                self.menuNewChar._handleEvents(event)

            elif g.gameState == MENU_INGAME:
                self.graphicsEngine.gameGUI.update(event)

            if event.type == pygame.QUIT:
                reactor.stop()
                sys.exit()
            elif event.type == pygame.MOUSEMOTION:
                self.handleMouse(event)

        # make it loop
        reactor.callLater(1./FPS, self.gameLoop)

    def quitGame(self):
        g.tcpConn.sendQuit()
        reactor.stop()
        pygame.quit()
        sys.exit()


    ##################
    # INPUT SPECIFIC #
    #################

    def checkInputKeys(self):
        def pressed(key):
            keys = pygame.key.get_pressed()

            if keys[key]:
                return True
            else:
                return False

        if pressed(pygame.K_UP) or pressed(pygame.K_w):
            g.inpDIR_UP = True
            g.inpDIR_DOWN = False
            g.inpDIR_LEFT = False
            g.inpDIR_RIGHT = False

        elif pressed(pygame.K_DOWN) or pressed(pygame.K_s):
            g.inpDIR_UP = False
            g.inpDIR_DOWN = True
            g.inpDIR_LEFT = False
            g.inpDIR_RIGHT = False

        elif pressed(pygame.K_LEFT) or pressed(pygame.K_a):
            g.inpDIR_UP = False
            g.inpDIR_DOWN = False
            g.inpDIR_LEFT = True
            g.inpDIR_RIGHT = False

        elif pressed(pygame.K_RIGHT) or pressed(pygame.K_d):
            g.inpDIR_UP = False
            g.inpDIR_DOWN = False
            g.inpDIR_LEFT = False
            g.inpDIR_RIGHT = True

        else:
            g.inpDIR_UP = False
            g.inpDIR_DOWN = False
            g.inpDIR_LEFT = False
            g.inpDIR_RIGHT = False

    def handleMouse(self, event):
        g.cursorX = event.pos[0]
        g.cursorY = event.pos[1]