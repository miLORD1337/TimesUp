from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
import random
import codecs
from requests import Session
import json
from threading import Thread
import time

class Window(QMainWindow):
    keyPressed = pyqtSignal(int)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event.key())

    def __init__(self):
        super().__init__()
        self.title = "TimesUp!"
        self.top= 150
        self.left= 150
        self.width = 1024
        self.height = 768

        self.fontsize = 20

        bg = QImage("bg.jpg")
        self.bgpic = QPixmap(bg)
        img = QImage("card.png")
        self.pic = QPixmap(img)

        self.turnTimer = QTimer()

        self.playername = 'Tästname'

        self.roundtypes = {0:'Lobby', 1:'Explain', 2:'One word only', 3:'Sound only', 4:'Pantomime'}
        self.n_rounds = len(self.roundtypes)

        # Initial Values
        self.words = []
        self.n_words = []
        self.playernames = []
        self.duration = 60
        self.turntime = 0
        self.round = 0
        self.step = 0
        self.word = 0
        self.player = 0
        self.n_players = 0
        self.timeexceeded = False
        self.setup()

        self.testing()

        # Triggers
        self.turnTimer.timeout.connect(self.count)
        self.keyPressed.connect(self.advanceStep)
        
        # Threads
        thread = Thread(target=self.updateGameState, daemon=True)
        thread.start()

        # All ready
        self.InitWindow()

    def setup(self):
        self.server = Session()
        self.url = 'http://localhost/server.php'
        self.server.post(self.url, {'SetDuration': self.duration})
        self.server.post(self.url, {'NewPlayer': self.playername})

    def testing(self):
        self.server.post(self.url, {'SetDuration': 6})
        self.server.post(self.url, {'NewPlayer': 'Player2'})
        for i in range(20):
            self.addWord('Word{}'.format(i))

    def updateGameState(self):
        while True:
            try:
                #print(self.server.get(self.url).text)
                gamestate = json.loads(self.server.get(self.url).text)
                if 'words' in gamestate: 
                    self.words = gamestate['words']
                    self.n_words = len(self.words)
                if 'players' in gamestate: 
                    self.playernames = gamestate['players']
                    self.n_players = len(self.playernames)
                if 'round' in gamestate: self.round = gamestate['round']
                if 'step' in gamestate: self.step = gamestate['step']
                if 'word' in gamestate: self.word = gamestate['word']
                if 'player' in gamestate: self.player = gamestate['player']
                if 'turnTime' in gamestate: self.turntime = gamestate['turnTime']
                if 'turnTimeExceeded' in gamestate: self.timeexceeded = gamestate['turnTimeExceeded']
                if 'duration' in gamestate: self.duration = gamestate['duration']
                print(gamestate)
            except:
                print('Error encounted while updating.')
            self.update()
            time.sleep(0.5)

    def addWord(self, word):
        self.server.post(self.url, {'NewWord': word})
        self.update()

    def addPlayer(self, player):
        self.server.post(self.url, {'NewPlayer': player})
        self.update()
        
    def advanceStep(self):
        self.secs = self.duration
        self.server.post(self.url, {'AdvanceStep': 0})
        self.update()

    def InitWindow(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        helpMenu = menubar.addMenu('&?')

        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAct)

        helpAct = QAction('Help', self)
        helpAct.triggered.connect(self.helpWindow)
        helpMenu.addAction(helpAct)

        aboutAct = QAction('About', self)
        aboutAct.triggered.connect(self.aboutWindow)
        helpMenu.addAction(aboutAct)

        self.show()

    def helpWindow(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(
        """Every player creates a .txt named after him- or herself, e.g. 'alice.txt'.
In this file he/she puts one word each row, as many words as the players choose beforehand. 
The number of words (and therefore lines) must be equal for each player. 
That file is then sent to the hosting player.
The hosting player copies the files into the 'files/'-folder and starts the game.
A keypress advances game steps, players, rounds, etc..
Have fun!
        """)
        msgBox.setWindowTitle("How to play?")
        msgBox.setStandardButtons(QMessageBox.Ok)
       
        returnValue = msgBox.exec()
    
    def aboutWindow(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Code by miLORD1337, 01.12.2020")
        msgBox.setWindowTitle("About TimesUp!")
        msgBox.setStandardButtons(QMessageBox.Ok)
       
        returnValue = msgBox.exec()

    def paintEvent(self, event):
        self.painter = QPainter(self)
        self.centered = self.pic.rect()
        self.centered.translate(self.rect().center().x()-self.pic.rect().width()/2, self.rect().center().y()-self.pic.rect().height()/2)
        offset = self.pic.rect().height()/2 + 10
        self.cardstack =  self.centered.translated(0, -offset)
        self.showncard =  self.centered.translated(0, offset)

        self.drawBg()
        if not self.round == 0: self.drawStack()

        if self.step == 1: # Look away!
            self.timeexceeded = False
        elif self.step == 2: # Card shown
            self.drawCard(self.words[self.word-1])
        elif self.step == 3: # Card tucked away, time running
            if not self.turnTimer.isActive(): self.turnTimer.start()
            self.drawTucked()
            self.drawTime()
        elif self.step == 4: # Show card to everyone
            self.turnTimer.stop()
            col = '#0fcb01'
            if self.timeexceeded: col = '#be1e3c'
            self.drawCard(self.words[self.word-1], col)
        else: # Default
            self.timeexceeded = False

        self.drawHUD()

        self.painter.end()

    def drawBg(self):
        self.painter.drawPixmap(self.rect(), self.bgpic)

    def drawHUD(self):
        font = QFont()
        font.setPointSize(self.fontsize)
        options = QTextOption()
        options.setWrapMode(QTextOption.WordWrap)
        self.painter.setFont(font)
        # Lobby
        if self.round == 0:
            self.painter.drawText(QRectF(20, 30, 400, 300), 'Lobby\nPlayers: {}'.format(self.n_players))
            txt = ''
            for player in self.playernames:
                txt = '\n'.join([txt, player])
            self.painter.drawText(QRectF(20, 30, 400, 300), '\n\n{}'.format(txt))
        # In game
        else:
            self.painter.drawText(QRectF(20, 30, 400, 300), 
                'Round {}, {}\n{} ➞ {}'.format(
                self.round, self.roundtypes[self.round], self.playernames[self.player-1],
                self.playernames[self.player]), options)
            self.painter.drawText(QRectF(20, 30, 400, 300), 
                '\n\n\n\n\nWord {}/{}'.format(self.word, self.n_words), options)

    def drawTime(self):
        font = QFont()
        font.setPointSize(self.fontsize)
        options = QTextOption()
        options.setWrapMode(QTextOption.WordWrap)
        self.painter.setFont(font)
        drawtime = self.secs
        if drawtime > self.secs: drawtime = self.secs
        if drawtime < 0: drawtime = 0
        self.painter.drawText(QRectF(20, 300, 400, 300), '{}/{} seconds left'.format(drawtime, self.duration), options)

    def count(self):
        self.update()
        self.secs -= 1
        if self.secs == 0:
            pass
        else:
            self.turnTimer.start(1000)

    def drawStack(self):
        for i in range(10):
            self.painter.drawPixmap(self.cardstack,  self.pic)
            self.cardstack.translate(-i/2,-i/2)

    def drawTucked(self):
        self.painter.drawPixmap(self.showncard,  self.pic)

    def drawCard(self, text, color = '#000000'):
        self.painter.setPen(QPen(QColor('#FFFFFF')))
        brush = QBrush(QColor("#FFFFFF"))
        self.painter.setBrush(brush)
        self.painter.drawRoundedRect(self.showncard, 10, 10)

        self.painter.setPen(QPen(QColor(color)))
        offset = QPoint(10, 10)
        border = QRect(self.showncard.topLeft()+offset, self.showncard.bottomRight()-offset)
        self.painter.drawRoundedRect(border, 10, 10)

        options = QTextOption()
        options.setWrapMode(QTextOption.WordWrap)
        options.setAlignment(Qt.AlignCenter)

        font = QFont()
        font.setPointSize(self.fontsize)
        self.painter.setFont(font)
        self.painter.drawText(QRectF(self.showncard), text, options)
        self.painter.setPen(QPen(QColor('#000000')))

if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = Window()
    sys.exit(App.exec())