from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
import random
import codecs

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

        self.timer = QTimer()

        self.dir = 'files'
        self.playertime = 60

        self.roundtypes = {1:'Explain', 2:'One word only', 3:'Sound only', 4:'Pantomime'}
        self.n_rounds = len(self.roundtypes)

        # Collect players
        self.files = [f for f in os.listdir(self.dir) if f.endswith('.txt')]
        self.playernames = [os.path.splitext(obj)[0] for obj in self.files]
        random.shuffle(self.playernames)
        self.playernames.append(self.playernames[0]) # Dirty Trick for easy next player
        self.n_players = len(self.files)

        # Collect words
        self.words = []
        for f in self.files:
            with codecs.open(os.path.join(self.dir,f), 'r', 'utf-8') as file:
                [self.words.append(line.rstrip('\n')) for line in file]
        random.shuffle(self.words)
        self.n_words = len(self.words)

        # Initial Values
        self.round = 1
        self.player = 1
        self.word = 1
        self.step = 0
        self.secs = self.playertime
        self.timeexceeded = False

        # Triggers
        self.keyPressed.connect(self.advanceStep)
        self.timer.timeout.connect(self.count)

        # All ready
        self.InitWindow()
        self.advanceStep()
        
    def advanceStep(self):
        self.step += 1
        if self.step > 4: # Card tucked away, times up!
            self.step = 1
            self.player += 1
            self.word += 1
        if self.player > self.n_players: self.player = 1
        if self.word > self.n_words: 
            self.word = 1
            self.round += 1
            random.shuffle(self.words)
        if self.round > self.n_rounds: self.close()
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
        self.drawStack()

        if self.step == 1: # Look away!
            self.timeexceeded = False
        elif self.step == 2: # Card shown
            self.drawCard(self.words[self.word-1])
        elif self.step == 3: # Card tucked away, time running
            self.timer.start(1000)
            self.drawTucked()
            self.drawTime()
        elif self.step == 4: # Show card to everyone
            if self.timeexceeded:
                self.drawCard(self.words[self.word-1], '#be1e3c')
            else:
                self.drawCard(self.words[self.word-1], '#0fcb01')
            self.secs = self.playertime
            self.timer.stop()
        else: # Default
            self.timeexceeded = False
            self.secs = self.playertime
            self.timer.stop()

        self.drawHUD()

        self.painter.end()

    def count(self):
        self.secs -= 1
        self.update()
        if self.secs == 0:
            self.timeexceeded = True
            self.secs = self.playertime
            self.advanceStep()
        else:
            self.timer.start(1000)

    def drawBg(self):
        self.painter.drawPixmap(self.rect(), self.bgpic)

    def drawHUD(self):
        font = QFont()
        font.setPointSize(self.fontsize)
        options = QTextOption()
        options.setWrapMode(QTextOption.WordWrap)
        self.painter.setFont(font)
        self.painter.drawText(QRectF(20, 30, 400, 300), 
            'Round {}, {}\n{} ➞ {}\n\n\n\nWord {}/{}'.format(
            self.round, self.roundtypes[self.round], self.playernames[self.player-1],
            self.playernames[self.player], self.word, self.n_words), options)

    def drawTime(self):
        font = QFont()
        font.setPointSize(self.fontsize)
        options = QTextOption()
        options.setWrapMode(QTextOption.WordWrap)
        self.painter.setFont(font)
        self.painter.drawText(QRectF(20, 300, 400, 300), '{}/{} seconds left'.format(self.secs, self.playertime), options)

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

App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())