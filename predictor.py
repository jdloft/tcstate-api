import tensorflow as tf
from tensorflow import keras
import os
import numpy as np

IMG_HEIGHT = 150
IMG_WIDTH = 150

class Predictor:
    def __init__(self):
        self.model = keras.models.load_model('model')
        self.probability_model = tf.keras.Sequential([self.model, tf.keras.layers.Softmax()])
        print(self.model.summary())
        self.class_map = {0: 'night', 1: 'empty', 2: 'med', 3: 'full'}

    def predict(self, test_image):
        with open(test_image, 'rb') as input:
            try:
                test_image = tf.image.decode_jpeg(input.read())
            except:
                return 0
        test_image = tf.image.resize(test_image, (IMG_HEIGHT, IMG_WIDTH)).numpy()
        test_image = test_image / 255.0

        prediction = self.probability_model.predict(np.array([test_image]))
    
        prediction = np.argmax(prediction[0])
        return int(prediction)

    def reload(self):
        self.model = keras.models.load_model('model')

    def retrain(self, img, class_id):
        with open(img, 'rb') as input:
            test_image = tf.image.decode_jpeg(input.read())
        test_image = tf.image.resize(test_image, (IMG_HEIGHT, IMG_WIDTH)).numpy()
        test_image = test_image / 255.0
        one_hot = [0 for i in range(4)]
        one_hot[class_id] = 1
        self.model.fit(np.array([test_image]), np.array([one_hot]))
        self.model.save('model')
