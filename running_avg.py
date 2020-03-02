from redis import Redis
import os
import time
import requests
from stream import Stream
from tallies import Tallies
from predictor import Predictor

stream = Stream()
tallies = Tallies()
predictor = Predictor()
redis = Redis()

states = []

def update():
    print("Updating...")
    try:
        timestamp = stream.download('img/')
    except:
        print("Error downloading new stream")
        return

    if timestamp is None:
        print("Stream downloader returned None (probably 500 error from server)")
        return

    class_id = predictor.predict('img/' + str(timestamp) + '.jpg')
    date = time.localtime(int(timestamp))
    tallies.tally(date.tm_wday, date.tm_hour, class_id)

    if len(states) >= 6:
        states.pop()
    states.append(class_id)
    print(states)

    new_avg = avg()
    print("Current img " + str(timestamp) + " prediction: " + str(class_id))
    print("Average: " + str(new_avg))
    redis.set('current-img', timestamp)
    redis.set('current-pred', class_id)
    redis.set('running-avg', new_avg)

def avg():
    count = 0
    for i in states:
        count += i
    return float(count) / len(states)

starttime = time.time()
interval = 10.0
while True:
    reload = redis.get('update-model')
    if reload is not None and int(reload) == 1:
        print("Reloading!")
        predictor.reload()
        redis.set('update-model', 0)
    update()
    print('Sleeping %s...' % int((interval - ((time.time() - starttime) % interval))))
    time.sleep(interval - ((time.time() - starttime) % interval))