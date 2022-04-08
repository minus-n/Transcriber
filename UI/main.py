import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi

from pathlib import Path
from typing import NoReturn

from UI.background_tasks import Transcriber
from .util import file_dialog

def start_ui(rules_file: str|None =None) -> NoReturn:
    """Starts the ui and calls the main loop.
    Until the main loop exits this function will not return.
    """

    app = QApplication(sys.argv)

    if rules_file is None:
        rules_file = file_dialog(
            type_='single',
            caption='Please choose a ruleset file',
            filter='Ruleset-Files (*.yaml);;All Files (*)'
        )
    
    window = TranscribeWindow(rules_file)
    window.show()

    app.exec()



class TranscribeWindow(QMainWindow):
    """Main Window of this application.
    Lets the user enter a string and transcribes it on the fly.
    """

    def __init__(self, ruleset: str | None = None, *args, **kwargs) -> None:
        """Initializes a TranscribeWindow object."""
        # init parent class features
        super(QMainWindow, self).__init__(*args, **kwargs)

        # load the ui from a .ui file
        curr_dir = Path(__file__).parent.resolve()
        ui_file = curr_dir / 'main.ui'
        loadUi(ui_file.absolute(), self)

        # make sure necessary fields exist
        self.input_text: QPlainTextEdit
        self.output_text: QPlainTextEdit
        self.action_rel_ruleset: QAction
        self.action_exit: QAction
        self.statusbar: QStatusBar

        # start transcriber job
        self._transcr_job_running = False
        self._threadpool = QThreadPool(self)
        self._transcr_job = Transcriber(ruleset)
        self._start_transcr_job()

        # connect listeners
        self.input_text.textChanged.connect(self.update_transcr)
        self._transcr_job.new_transcription.connect(self._set_parsed_text)

        # if the text of the QPlainTextEdit is not explicitly
        # set to "", the placeholder text will not be shown
        self.input_text.setPlainText('')
        self.output_text.setPlainText('')

    
    def show_msg(self, msg: str, hold: int) -> None:
        """Shows a message to the user for ~at~least~ 'hold' milliseconds."""
        self.statusBar().showMessage(msg, hold)

    def select_ruleset(self, ruleset: str) -> None:
        """Forwards the given ruleset name to the background
        transcription job."""
        self._transcr_job.selected_ruleset = ruleset

    @pyqtSlot()
    def update_transcr(self) -> None:
        """Sends an update request to the transcriber job."""
        if self._transcr_job_running:
            self._transcr_job.request_transcr(
                self.input_text.toPlainText()
            )

    def closeEvent(self, *args, **kwargs) -> None:
        """Override the default closeEvent to ask the
        transcription job to finish too."""
        self._transcr_job.request_exit()
        return super(TranscribeWindow, self).closeEvent(*args, **kwargs)

    # == implementation specific functions ==
    @pyqtSlot(str)
    def _set_parsed_text(self, text: str) -> None:
        # sets the text in the "parsed" text field
        self.output_text.setPlainText(text)

    def _start_transcr_job(self) -> None:
        # starts the transcribing background job
        if not self._transcr_job_running:
            self._threadpool.start(self._transcr_job)
            self._transcr_job_running = True
            
    def _end_transcr_job(self) -> None:
        # asks the transcriber job to finish and exit
        if self._transcr_job_running:
            def set_running_to_false():
                self._transcr_job_running = False

            self._transcr_job.request_exit(set_running_to_false)
