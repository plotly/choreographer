from .target import Target


class Tab(Target):
    def __init__(self, target_id, browser):
        super().__init__(target_id, browser)
