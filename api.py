import flask
from flask import jsonify, request, send_from_directory
import json
import os
import glob
import shutil
import time
import sys
from redis import Redis
from tallies import Tallies

app = flask.Flask(__name__)

tallies = Tallies()
redis = Redis()
class_map = {0: 'night', 1: 'empty', 2: 'med', 3: 'full'}

@app.route('/current', methods=['GET'])
def current():
    output = {}
    current_img = redis.get('current-img')
    if current_img is not None:
        output['timestamp'] = int(current_img)

    current_pred = redis.get('current-pred')
    if current_pred is not None:
        output['state'] = int(current_pred)

    avg = redis.get('running-avg')
    if avg is not None:
        output['average'] = float(redis.get('running-avg'))
    else:
        output['average'] = 0.0
    return jsonify(output)

@app.route('/suggest', methods=['POST'])
def submit():
    try:
        timestamp = request.args.get('timestamp')
        state = int(request.args.get('state'))
    except ValueError:
        return '', 400

    if timestamp is None or state is None:
        return '', 400
    
    img = 'img/' + timestamp + '.jpg'
    if os.path.isfile(img):
        print('Found:', img)
        pipeline = redis.pipeline()
        pipeline.rpush('suggestions-times', timestamp)
        pipeline.rpush('suggestions-states', state)
        pipeline.execute()
    
    return ''

@app.route('/history', methods=['GET'])
def history():
    output = {}
    tallies.update_dayavgs()
    output['day'] = tallies.get_day(time.localtime().tm_wday)
    output['week'] = tallies.get_week()
    return jsonify(output)

@app.route('/current-img.jpg', methods=['GET'])
def current_img():
    timestamp = str(int(redis.get('current-img')))
    if os.path.isfile('img/' + timestamp + '.jpg'):
        app.logger.info('Found current image')
        return send_from_directory('img', timestamp + '.jpg')
    else:
        app.logger.info('Current image not found: img/%s.jpg', timestamp)
        return '', 404

app.run(host='0.0.0.0', port='12345')
