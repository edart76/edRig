# little window that writes down every single time you embarrass yourself
import sys
from PySide2 import QtCore, QtWidgets
import logging

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
        # originally: XStream.stdout().write("{}\n".format(record))

logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
# try to get this on a per-widget basis


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.Signal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(unicode(msg))
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class LoggingWidget(QtWidgets.QDialog):
    def __init__( self, parent = None ):
        super(LoggingWidget, self).__init__(parent)

        self._console = QtWidgets.QTextBrowser(self)

        XStream.stdout().messageWritten.connect( self._console.insertPlainText )
        XStream.stderr().messageWritten.connect( self._console.insertPlainText )
