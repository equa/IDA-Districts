#background calculation of the pipe statics (change statics-steel-solver): a QgsTask with progress and cancel on a
#connection of its own; it never touches widgets, the report opens in finished() in the main thread
import traceback

import psycopg2.extras
from qgis.core import QgsTask

from . import statics_solve_db as ssd


class StaticsTask(QgsTask):
    """Calculates the version on conn (opened in the main thread, used only here) and writes the results.
    on_done(ok, payload): payload is the result dict, or the refusal / error text, or None when cancelled."""

    def __init__(self, description, conn, schema, on_done):
        #the default flags include cancel (no enum access, same on QGIS 3.44 and 4.2)
        super().__init__(description)
        self.conn, self.schema, self.on_done = conn, schema, on_done
        self.result, self.error, self.refused = None, None, None

    def run(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            result = ssd.calculate(cur, self.schema, progress=self.setProgress, cancelled=self.isCanceled)
            if result is None or self.isCanceled():
                return False
            ssd.writeResults(cur, self.schema, result)
            self.result = result
            return True
        except ssd.Refused as e:
            self.refused = str(e)
            return False
        except Exception:
            self.error = traceback.format_exc()
            return False

    def finished(self, ok):
        try:
            self.conn.close()
        except Exception:
            pass
        if ok:
            self.on_done(True, self.result)
        elif self.refused is not None:
            self.on_done(False, ('refused', self.refused))
        elif self.error is not None:
            self.on_done(False, ('error', self.error))
        else:
            self.on_done(False, None)
