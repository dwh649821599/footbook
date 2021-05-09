# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'homepage.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication, QScrollArea, QDesktopWidget, QRadioButton, QScrollBar, \
    QPlainTextEdit, QLabel, QPushButton, QLineEdit, QMenu, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QFont, QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QPoint, QCoreApplication, QRect, QThread, pyqtSignal
import sys, os, pickle
import time
import cv2
from gui import search as sc

method = None


class RcvThread(QThread):
    mysignal = pyqtSignal(tuple)

    def __init__(self, cthandle, obj, isTimeout):
        super(RcvThread, self).__init__()
        self.cthandle = cthandle
        self.obj = obj
        self.isTimeout = isTimeout

    def run(self):
        while True:
            time.sleep(0.01)
            rcvMsg = self.cthandle.check_text_queue()
            VR = self.cthandle.check_certain_type_of_request_response(b'video_request')
            VA = self.cthandle.check_certain_type_of_request_response(b'video_accept')
            AR = self.cthandle.check_certain_type_of_request_response(b'audio_request')
            AA = self.cthandle.check_certain_type_of_request_response(b'audio_accept')
            SFY = self.cthandle.check_certain_type_of_request_response(b'search_friend_OK')
            SFN = self.cthandle.check_certain_type_of_request_response(b'search_friend_NO')
            AFA = self.cthandle.check_certain_type_of_request_response(b'add_friend_accept')
            AFR = self.cthandle.check_certain_type_of_request_response(b'add_friend_request')
            if rcvMsg:
                self.mysignal.emit(rcvMsg)
            if VR:
                self.mysignal.emit(VR)
            if VA:
                self.mysignal.emit(VA)
            if AR:
                self.mysignal.emit(AR)
            if AA:
                self.mysignal.emit(AA)
            if SFN:
                self.mysignal.emit(SFN)
            if SFY:
                self.mysignal.emit(SFY)
            if AFA:
                self.mysignal.emit(AFA)
            if AFR:
                self.mysignal.emit(AFR)
            if self.isTimeout:
                self.obj.insertMessage('□◁ 视频请求超时', '', True, False)
                self.isTimeout = False


class MessageBox(QWidget):
    def __init__(self, send=True, receive=False, accept=False, parent=None):
        super().__init__(parent)
        self.isReceive = receive
        self.isSend = send
        self.isAccept = accept
        self.setupUi()

    def setupUi(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(650, 60)
        self.setMinimumSize(QtCore.QSize(60, 60))
        self.setMaximumSize(QtCore.QSize(650, 60))
        self.icon = QLabel()
        self.icon.setFixedSize(30, 30)
        self.icon.setStyleSheet('''border-image:url(./pic/user.svg);
                                    background:transparent;
                                    border-radius:4px;
                                    border:none;''')
        self.saying = QLabel()
        self.saying.setMinimumSize(20, 30)
        self.saying.setMaximumWidth(550)
        self.saying.setStyleSheet('''border:none;
                                    background:#b2e281;
                                    border-radius:4px;
                                    font-size:15px;
                                    font:bold;''')
        self.listening = QLabel()
        self.listening.setMinimumSize(20, 30)
        self.listening.setMaximumWidth(550)
        self.listening.setStyleSheet('''border:none;
                                        background:#b2b2b2;
                                        border-radius:4px;
                                        font-size:15px;
                                        font:bold;''')
        self.accept = QPushButton()
        self.accept.setMinimumSize(20, 30)
        self.accept.setMaximumWidth(550)
        self.accept.setStyleSheet('''border:none;
                                       background:#b2b2b2;
                                       border-radius:4px;
                                       font-size:15px;
                                       font:bold;''')

        self.accept.setCursor(QCursor(Qt.PointingHandCursor))

        self.layout = QHBoxLayout(self)
        self.spacer = QLabel()
        if self.isSend:
            self.saying.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.layout.addWidget(self.spacer)
            self.layout.addWidget(self.saying)
            self.layout.addSpacing(10)
            self.layout.addWidget(self.icon)
        elif self.isReceive:
            self.listening.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.layout.addWidget(self.icon)
            self.layout.addSpacing(10)
            if self.isAccept:
                self.layout.addWidget(self.accept)
            else:
                self.layout.addWidget(self.listening)
            self.layout.addWidget(self.spacer)


class Homepage(QMainWindow):
    def __init__(self, Mainwindow, cthandle):
        global method
        super(Homepage, self).__init__()
        self.cthandle = cthandle
        self.allUserInfo = self.cthandle.get_init_info()
        self.tofriend = None
        self.isVideoing = False
        self.isTimeout = False
        self.isAudioing = False
        self.isTimeout_audio = False
        self.friendRequestList = []

        self.setupUi(Mainwindow)

        self.rcvThread = RcvThread(self.cthandle, self, self.isTimeout)
        self.rcvThread.mysignal.connect(self.receiveMessage)
        self.rcvThread.start()

    def setupUi(self, MainWindow):
        MainWindow.setWindowFlags(Qt.FramelessWindowHint)
        MainWindow.setAttribute(Qt.WA_TranslucentBackground)
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.setEnabled(True)
        MainWindow.resize(950, 600)
        MainWindow.setMinimumSize(QtCore.QSize(950, 600))
        MainWindow.setMaximumSize(QtCore.QSize(950, 600))
        MainWindow.setAcceptDrops(True)

        self.mw = MainWindow

        self.searchmw = QtWidgets.QMainWindow()
        self.searchwindow = sc.Search(self.searchmw, self.cthandle, self.refreshDialog)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(271, 0, 20, 601))
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setGeometry(QtCore.QRect(280, 390, 661, 20))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.line_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_3.setGeometry(QtCore.QRect(51, 0, 20, 601))
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")


        self.input = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.input.setGeometry(QtCore.QRect(280, 430, 671, 131))
        self.input.setObjectName("input")
        self.input.setFont(QFont('微软雅黑', 16))

        self.logo = QLabel(self.centralwidget)
        self.logo.setFixedSize(100, 100)
        self.logo.move(560, 170)
        self.logo.setPixmap(QPixmap('pic/logo100.svg'))

        self.send = QtWidgets.QPushButton(self.centralwidget)
        self.send.setGeometry(QtCore.QRect(840, 560, 75, 30))
        self.send.setObjectName("send")
        self.send.setCursor(QCursor(Qt.PointingHandCursor))

        self.audio = QtWidgets.QPushButton(self.centralwidget)
        self.audio.setGeometry(QtCore.QRect(290, 400, 31, 31))
        self.audio.setObjectName("audio")
        self.audio.setCursor(QCursor(Qt.PointingHandCursor))

        self.video = QtWidgets.QPushButton(self.centralwidget)
        self.video.setGeometry(QtCore.QRect(330, 400, 31, 31))
        self.video.setObjectName("video")
        self.video.setCursor(QCursor(Qt.PointingHandCursor))

        self.picture = QtWidgets.QPushButton(self.centralwidget)
        self.picture.setGeometry(QtCore.QRect(370, 400, 31, 31))
        self.picture.setObjectName("picture")
        self.picture.setCursor(QCursor(Qt.PointingHandCursor))

        self.dialog = QtWidgets.QScrollArea(self.centralwidget)
        self.dialog.setGeometry(QtCore.QRect(50, 60, 231, 541))
        self.dialog.setWidgetResizable(True)
        self.dialog.setObjectName("dialog")
        self.dialog.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dialog.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dialogwidget = QtWidgets.QWidget()
        self.dialogwidget.setGeometry(QtCore.QRect(0, 0, 219, 539))
        self.dialogwidget.setObjectName("dialogwidget")
        self.dialog.setWidget(self.dialogwidget)

        self.dialoglayout = QVBoxLayout(self.dialogwidget)
        self.dialoglayout.setAlignment(Qt.AlignTop)
        self.dialoglayout.setSpacing(0)
        self.dialogwidget.setLayout(self.dialoglayout)

        self.dialoglist = {}
        self.messagelist = {}
        self.messagewidgetlist = {}
        self.dialogdic = {}
        self.history = {}
        self.curmessage = None

        for i in range(len(self.allUserInfo['friends'])):
            self.createdialog(i, str(self.allUserInfo['friends'][i]['id']))

        qss = ''''''
        for i in self.dialoglist.keys():
            qss += f'''QPushButton#dialogchoice{str(i)}''' + '''{background:#e3e3e3;border:none;}''' + \
                   f'''QPushButton#dialogchoice{str(i)}:''' + '''hover{background:#b8b8b8;}''' + \
                   f'''QPushButton#dialogchoice{str(i)}:''' + '''focus{background:#969696;}'''
            self.dialogwidget.setStyleSheet(qss)

        self.searchwidget = QtWidgets.QWidget(self.centralwidget)
        self.searchwidget.setGeometry(QtCore.QRect(60, 0, 221, 61))
        self.searchwidget.setObjectName("searchwidget")
        self.search = QtWidgets.QLineEdit(self.searchwidget)
        self.search.setGeometry(QtCore.QRect(10, 20, 170, 20))
        self.search.setObjectName("search")
        self.search.setClearButtonEnabled(True)

        self.searchbtn = QtWidgets.QPushButton(self.searchwidget)
        self.searchbtn.setGeometry(QtCore.QRect(190, 20, 20, 20))
        self.searchbtn.setObjectName("searchbtn")
        self.searchbtn.setCursor(QCursor(Qt.PointingHandCursor))

        self.userinfo = QtWidgets.QWidget(self.centralwidget)
        self.userinfo.setGeometry(QtCore.QRect(0, 0, 61, 601))
        self.userinfo.setObjectName("userinfo")

        self.userpic = QtWidgets.QPushButton(self.userinfo)
        self.userpic.setGeometry(QtCore.QRect(10, 10, 41, 41))
        self.userpic.setObjectName("userpic")
        self.userpic.setCursor(QCursor(Qt.PointingHandCursor))
        self.userpic.setStyleSheet(f'''border-image:url(./user/{str(self.allUserInfo['id'])}/head.png);''')

        self.addfriend = QtWidgets.QPushButton(self.userinfo)
        self.addfriend.setGeometry(QtCore.QRect(15, 80, 30, 30))
        self.addfriend.setObjectName("addfriend")
        self.addfriend.setCursor(QCursor(Qt.PointingHandCursor))

        self.addgroup = QtWidgets.QPushButton(self.userinfo)
        self.addgroup.setGeometry(QtCore.QRect(15, 125, 30, 30))
        self.addgroup.setObjectName("addgroup")
        self.addgroup.setCursor(QCursor(Qt.PointingHandCursor))

        self.creategroup = QtWidgets.QPushButton(self.userinfo)
        self.creategroup.setGeometry(QtCore.QRect(15, 170, 30, 30))
        self.creategroup.setObjectName("creategroup")
        self.creategroup.setCursor(QCursor(Qt.PointingHandCursor))

        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(280, 0, 671, 61))
        self.widget.setObjectName("widget")
        self.closebtn = QtWidgets.QPushButton(self.widget)
        self.closebtn.setGeometry(QtCore.QRect(640, 0, 30, 30))
        self.closebtn.setObjectName("closebtn")
        self.minbtn = QtWidgets.QPushButton(self.widget)
        self.minbtn.setGeometry(QtCore.QRect(610, 0, 30, 30))
        self.minbtn.setObjectName("minbtn")
        self.name = QtWidgets.QLabel(self.widget)
        self.name.setGeometry(QtCore.QRect(13, 22, 561, 31))
        self.name.setObjectName("name")
        self.name.setFont(QFont('微软雅黑', 16))
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.setqss(MainWindow)

        self.closebtn.clicked.connect(self.closepage)
        self.minbtn.clicked.connect(self.minimize)
        self.send.clicked.connect(self.sendMessage)
        self.video.clicked.connect(self.openVideo)
        self.audio.clicked.connect(self.openAudio)
        self.userpic.clicked.connect(self.modifyHead)

        self.addfriend.clicked.connect(self.searchFriend)

        for i in self.dialoglist.keys():
            curdialog = self.dialoglist[i]
            curdialog.clicked.connect(self.openMessageWindow)

    def createdialog(self, index, name, isFresh=False, head=''):
        exec('self.dialogdic[str(name)] = index')
        exec(f'self.dialogchoice{str(index)} = QPushButton(self.dialogwidget)')
        exec(f"self.dialogchoice{str(index)}.setObjectName(f'dialogchoice{str(index)}')")
        exec(f'icon = QLabel(self.dialogchoice{str(index)})')
        if not isFresh:
            exec(f"icon.setPixmap(QPixmap('./user/{str(self.allUserInfo['id'])}/friends/head{str(self.allUserInfo['friends'][index]['id'])}.png'))")
        else:
            exec(f"icon.setPixmap(QPixmap(head))")
        exec(f'icon.setFixedSize(50, 50)')
        exec(f'friendname = QLabel(self.dialogchoice{str(index)})')
        exec(f'friendname.setText(str(name))')
        exec(f"friendname.setFont(QFont('微软雅黑', 14))")
        exec(f'self.hint{str(index)} = QLabel(self.dialogchoice{str(index)})')
        exec(f"self.hint{str(index)}.setPixmap(QPixmap('./pic/hint.svg'))")
        exec(f'self.hint{str(index)}.setFixedSize(20, 20)')
        exec(f'self.hint{str(index)}.setHidden(True)')
        exec(f'hl = QHBoxLayout(self.dialogchoice{str(index)})')
        exec(f'hl.addWidget(icon)')
        exec(f'hl.addWidget(friendname)')
        exec(f'hl.addWidget(self.hint{str(index)})')

        exec(f'self.dialogchoice{str(index)}.setLayout(hl)')
        exec(f'self.dialogchoice{str(index)}.setFixedSize(220,70)')
        exec(f'self.dialoglayout.addWidget(self.dialogchoice{str(index)})')
        exec(f'self.dialoglist[index] = self.dialogchoice{str(index)}')

        exec(f'self.message{str(index)} = QtWidgets.QScrollArea(self.centralwidget)')
        exec(f'self.message{str(index)}.setGeometry(QtCore.QRect(280, 60, 671, 341))')
        exec(f'self.message{str(index)}.setWidgetResizable(True)')
        exec(f'self.message{str(index)}.setObjectName("message")')
        exec(f'self.message{str(index)}.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)')
        exec(f'self.message{str(index)}.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)')

        exec(f'self.messagewidget{str(index)} = QtWidgets.QWidget()')
        exec(f'self.messagewidget{str(index)}.setGeometry(QtCore.QRect(0, 0, 669, 339))')
        exec(f'self.messagewidget{str(index)}.setObjectName(f"messagewidget{str(index)}")')
        exec(f'self.message{str(index)}.setWidget(self.messagewidget{str(index)})')
        exec(f'self.messagelist[index] = self.message{str(index)}')
        exec(f'self.messagewidgetlist[index] = self.messagewidget{str(index)}')

        exec(f'self.message{str(index)}.setHidden(True)')
        exec(f'self.msglayout{str(index)} = QVBoxLayout(self.messagewidget{str(index)})')

        exec('spacer1 = QLabel()')
        exec('spacer2 = QLabel()')
        exec('spacer3 = QLabel()')
        exec('spacer4 = QLabel()')
        exec('spacer5 = QLabel()')

        exec('spacer1.setFixedSize(QtCore.QSize(650, 60))')
        exec('spacer2.setFixedSize(QtCore.QSize(650, 60))')
        exec('spacer3.setFixedSize(QtCore.QSize(650, 60))')
        exec('spacer4.setFixedSize(QtCore.QSize(650, 60))')
        exec('spacer5.setFixedSize(QtCore.QSize(650, 60))')

        exec('self.history[index] = [spacer1, spacer2, spacer3, spacer4, spacer5]')

    def receiveMessage(self, msg):
        print(msg[2])
        if msg[2] == b'video_accept':
            if self.curmessage is None:
                return
            if self.curmessage != self.dialogdic[msg[0]]:
                exec(f'self.hint{str(self.dialogdic[msg[0]])}.setVisible(True)')
            self.isVideoing = True
            self.insertMessage('', (msg[0], msg[1], '□◁ 对方已接受，正在建立连接'.encode()), False, True)
            self.video.setStyleSheet('border-image:url(./pic/video1.svg);hover{border-image:url(./pic/video2.svg);}')
            try:
                self.cthandle.open_video(str(self.allUserInfo['friends'][self.curmessage]['id']), self.timeout)
            except Exception as e:
                print(e)
        elif msg[2] == b'audio_accept':
            if self.curmessage is None:
                return
            if self.curmessage != self.dialogdic[msg[0]]:
                exec(f'self.hint{str(self.dialogdic[msg[0]])}.setVisible(True)')
            self.isAudioing = True
            self.insertMessage('', (msg[0], msg[1], '♬ 对方已接受，正在建立连接'.encode()), False, True)
            self.audio.setStyleSheet('border-image:url(./pic/video1.svg);hover{border-image:url(./pic/video2.svg);}')
            try:

                self.cthandle.open_audio(str(self.allUserInfo['friends'][self.curmessage]['id']), self.timeout_audio)
            except Exception as e:
                print(e)
        elif msg[2] == b'audio_request':
            if self.curmessage != self.dialogdic[msg[0]]:
                exec(f'self.hint{str(self.dialogdic[msg[0]])}.setVisible(True)')
            self.insertMessage('', (msg[0], msg[1], '♬ 收到音频请求，点击建立连接'.encode()), False, True, True, False, True)
        elif msg[2] == b'video_request':
            if self.curmessage != self.dialogdic[msg[0]]:
                exec(f'self.hint{str(self.dialogdic[msg[0]])}.setVisible(True)')
            self.insertMessage('', (msg[0], msg[1], '□◁ 收到视频请求，点击建立连接'.encode()), False, True, True, True, False)
        elif msg[2][:16] == b'search_friend_OK':
            self.searchRst = pickle.loads(msg[2][16:])
            try:
                self.searchwindow.isrequest = True
                self.searchwindow.isaccept = False
                self.searchwindow.id = self.searchRst['id']
                self.searchwindow.name = self.searchRst['name']
                self.searchwindow.head = self.searchRst['head']
                self.searchwindow.friendid.setText(str(self.searchRst['id']))
                self.searchwindow.friendname.setText(str(self.searchRst['name']))
                with open('./temp/head.png', 'wb') as f:
                    f.write(self.searchRst['head'])
                self.searchwindow.icon.setPixmap(QPixmap('./temp/head.png'))
                self.searchwindow.hl.addWidget(self.searchwindow.icon)
                self.searchwindow.hl.addWidget(self.searchwindow.friendid)
                self.searchwindow.hl.addWidget(self.searchwindow.friendname)
                self.searchwindow.icon.setVisible(True)
                self.searchwindow.friendid.setVisible(True)
                self.searchwindow.searchResult.setVisible(True)
                self.searchwindow.searchResult.setToolTip('点击发送加好友请求')
                self.friendRequestList.append(self.searchwindow.id)
            except Exception as e:
                print(e)
            print(self.searchRst)
        elif msg[2] == b'search_friend_NO':
            self.searchwindow.id = ''
            self.searchwindow.name = ''
            self.searchwindow.head = ''
            self.searchwindow.isrequest = True
            self.searchwindow.isaccept = False
            self.searchwindow.hl.removeWidget(self.searchwindow.icon)
            self.searchwindow.hl.removeWidget(self.searchwindow.friendid)
            self.searchwindow.icon.setHidden(True)
            self.searchwindow.friendid.setHidden(True)
            self.searchwindow.hl.removeWidget(self.searchwindow.friendname)
            self.searchwindow.friendname.setAlignment(Qt.AlignCenter)
            self.searchwindow.friendname.setText('用户不存在')
            self.searchwindow.hl.addWidget(self.searchwindow.friendname)
            self.searchwindow.searchResult.setVisible(True)
            self.searchwindow.searchResult.setToolTip('用户不存在')
        elif msg[2][:18] == b'add_friend_request':
            friendRequest = pickle.loads(msg[2][18:])
            print(friendRequest)
            self.addfriend.setStyleSheet('border-image:url(./pic/addfriend-dark1.svg);')
            print(f'{msg[0]}想加你为好友')
            self.searchwindow.isrequest = False
            self.searchwindow.isaccept = True
            self.searchwindow.id = friendRequest['id']
            self.searchwindow.name = friendRequest['name']
            self.searchwindow.head = friendRequest['head']
            self.searchwindow.friendid.setText(str(friendRequest['id']))
            self.searchwindow.friendname.setText(str(friendRequest['name']))
            with open('./temp/head.png', 'wb') as f:
                f.write(friendRequest['head'])
            self.searchwindow.icon.setPixmap(QPixmap('./temp/head.png'))
            self.searchwindow.hl.addWidget(self.searchwindow.icon)
            self.searchwindow.hl.addWidget(self.searchwindow.friendid)
            self.searchwindow.hl.addWidget(self.searchwindow.friendname)
            self.searchwindow.icon.setVisible(True)
            self.searchwindow.friendid.setVisible(True)
            self.searchwindow.searchResult.setVisible(True)
            self.searchwindow.searchResult.setToolTip(f'有来自{friendRequest["id"]}的好友请求')
        elif msg[2] == b'add_friend_accept':
            self.searchwindow.isrequest = False
            self.searchwindow.isaccept = True

            self.addfriend.setStyleSheet('border-image:url(./pic/addfriend-dark1.svg);')

            self.allUserInfo = self.cthandle.get_init_info()

            with open('./temp/head.png', 'wb') as f:
                for i in self.allUserInfo['friends']:
                    if str(i['id']) == msg[0]:

                        f.write(i['head'])
            self.refreshDialog(msg[0], './temp/head.png')

        else:
            if self.curmessage is None:
                return
            if self.curmessage != self.dialogdic[msg[0]]:
                exec(f'self.hint{str(self.dialogdic[msg[0]])}.setVisible(True)')
            self.insertMessage('', msg, False, True)
        try:
            exec(f'self.message{str(self.dialogdic[msg[0]])}.ensureVisible(9999, 9999)')
        except:
            pass

    def refreshDialog(self, id, head):
        try:
            index = len(self.dialoglist)
            self.createdialog(index, id, True, head)
            qss = ''''''
            for i in self.dialoglist.keys():
                qss += f'''QPushButton#dialogchoice{str(i)}''' + '''{background:#e3e3e3;border:none;}''' + \
                       f'''QPushButton#dialogchoice{str(i)}:''' + '''hover{background:#b8b8b8;}''' + \
                       f'''QPushButton#dialogchoice{str(i)}:''' + '''focus{background:#969696;}'''
                self.dialogwidget.setStyleSheet(qss)

            for i in self.dialoglist.keys():
                curdialog = self.dialoglist[i]
                curdialog.clicked.connect(self.openMessageWindow)

            self.allUserInfo = self.cthandle.get_init_info()
        except Exception as e:
            print(e)

    def sendMessage(self):
        if self.curmessage is None:
            return
        data = self.input.toPlainText()
        target = str(self.allUserInfo['friends'][self.curmessage]['id'])
        timestamp = str(time.time())
        self.cthandle.send_text(target, timestamp, data)
        self.input.clear()
        self.insertMessage(data, '', True, False)
        exec(f'self.message{str(self.curmessage)}.ensureVisible(9999, 9999)')

    def openMessageWindow(self):
        index = 0
        sender = self.sender()
        # print(self.curmessage)
        # print(sender)
        for i in self.dialoglist.keys():
            if sender == self.dialoglist[i]:
                index = i
                if index == self.curmessage:
                    return
                exec(f'self.message{str(index)}.setVisible(True)')
                break
        if self.curmessage is not None:
            self.messagelist[self.curmessage].setHidden(True)
        self.curmessage = index
        try:
            self.name.setText(self.allUserInfo['friends'][self.curmessage]['name'])
            exec(f'self.hint{str(self.curmessage)}.setHidden(True)')
        except Exception as e:
            print(e)

    def searchFriend(self):
        self.addfriend.setStyleSheet('border-image:url(./pic/addfriend-dark.svg);')
        self.setqss(self.mw)
        self.searchmw.show()

    def modifyHead(self):
        head, _ = QFileDialog.getOpenFileName(self.mw, '选择头像', os.getcwd(), "Image files (*.jpg *.gif *.png *.jpeg)")
        if _:
            img = cv2.imread(head)
            print(img.shape)
            img = cv2.resize(img, (50, 50))
            cv2.imwrite(f'./user/{str(self.allUserInfo["id"])}/head.png', img)
            self.userpic.setStyleSheet(f'border-image:url(./user/{str(self.allUserInfo["id"])}/head.png);')
            try:
                with open(f'./user/{str(self.allUserInfo["id"])}/head.png', 'rb') as f:
                    self.cthandle.send_request(b'modify_head' + pickle.dumps(f.read()), str(self.allUserInfo["id"]))
            except Exception as e:
                print(e)

    def insertMessage(self, text, msg, send=True, rcv=False, accept=False, video=False, audio=False):
        if send:
            msgbox = MessageBox(True, False)
            msgbox.icon.setStyleSheet(f'border-image:url(./user/{self.allUserInfo["id"]}/head.png);')
            msgbox.saying.setText(f' {text} ')
            msgbox.saying.adjustSize()
            msgbox.saying.setFixedSize(msgbox.saying.size())
            msgbox.saying.setMaximumHeight(30)
            if self.history[int(self.curmessage)]:
                if len(self.history[int(self.curmessage)]) != 5:
                    for i in self.history[int(self.curmessage)]:
                        exec(f'self.msglayout{str(self.curmessage)}.removeWidget(i)')
                exec(f'self.msglayout{str(self.curmessage)}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.curmessage)}.setAlignment(msgbox, Qt.AlignRight | Qt.AlignTop)')
                self.history[int(self.curmessage)].pop(0)
                for i in self.history[int(self.curmessage)]:
                    exec(f'self.msglayout{str(self.curmessage)}.addWidget(i)')
            else:
                exec(f'self.msglayout{str(self.curmessage)}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.curmessage)}.setAlignment(msgbox, Qt.AlignRight | Qt.AlignTop)')
        if rcv and not accept:
            msgbox = MessageBox(False, True)
            msgbox.icon.setStyleSheet(f'border-image:url(./user/{self.allUserInfo["id"]}/friends/head{msg[0]}.png);')
            msgbox.listening.setText(f' {msg[2].decode()} ')
            msgbox.listening.adjustSize()
            msgbox.listening.setFixedSize(msgbox.listening.size())
            msgbox.listening.setMaximumHeight(30)
            if self.history[self.dialogdic[msg[0]]]:
                if len(self.history[self.dialogdic[msg[0]]]) != 5:
                    for i in self.history[self.dialogdic[msg[0]]]:
                        exec(f'self.msglayout{self.dialogdic[msg[0]]}.removeWidget(i)')
                # print(self.history[self.dialogdic[msg[0]]])
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')
                self.history[self.dialogdic[msg[0]]].pop(0)
                for i in self.history[self.dialogdic[msg[0]]]:
                    exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(i)')
            else:
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')
        if rcv and accept and video:
            msgbox = MessageBox(False, True, True)
            msgbox.icon.setStyleSheet(f'border-image:url(./user/{self.allUserInfo["id"]}/friends/head{msg[0]}.png);')
            msgbox.accept.setText(f' {msg[2].decode()} ')
            msgbox.accept.adjustSize()
            msgbox.accept.setFixedSize(msgbox.accept.size())
            msgbox.accept.setMaximumHeight(30)
            msgbox.accept.clicked.connect(self.acceptVideo)
            if self.history[self.dialogdic[msg[0]]]:
                if len(self.history[self.dialogdic[msg[0]]]) != 5:
                    for i in self.history[self.dialogdic[msg[0]]]:
                        exec(f'self.msglayout{self.dialogdic[msg[0]]}.removeWidget(i)')
                # print(self.history[self.dialogdic[msg[0]]])
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')
                self.history[self.dialogdic[msg[0]]].pop(0)
                for i in self.history[self.dialogdic[msg[0]]]:
                    exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(i)')
            else:
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')
        if rcv and accept and audio:
            msgbox = MessageBox(False, True, True)
            msgbox.icon.setStyleSheet(f'border-image:url(./user/{self.allUserInfo["id"]}/friends/head{msg[0]}.png);')
            msgbox.accept.setText(f' {msg[2].decode()} ')
            msgbox.accept.adjustSize()
            msgbox.accept.setFixedSize(msgbox.accept.size())
            msgbox.accept.setMaximumHeight(30)
            msgbox.accept.clicked.connect(self.acceptAudio)
            if self.history[self.dialogdic[msg[0]]]:
                if len(self.history[self.dialogdic[msg[0]]]) != 5:
                    for i in self.history[self.dialogdic[msg[0]]]:
                        exec(f'self.msglayout{self.dialogdic[msg[0]]}.removeWidget(i)')
                # print(self.history[self.dialogdic[msg[0]]])
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')
                self.history[self.dialogdic[msg[0]]].pop(0)
                for i in self.history[self.dialogdic[msg[0]]]:
                    exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(i)')
            else:
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.addWidget(msgbox)')
                exec(f'self.msglayout{str(self.dialogdic[msg[0]])}.setAlignment(msgbox, Qt.AlignLeft | Qt.AlignTop)')

    def openVideo(self):
        if self.curmessage is not None:
            if not self.isVideoing:
                self.insertMessage('□◁ 发起视频请求', '', True, False)
                self.cthandle.send_request('video_request', str(self.allUserInfo['friends'][self.curmessage]['id']))
            elif self.isVideoing:
                self.isVideoing = False
                self.insertMessage('□◁ 视频通话结束', '', True, False)
                try:
                    self.cthandle.end_video()
                    self.cthandle.end_audio()
                except Exception as e:
                    print(e)
                self.video.setStyleSheet('border-image:url(./pic/video0.svg);video:hover{border-image:url('
                                         './pic/video1.svg);}')
                self.setqss(self.mw)

    def openAudio(self):
        if self.curmessage is not None:
            if not self.isAudioing:
                self.insertMessage('♬ 发起通话请求', '', True, False)
                self.cthandle.send_request('audio_request', str(self.allUserInfo['friends'][self.curmessage]['id']))
            elif self.isAudioing:
                self.isAudioing = False
                self.insertMessage('♬ 音频通话结束', '', True, False)
                try:
                    self.cthandle.end_audio()
                except Exception as e:
                    print(e)
                self.audio.setStyleSheet('border-image:url(./pic/video0.svg);video:hover{border-image:url('
                                         './pic/video1.svg);}')
                self.setqss(self.mw)

    def timeout_audio(self):
        try:
            self.isAudioing = False
            self.isTimeout_audio = True
            self.cthandle.end_audio()
            self.audio.setStyleSheet('border-image:url(./pic/video0.svg);video:hover{border-image:url('
                                     './pic/video1.svg);}')
            # self.setqss(self.mw)
        except Exception as e:
            print(e)

    def timeout(self):
        try:
            self.isVideoing = False
            self.isTimeout = True
            self.video.setStyleSheet('border-image:url(./pic/video0.svg);video:hover{border-image:url('
                                     './pic/video1.svg);}')
            # self.setqss(self.mw)
            self.cthandle.end_video()
            self.cthandle.end_audio()
        except Exception as e:
            print(e)

    def acceptVideo(self):
        self.isVideoing = True
        self.cthandle.send_request('video_accept', str(self.allUserInfo['friends'][self.curmessage]['id']))
        self.setqss(self.mw)
        self.video.setStyleSheet('border-image:url(./pic/video1.svg);}')
        try:
            self.cthandle.open_video(str(self.allUserInfo['friends'][self.curmessage]['id']), self.timeout)
        except Exception as e:
            print(e)

    def acceptAudio(self):
        self.isAudioing = True
        self.cthandle.send_request('audio_accept', str(self.allUserInfo['friends'][self.curmessage]['id']))
        self.setqss(self.mw)
        self.audio.setStyleSheet('border-image:url(./pic/video1.svg);}')
        try:
            self.cthandle.open_audio(str(self.allUserInfo['friends'][self.curmessage]['id']), self.timeout_audio)
        except Exception as e:
            print(e)

    def setqss(self, MainWindow):
        with open('homepage.qss', 'r') as f:
            qssStyle = f.read()
        MainWindow.setStyleSheet(qssStyle)

    def closepage(self):
        self.searchwindow.mw.close()
        self.mw.close()
        self.close()
        os._exit(0)
        sys.exit(0)

    def minimize(self):
        self.mw.setWindowState(Qt.WindowMinimized)

    def closeEvent(self, event):
        sys.exit(0)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.send.setText(_translate("MainWindow", "发送"))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Homepage(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())