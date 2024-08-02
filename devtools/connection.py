from .session import Session
from collections import OrderedDict


class Connection:
    def __init__(self, browser_process):
        self.browser_process = browser_process
        self.browser_session = Session(sessionId="")
        self.tab_sessions = OrderedDict()

    i=0
    def create_tab(self):
        global i
        self.browser_session = Session(str(i))
        global i = i + 1
        self.tab_sessions[self.browser_session.sessionId] = self.browser_session
        print("The session was created and added!")

    def open_tab(self):
        print(self.tab_sessions)

    def add_tab(self, session_id):
        self.browser_session = Session(session_id)
        self.tab_sessions[self.browser_session.sessionId] = self.browser_session
        print("The session was added!")
    
    def close_tab(self):
        self.tab_sessions = OrderedDict()
        print("The sessions was deleted!")