import flask
from flask import jsonify, request, send_from_directory
import json
import os
import glob
import shutil
import time
import sys
from redis import Redis
from stream import Stream
from predictor import Predictor
from tallies import Tallies

app = flask.Flask(__name__)
app.config['DEBUG'] = True

stream = Stream()
predictor = Predictor()
tallies = Tallies()
redis = Redis()
class_map = {0: 'night', 1: 'empty', 2: 'med', 3: 'full'}

@app.route('/current', methods=['GET'])
def current():
    output = {}
    output['timestamp'] = stream.download('api/unclass/')
    avg = redis.get('running-avg')
    if avg is not None:
        output['average'] = float(redis.get('running-avg'))
    else:
        output['average'] = 0.0
    return jsonify(output)

@app.route('/prediction/<timestamp>', methods=['GET'])
def prediction(timestamp):
    image = 'api/unclass/' + timestamp + '.jpg'
    output = {}
    output['class'] = predictor.predict(image)
    date = time.localtime(int(timestamp))
    tallies.tally(date.tm_wday, date.tm_hour, output['class'])
    shutil.copy(image, 'api/sorted/' + predictor.class_map[output['class']] + '/' + os.path.basename(image))
    return jsonify(output)

@app.route('/suggest', methods=['POST'])
def submit():
    try:
        timestamp = request.args.get('timestamp')
        class_id = int(request.args.get('class'))
    except ValueError:
        return '', 400

    if timestamp is None or class_id is None:
        return '', 400
    
    found = glob.glob('api/sorted/*/' + timestamp + '.jpg')
    print('Found:', found)
    if len(found) >= 1:
        os.rename(found[0], 'api/sorted/' + class_map[class_id] + '/' + os.path.basename(found[0]))
    
    return ''

@app.route('/history', methods=['GET'])
def history():
    output = {}
    tallies.update_dayavgs()
    output['day'] = tallies.get_day(time.localtime().tm_wday)
    output['week'] = tallies.get_week()
    return jsonify(output)

@app.route('/img/<path:path>')
def return_img(path):
    print('Serving static image ' + path, file=sys.stderr)
    return send_from_directory('unclass', path)

app.run(port='12345')
