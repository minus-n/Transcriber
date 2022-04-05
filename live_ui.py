from typing import Iterable
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QAction, QMenu
from PyQt5.QtCore import pyqtSlot, QThreadPool, pyqtSignal, QObject
from PyQt5 import uic

import sys
from time import sleep
import functools

from load import load
from parse_text import parse_text


def transcr_to_select_action(names: Iterable[str], parent: 'TranscribeWindow') -> list[QAction]:
    out = []
    for name in names:
        action = QAction(name, parent)
        action.triggered.connect(
            functools.partial(parent.actionSelect_transcription,name)
        )
        out.append(action)    
    return out


class Transcriber(QObject):
    new_transcription_available = pyqtSignal(str)
    user_msg = pyqtSignal(str)
    new_transcription_table = pyqtSignal()

    def __init__(self, parent_window: 'TranscribeWindow', transcription_file):
        super(QObject, self).__init__()
        self.parent_window = parent_window
        
        self.transcription_requested = False
        self.text_to_transcribe = ''
        
        self.transcription_file = transcription_file
        self.transcription_table = load(self.transcription_file)
        try:
            self.transcription_type = self.transcription_types[0]
        except IndexError:
            self.transcription_type = ''
        self.rel_transcr_table_requested = False

        self.exit_requested = False

    @property
    def transcription_types(self):
        return sorted(self.transcription_table.available)

    @pyqtSlot(str)
    def request_transcription(self, text_to_transcribe):
        self.user_msg.emit(f'transcription ({self.transcription_type}) started…')
        self.transcription_requested = True
        self.text_to_transcribe = text_to_transcribe

    @pyqtSlot()
    def request_exit(self):
        self.exit_requested = True

    @pyqtSlot()
    def request_reload_transcription_table(self):
        self.rel_transcr_table_requested = True
        self.user_msg.emit(f'reloading conversion table ({self.transcription_type}@{self.transcription_file})')
 
    @pyqtSlot()
    def __call__(self):
        while not self.exit_requested:
            if self.transcription_requested:
                self.transcription_requested = False
                if not self.transcription_type:
                    self.new_transcription_available.emit(
                        self.text_to_transcribe
                    )
                else:
                    self.new_transcription_available.emit(
                        parse_text(self.text_to_transcribe, self.transcription_table, self.transcription_type)
                    )
                    self.user_msg.emit(f'transcription ({self.transcription_type}) finished')
            elif self.rel_transcr_table_requested:
                self.rel_transcr_table_requested = False
                self.transcription_table = load(self.transcription_file)
                self.parent_window.update_transcription()
                self.user_msg.emit('reloading conversion table finished.')
                if self.transcription_type not in self.transcription_types:
                    try:
                        self.transcription_type = self.transcription_types[0]
                    except IndexError:
                        self.transcription_type = ''

            sleep(0.05)
        



class TranscribeWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        uic.loadUi('main.ui', self)

        # typehint the used varibles, so my IDE knows their type and
        # to raise an error on non-existance
        self.input_text: QPlainTextEdit
        self.output_text: QPlainTextEdit
        self.actionReload_conversion_table: QAction
        self.actionExit: QAction
        self.menuConvert_to: QMenu

        # 'init' the text edits (makes placeholder text visible from the beginning)
        self.input_text.setPlainText('')
        self.output_text.setPlainText('')

        # initialize transcription worker
        self.threadpool = QThreadPool()
        self.transcriber = Transcriber(self, 'kana.yaml')
        self.threadpool.start(self.transcriber)

        # initialize text update
        self.input_text.textChanged.connect(self.update_transcription)
        self.transcriber.new_transcription_available.connect(self.transcription_available)

        # initialize button/menu functionality
        self.actionReload_conversion_table.triggered.connect(
            self.transcriber.request_reload_transcription_table
        )
        self.actionExit.triggered.connect(self.close)
        self.set_available_transcriptions()
        self.transcriber.new_transcription_table.connect(
            self.set_available_transcriptions
        )

        # the transcriber will occasionally send some messages
        self.transcriber.user_msg.connect(self.show_user_msg)

    @pyqtSlot(str)
    def actionSelect_transcription(self, transcr):
        self.transcriber.transcription_type = transcr
        self.update_transcription()

    @pyqtSlot()
    def set_available_transcriptions(self):
        self.menuConvert_to.clear()
        self.menuConvert_to.addActions(
            transcr_to_select_action(
                self.transcriber.transcription_types,
                self
            )
        )

    @pyqtSlot(str)
    def show_user_msg(self, msg):
        self.statusBar().showMessage(msg, msecs=700)

    def update_transcription(self):
        self.transcriber.request_transcription(self.input_text.toPlainText())
    
    pyqtSlot(str)
    def transcription_available(self, new_text):
        self.output_text.setPlainText(new_text)

    def closeEvent(self, event):
        self.transcriber.request_exit()
        super(QMainWindow, self).closeEvent(event)


app = QApplication(sys.argv)
w = TranscribeWindow()
w.show()
app.exec()
