import tensorflow as tf
from tensorflow import keras
from redis import Redis
import os
import numpy as np
import time

IMG_HEIGHT = 150
IMG_WIDTH = 150
interval = 10.0 #300.0 # 5 mins

redis = Redis()
model = keras.models.load_model('model')

def get_jobs(): # get lists from redis (blocking)
    timestamps = []
    states = []

    print("Waiting for timestamp...")
    timestamps.append(redis.blpop('suggestions-times')[1])
    print(timestamps)

    print("Waiting for state...")
    states.append(redis.blpop('suggestions-states')[1])
    print(states)

    # wait 5 mins for other suggestions
    print("Waiting 5 mins for more suggestions...")
    starttime = time.time()
    time.sleep(interval - ((time.time() - starttime) % interval))

    pipeline = redis.pipeline()
    pipeline.lrange('suggestions-times', 0, -1)
    pipeline.lrange('suggestions-states', 0, -1)
    pipeline.delete('suggestions-times')
    pipeline.delete('suggestions-states')
    output = pipeline.execute()

    timestamps += output[0]
    states += output[1]
    print(timestamps)
    print(states)
    assert len(timestamps) == len(states)

    return [int(i) for i in timestamps], [int(i) for i in states]

def get_params(timestamps, states): # list of timestamps to images (resized and normalized)
    images = []
    one_hots = []
    for i, timestamp in enumerate(timestamps):
        img = 'img/' + str(timestamp) + '.jpg'
        if os.path.isfile(img):
            with open(img, 'rb') as f:
                try:
                    img_file = tf.image.decode_jpeg(f.read())
                except:
                    print("Skipping invalid image " + str(timestamp))
                    continue
            img_file = tf.image.resize(img_file, (IMG_HEIGHT, IMG_WIDTH)).numpy()
            img_file = img_file / 255.0
            images.append(img_file)

            one_hot = [0 for j in range(4)]
            one_hot[states[i]] = 1
            one_hots.append(one_hot)
        else:
            print("Skipping " + str(timestamp))
    return images, one_hots

def get_onehots(states): # list of states to one hot lists
    one_hots = []
    for state in states:
        one_hot = [0 for i in range(4)]
        one_hot[state] = 1
        one_hots.append(one_hot)
    return one_hots


while True:
    timestamps, states = get_jobs()
    images, one_hots = get_params(timestamps, states)

    print(np.array(images).shape)
    print(one_hots)
    model.fit(np.array(images), np.array(one_hots))
    model.save('model')
    redis.set('update-model', 1)
