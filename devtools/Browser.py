from app.app_utils import Pipe
from collections import OrderedDict

class Browser:
    def __init__(self):
        self.pipes = OrderedDict()
        self.subprocess = OrderedDict()