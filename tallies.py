import os
import glob
import redis
import time

class_map = {'night': 0, 'empty': 1, 'med': 2, 'full': 3}

class Tallies:
    def __init__(self):
        self.redis = redis.Redis()

    def read(self, dir):
        for image in glob.glob(dir + '*/*.jpg'):
            timestamp = int((os.path.splitext(os.path.basename(image)))[0])
            date = time.localtime(timestamp)
            class_id = class_map[os.path.split(os.path.split(image)[0])[1]]
            if class_id > 0:
                self.tally(date.tm_wday, date.tm_hour, class_id)
        self.update_dayavgs()

    def tally(self, day, hr, weight):
        print('Tallying day:', day, ':', hr, ':weight =', weight)
        weight = int(self.redis.incr('day:' + str(day) + ':' + str(hr) + ':weight', weight))
        count = int(self.redis.incr('day:' + str(day) + ':' + str(hr) + ':count'))
        self.redis.set('day:' + str(day) + ':' + str(hr) + ':avg', float(weight) / count)

    def update_dayavgs(self):
        print('Updating day averages')
        for day in range(7):
            avgs = 0
            for hr in range(24):
                avg = self.redis.get('day:' + str(day) + ':' + str(hr) + ':avg')
                if avg is not None:
                    avgs += float(avg)
            self.redis.set('day:' + str(day) + ':avg', float(avgs) / 7)

    def get_day(self, day):
        out = []
        for hr in range(24):
            avg = self.redis.get('day:' + str(day) + ':' + str(hr) + ':avg')
            if avg is not None:
                out.append(float(avg))
            else:
                out.append(0.0)
        return out

    def get_week(self):
        out = []
        for day in range(7):
            avg = self.redis.get('day:' + str(day) + ':avg')
            if avg is not None:
                out.append(float(avg))
            else:
                out.append(0.0)
        return out
    
    def clear_server(self):
        for day in range(7):
            for hr in range(24):
                self.redis.delete('day:' + str(day) + ':' + str(hr) + ':weight')
                self.redis.delete('day:' + str(day) + ':' + str(hr) + ':count')
                self.redis.delete('day:' + str(day) + ':' + str(hr) + ':avg')
            self.redis.delete('day:' + str(day) + ':avg')
