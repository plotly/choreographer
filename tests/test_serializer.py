from datetime import datetime

from choreographer.pipe import Pipe

data = [1, 2.00, 3, float("nan"), float("inf"), float("-inf"), datetime.today()]

def test_de_serialize():
    pipe = Pipe()
    obj = pipe.serialize(data)
    pipe.deserialize(obj[:-1]) # split out \0
