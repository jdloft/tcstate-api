from redis import Redis
import os
import time
import requests
from stream import Stream
from predictor import Predictor

stream = Stream()
predictor = Predictor()
redis = Redis()

states = []

def update():
    print("Updating...")
    try:
        timestamp = stream.download('running/')
    except requests.exceptions.ConnectionError:
        return
    class_id = predictor.predict('running/' + str(timestamp) + '.jpg')
    os.remove('running/' + str(timestamp) + '.jpg')
    if len(states) >= 6:
        states.pop()
    states.append(class_id)
    print(states)
    new_avg = avg()
    print("Average: " + str(new_avg))
    redis.set('running-avg', new_avg)

def avg():
    count = 0
    for i in states:
        count += i
    return float(count) / len(states)

starttime = time.time()
interval = 10.0
while True:
    update()
    print('Sleeping %s...' % int((interval - ((time.time() - starttime) % interval))))
    time.sleep(interval - ((time.time() - starttime) % interval))