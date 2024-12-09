from datetime import datetime

from choreographer.pipe import Pipe

data = [1, 2.00, 3, float("nan"), float("inf"), float("-inf"), datetime.today()]

def test_de_serialize():
    pipe = Pipe()
    obj = pipe.serialize(data)
    print(obj)
    pipe.deserialize(obj[:-1]) # split out \0


# TODO: Not sure if this all the data we have to worry about:
# we should also run through mocks and have it print data.
