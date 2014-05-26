import win32serviceutil
import win32service
import win32event
import servicemanager

import sclient

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "MementoClient"
    _svc_display_name_ = "Memento Client"

    _socket = None

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._socket.close()

        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        port = 4444
        address = ""
        ssl = {
            "enabled": False,
            "pem": None,
            "password": None
        }

        self._socket = sclient.get_socket(port, address, ssl)
        sclient.serve(self._socket)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)