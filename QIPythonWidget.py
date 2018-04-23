# encoding: UTF-8
from PyQt4.QtGui  import *
#from qtconsole.qt import QtGui
from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

##########################################################################
class QIPythonWidget(RichJupyterWidget):
    """ Convenience class for a live IPython console widget"""
    #---------------------------------------------------------------------
    def __init__(self,ctaEngine, eventEngine, parent, customBanner=None,*args,**kwargs):

        banner = u""
        banner += u"\nkTool.datas : 行情数据"
        banner += u"\nkTool.parent.spdData : 开仓点分析"
        super(QIPythonWidget, self).__init__(banner = banner)

        #self.setFixedWidth(420)

        if customBanner is not None: self.banner=customBanner

        self.font_size = 6
        self._display_banner = False
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=False)
        kernel_manager.kernel.gui = 'qt'
        self.kernel_client = kernel_client = self.kernel_manager.client()
        kernel_client.start_channels()
        
        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()            
        self.exit_requested.connect(stop)

    #---------------------------------------------------------------------
    def pushVariables(self,variableDict):
        """ 
        Given a dictionary containing name / value pairs,
        push those variables to the IPython console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)
    #---------------------------------------------------------------------
    def clearTerminal(self):
        """
        Clears the terminal
        """
        self._control.clear()    

    #---------------------------------------------------------------------
    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    #---------------------------------------------------------------------
    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)
