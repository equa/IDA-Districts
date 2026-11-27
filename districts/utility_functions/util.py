import ctypes
import json
import time
from win32 import win32process, win32event
import sys
import os
from .compat import MessageCritical, MessageWarning
import traceback

from qgis.core import QgsMessageLog, Qgis
from .compat import MessageInfo
from .debug_log import dprint, debug_enabled
from .translations import tr_msg
from .hidden_simulation import windowOptions

# IDA registers with its message broker when it accepts API calls; the line is not documented by the IDA API
BROKER_LOG = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'equa', 'ida_message_broker_log.txt')
REGISTER_MAX_WAIT = 60
OPEN_MAX_WAIT = 180
POLL_INTERVAL = 0.2


class IdaOpenError(Exception):
    """The first model of an IDA session could not be opened; text is IDA's answer or the reason."""
    def __init__(self, path, text):
        super().__init__('{}: {}'.format(path, text))
        self.path = path
        self.text = text


def fileSize(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return None


class Util_api:
    def __init__(self,plugin_dir,config,submodel='1',hidden=False):
        # Define your path to the IDA Districts bin folder here
        path_to_districts = config['pathDistricts'].replace("\\","\\\\")+"bin\\\\"
        command = "\""+path_to_districts + "ida-districts.exe\" \"" + path_to_districts + "ida.img\" -G1 -C " + str(submodel)+'_'+time.strftime("%m%d%H%M%S", time.localtime())
        if windowOptions(hidden):
            command += " " + " ".join(windowOptions(hidden))
        dprint(command)
        # before the start: the registration of this process is looked for only after this offset
        self.broker_log = BROKER_LOG
        self.log_offset = fileSize(self.broker_log)
        startObj = win32process.STARTUPINFO()
        ret = win32process.CreateProcess(None,command,None,None,0,0,None,None,startObj)
        self.start_time = time.monotonic()
        self.process_handle = ret[0]
        self.pid = str(ret[2])
        dprint(self.pid)
        #Add path_to_districts to PATH variable, is removed when program finishes
        os.environ['PATH'] = path_to_districts + os.pathsep  + os.environ['PATH']


        self.ida_lib = ctypes.CDLL(path_to_districts + 'x64\\idaapi2.dll')

        self.ida_lib.connect_to_ida.restype = ctypes.c_bool
        self.ida_lib.connect_to_ida.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.ida_lib.switch_remote_connection.restype = ctypes.c_bool
        self.ida_lib.switch_remote_connection.argtypes = [ctypes.c_char_p]
        self.ida_lib.switch_api_version.restype = ctypes.c_bool
        self.ida_lib.switch_api_version.argtypes = [ctypes.c_long]
        self.ida_lib.call_ida_function.restype = ctypes.c_long
        self.ida_lib.call_ida_function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.ida_disconnect.restype = ctypes.c_bool
        self.ida_lib.ida_disconnect.argtypes = []
        self.ida_lib.get_err.restype = ctypes.c_long
        self.ida_lib.get_err.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.childNodes.restype = ctypes.c_long
        self.ida_lib.childNodes.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.parentNode.restype = ctypes.c_long
        self.ida_lib.parentNode.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.setParentNode.restype = ctypes.c_long
        self.ida_lib.setParentNode.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.hasChildNodes.restype = ctypes.c_long
        self.ida_lib.hasChildNodes.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.firstChild.restype = ctypes.c_long
        self.ida_lib.firstChild.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.lastChild.restype = ctypes.c_long
        self.ida_lib.lastChild.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.nextSibling.restype = ctypes.c_long
        self.ida_lib.nextSibling.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.previousSibling.restype = ctypes.c_long
        self.ida_lib.previousSibling.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.childNodesLength.restype = ctypes.c_long
        self.ida_lib.childNodesLength.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.setNodeValue.restype = ctypes.c_long
        self.ida_lib.setNodeValue.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.cloneNode.restype = ctypes.c_long
        self.ida_lib.cloneNode.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.insertBefore.restype = ctypes.c_long
        self.ida_lib.insertBefore.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.createNode.restype = ctypes.c_long
        self.ida_lib.createNode.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.contains.restype = ctypes.c_long
        self.ida_lib.contains.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.domAncestor.restype = ctypes.c_long
        self.ida_lib.domAncestor.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.item.restype = ctypes.c_long
        self.ida_lib.item.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.appendChild.restype = ctypes.c_long
        self.ida_lib.appendChild.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.removeChild.restype = ctypes.c_long
        self.ida_lib.removeChild.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.replaceChild.restype = ctypes.c_long
        self.ida_lib.replaceChild.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.setAttribute.restype = ctypes.c_long
        self.ida_lib.setAttribute.argtypes = [ctypes.c_char_p, ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.getAttribute.restype = ctypes.c_long
        self.ida_lib.getAttribute.argtypes = [ctypes.c_char_p, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.openDocument.restype = ctypes.c_long
        self.ida_lib.openDocument.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.openDocByTypeAndName.restype = ctypes.c_long
        self.ida_lib.openDocByTypeAndName.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.saveDocument.restype = ctypes.c_long
        self.ida_lib.saveDocument.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.runSimulation.restype = ctypes.c_long
        self.ida_lib.runSimulation.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.pollForQueuedResults.restype = ctypes.c_long
        self.ida_lib.pollForQueuedResults.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.getZones.restype = ctypes.c_long
        self.ida_lib.getZones.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.getWindows.restype = ctypes.c_long
        self.ida_lib.getWindows.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.getChildrenOfType.restype = ctypes.c_long
        self.ida_lib.getChildrenOfType.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.findNamedChild.restype = ctypes.c_long
        self.ida_lib.findNamedChild.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.exitSession.restype = ctypes.c_long
        self.ida_lib.exitSession.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.getAllSubobjectsOfType.restype = ctypes.c_long
        self.ida_lib.getAllSubobjectsOfType.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.runIDAScript.restype = ctypes.c_long
        self.ida_lib.runIDAScript.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.copyObject.restype = ctypes.c_long
        self.ida_lib.copyObject.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.findObjectsByCriterium.restype = ctypes.c_long
        self.ida_lib.findObjectsByCriterium.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.findUseOfResource.restype = ctypes.c_long
        self.ida_lib.findUseOfResource.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_int]
        self.ida_lib.printReport.restype = ctypes.c_long
        self.ida_lib.printReport.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_long, ctypes.c_char_p, ctypes.c_int]

    #Utility functions
    def elapsed(self):
        return time.monotonic() - self.start_time

    def process_ended(self):
        try:
            return win32event.WaitForSingleObject(self.process_handle, 0) == win32event.WAIT_OBJECT_0
        except Exception:
            return False

    def new_log_lines(self):
        """Complete lines added to the broker log since the last read, None if it cannot be read."""
        if self.log_offset is None:
            return None
        size = fileSize(self.broker_log)
        if size is None:
            return None
        if size < self.log_offset:
            self.log_offset = 0
        try:
            with open(self.broker_log, 'rb') as f:
                f.seek(self.log_offset)
                data = f.read(size - self.log_offset)
        except OSError:
            return None
        # a line still being written is read again next time
        end = data.rfind(b'\n') + 1
        self.log_offset += end
        return [line.strip() for line in data[:end].decode('utf-8', 'replace').splitlines()]

    def wait_for_registration(self, max_wait=REGISTER_MAX_WAIT):
        """'registered', 'ended' (IDA process gone) or 'unknown' (no log, or no line within max_wait)"""
        needle = 'Registering...: {}'.format(self.pid)
        while True:
            lines = self.new_log_lines()
            if lines is None:
                return 'unknown'
            if needle in lines:
                return 'registered'
            if self.process_ended():
                return 'ended'
            if self.elapsed() >= max_wait:
                return 'unknown'
            time.sleep(POLL_INTERVAL)

    def open_document(self, path, max_wait=OPEN_MAX_WAIT):
        """Open the first model of this session: wait for IDA's registration, then openDocument, retried after a
        timeout (a call sent before IDA is ready is never answered, and the connection only works again after a
        new connect_to_ida). Returns the document handle or raises IdaOpenError."""
        state = self.wait_for_registration()
        if state == 'ended':
            raise IdaOpenError(path, tr_msg('IDA Districts ended during the start'))
        if state == 'unknown':
            QgsMessageLog.logMessage(tr_msg('IDA Districts registration not found after {} s, opening anyway')
                                     .format(round(self.elapsed())), 'Districts', MessageInfo)
        while True:
            self.ida_lib.connect_to_ida(b"5945", self.pid.encode())
            result = self.call_ida_api_function(self.ida_lib.openDocument, path.encode('utf-8'))
            if isinstance(result, int) and not isinstance(result, bool) and result > 0:
                return result
            text = str(result)
            if not text.startswith('Timeout'):
                raise IdaOpenError(path, text)
            if self.process_ended():
                raise IdaOpenError(path, tr_msg('IDA Districts ended during the start'))
            if self.elapsed() >= max_wait:
                raise IdaOpenError(path, text)
            QgsMessageLog.logMessage(tr_msg('IDA Districts not ready after {} s, retrying')
                                     .format(round(self.elapsed())), 'Districts', MessageInfo)

    def exit_ida(self,doc=None,timeout=30):
        """Close the IDA Districts session started by this Util_api.
        Sends the lisp function (exit-ida) via runIDAScript (needs an open document), otherwise the API
        function exitSession (slower: ~15 s). No result is polled (IDA terminates). Waits up to timeout seconds for the
        process to end and terminates it if it is still running (e.g. a modal error dialog in IDA).
        ida_disconnect is NOT called: idaapi2.dll is loaded once per QGIS process and after ida_disconnect its connection
        cannot be opened again (connect_to_ida of the next IDA session returns False, 'not a socket' from zmq), so every
        later simulation in the same QGIS session failed. connect_to_ida of the next session switches the connection."""
        p = ctypes.create_string_buffer(32000)
        try:
            #openDocument returns the document handle (int) or an error text
            if isinstance(doc,int) and doc:
                self.ida_lib.runIDAScript(doc, b"(exit-ida)", p, len(p))
            else:
                self.ida_lib.exitSession(p, len(p))
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), "Districts", MessageCritical)
        try:
            if win32event.WaitForSingleObject(self.process_handle, int(timeout*1000)) != win32event.WAIT_OBJECT_0:
                win32process.TerminateProcess(self.process_handle, 1)
                QgsMessageLog.logMessage("IDA Districts (pid {}) did not exit, terminated".format(self.pid), "Districts", MessageWarning)
        except Exception:
            #process already ended / handle closed
            pass

    def ida_poll_results_queue (self,time_interval):
      size = 32000
      doc_str = ctypes.create_string_buffer(size) 
      poll_result = False
      while poll_result is not None and not poll_result:
        time.sleep(time_interval)
        poll_res = self.ida_lib.pollForQueuedResults(doc_str, len(doc_str))
        reply = doc_str.value.decode("utf-8")
        # an empty reply: no answer yet
        if reply.strip():
          try:
            poll_result2 = json.loads(reply)
            dprint(poll_result2)
            if isinstance(poll_result2, list):
              if debug_enabled(): dprint(poll_result2[0]['value'])
              poll_result = poll_result2[0]['value']
            else:
              return ""
          except Exception:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            )
        # an IDA that ended never answers: the caller would wait forever
        if poll_result is not None and not poll_result and self.process_ended():
          QgsMessageLog.logMessage(tr_msg('IDA Districts (pid {}) ended without an answer').format(self.pid), "Districts", MessageCritical)
          return ""
      return poll_result2[1]['value']

    def call_ida_api_function (self,fun, *args):
      "Just send in the function name and its unique arguments (not out buffer and out buffer length)" 
      p = ctypes.create_string_buffer(32000)    
      args = args + (p,len(p))
      res = fun(*args)
      if res == 0:
        return self.ida_poll_results_queue(0.1)
      elif res > 0 :
        p = ctypes.create_string_buffer(res) 
        res = fun(*args)
        if res == 0:
          return self.ida_poll_results_queue(0.1)
        else:
          return ""
      else:
          res2 = self.ida_lib.get_err(p,len(p))
          return p.value.decode("utf-8")

    def call_ida_api_function_j (self,fun, *args):
      "Just send in the function name and its unique arguments (not out buffer and out buffer length)" 
      p = ctypes.create_string_buffer(32000)    
      args = args + (p,len(p))
      res = fun(*args)
      if res == 0:
        return p
      else:
        p = ctypes.create_string_buffer(res) 
        res = fun(*args)
        if res == 0:
          return p
        else:
          return ""

    def ida_poll_results_queue_j (self,time_interval):
      size = 32000
      doc_str = ctypes.create_string_buffer(size) 
      poll_result = False
      while poll_result is not None and not poll_result:
        time.sleep(time_interval)
        poll_res = self.ida_lib.pollForQueuedResults(doc_str, len(doc_str))
        reply = doc_str.value.decode("utf-8")
        if reply.strip():
          poll_result2 = json.loads(reply)
          if isinstance(poll_result2, list):
            poll_result = poll_result2[0]['value']
          else:
            return ""
        if poll_result is not None and not poll_result and self.process_ended():
          QgsMessageLog.logMessage(tr_msg('IDA Districts (pid {}) ended without an answer').format(self.pid), "Districts", MessageCritical)
          return ""
      return json.dumps(poll_result2[1])

    def ida_get_named_child(self,par,name):
      site_res = self.call_ida_api_function(self.ida_lib.findNamedChild,par, name.encode())
      return site_res

    def ida_get_value(self,par):
      val = self.call_ida_api_function(self.ida_lib.getAttribute,b"VALUE", par)
      return val

    def ida_get_name(self,par):
      val = self.call_ida_api_function(self.ida_lib.getAttribute,b"NAME", par)
      return val
