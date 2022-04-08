from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QObject

from typing import Literal

__all__ = [
    'file_dialog',
]


def file_dialog(type_: Literal['single']|Literal['many']|Literal['save'], caption: str|None = None, parent: QObject|None = None, filter: str = 'All Files (*)') -> str:
    if type_ == 'single':
        dialog_function = QFileDialog.getOpenFileUrl
    elif type_ == 'many':
        dialog_function = QFileDialog.getOpenFileUrls
    elif type_ == 'save':
        dialog_function = QFileDialog.getSaveFileUrl
    else:
        raise ValueError(f'The dialog type {type_!r} is not valid')
    
    return dialog_function(
        parent=parent,
        caption=caption,
        filter=filter,
        # options=QFileDialog.DontUseNativeDialog,
    )[0].toLocalFile()



