from typing import Callable
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from time import sleep

from core import Rulesets, load_rules, parse_text


class Transcriber(QObject):
    """An object representing the background task of
    applying a ruleset to a string.
    This object is only intended for communication
    with _one_ frontend Window."""
    
    # signals for communicating with the 'parent window'
    new_transcription = pyqtSignal(str)

    def __init__(self, ruleset: str|None =None, *args, **kwargs) -> None:
        """Initializes a transcriber object."""
        # init parent class features
        super(Transcriber, self).__init__(*args, **kwargs)
        
        # store transcription requests
        self._want_transcribe = False
        self._transcribe_text = ''

        # store the currently loaded rulesets & the selected one
        self._rulesets = Rulesets()
        self._curr_ruleset = ''

        # store exit requests
        self._want_exit = False
        self._on_exit = lambda: None

        # we can init a transcriber object with a path to a ruleset
        if ruleset:
            self.load_ruleset(ruleset)

        # select a ruleset by default
        self._select_valid_ruleset()

    def __call__(self) -> None:
        """Makes this object usable in a QThreadpool."""
        self._main_loop()

    def request_exit(self, on_exit: Callable =lambda: None) -> None:
        """When this object finishes the current loop cycle
        it will terminate.
        
        on_exit - lambda to call when the transcriber exits,
                    overrides all previously set on_exits
        """
        self._want_exit = True
    
    @property
    def rulesets(self) -> list[str]:
        """Returns a list of all the names of the
        available rulesets."""
        return self._rulesets.names

    @property
    def selected_ruleset(self) -> str:
        """Returns the currently selected ruleset"""
        return self._curr_ruleset

    @selected_ruleset.setter
    def selected_ruleset(self, new_rlst: str) -> None:
        """If the given ruleset is available, select it.
        If not, raise an error."""
        
        if new_rlst not in self._rulesets:
            raise ValueError('The given ruleset name is not among the loaded ones.')

        self._curr_ruleset = new_rlst

    def load_ruleset(self, ruleset_pth: str) -> None:
        """Loads a ruleset from a specified path.
        The loaded set will be available only for this 
        object. Doesn't check if the current ruleset is
        the one to load (=> reloading possible)"""
        self._rulesets = load_rules(ruleset_pth)
        self._select_valid_ruleset()

    def request_transcr(self, text: str) -> None:
        """Schedules a transcription and cancels all pending ones."""
        self._want_transcribe = True
        self._transcribe_text = text

    # == implementation specific functions ==
    def _main_loop(self):
        # process and wait for new events
        while not self._want_exit:
            if self._want_transcribe:

                self.new_transcription.emit(
                    self._transcribe(
                        self._transcribe_text
                    )
                )
            
            sleep(0.01)
        self._on_exit()
    
    def _transcribe(self, text):
        # apply the currently selected ruleset to the given string
        ruleset = self._rulesets[self._curr_ruleset]
        return parse_text(text, ruleset)

    def _select_valid_ruleset(self):
        # select a ruleset from self._rulesets
        # (so no wrong one is selected)
        if (self._rulesets) and (self._curr_ruleset not in self._rulesets):
            self.selected_ruleset = self.rulesets[0]
