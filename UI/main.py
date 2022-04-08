from collections import OrderedDict
from functools import partial
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
        self.menu_select_ruleset: QMenu

        # start transcriber job
        self._transcr_job_running = False
        self._threadpool = QThreadPool(self)
        self._transcr_job = Transcriber(ruleset)
        self.current_ruleset = ruleset
        self._start_transcr_job()

        # connect listeners
        self.input_text.textChanged.connect(self.update_transcr)
        self._transcr_job.new_transcription.connect(self._set_parsed_text)
        self.action_exit.triggered.connect(self.close)
        self.action_rel_ruleset.triggered.connect(self.reload_rulesets)

        # if the text of the QPlainTextEdit is not explicitly
        # set to "", the placeholder text will not be shown
        self.input_text.setPlainText('')
        self.output_text.setPlainText('')

        # store actions that trigger the current rulesets
        self.actions_select_ruleset: OrderedDict[str, QAction] = \
                OrderedDict()

    def show_msg(self, msg: str, hold: int) -> None:
        """Shows a message to the user for ~at~least~ 'hold' milliseconds."""
        self.statusBar().showMessage(msg, hold)

    # == interaction with the transcriptor ==
    def select_ruleset(self, ruleset: str) -> None:
        """Forwards the given ruleset name to the background
        transcription job."""
        self._transcr_job.selected_ruleset = ruleset
        self.update_transcr()

    @pyqtSlot()
    def reload_rulesets(self) -> None:
        """Forwards the reload of the ruleset to 
        the transcription job."""
        self._transcr_job.load_ruleset(self.current_ruleset)
        self._clear_rulesets_menu()
        self._fill_rulesets_menu()

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

    # == non-public functions ==
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

    def _clear_rulesets_menu(self) -> None:
        # clears the menu of rulesets to select and
        # clears up the QActions in self.actions_select_ruleset
        for ruleset_name, sel_action in self.actions_select_ruleset.items():
            self.menu_select_ruleset.removeAction(sel_action)
            sel_action.triggered.disconnect()

        self.actions_select_ruleset.clear()

    def _fill_rulesets_menu(self) -> None:
        # populates the menu of rulesets to select
        for ruleset_name in self._transcr_job.rulesets:
            # select ruleset action
            sel_rlst_action = QAction(ruleset_name, self)
            self.actions_select_ruleset[ruleset_name] = sel_rlst_action
            sel_rlst_action.triggered.connect(
                partial(self.select_ruleset, ruleset_name)
            )
        
            self.menu_select_ruleset.addAction(sel_rlst_action)

