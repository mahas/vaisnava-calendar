import sys
import os
import os.path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import gaurabda as G
import gaurabda.TServer as GS

GCAL_PORT = int(os.getenv("PORT", os.getenv("GCAL_SERVER_PORT", 8047)))

GS.run_server(host="0.0.0.0", port=GCAL_PORT)