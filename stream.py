import os
import time
import requests

class Stream:
    url = 'https://testing.byu.edu/sites/all/scripts/cameraFeeds.php?camera=http%3A%2F%2Fusted%40ctl-tc-a.byu.edu%2Fimage%2Fjpeg.cgi'

    def download(self, dir):
        r = requests.get(self.url)
        timestamp = int(time.time())
        with open(dir + str(timestamp) + '.jpg', 'wb') as f:
            f.write(r.content)
        return timestamp
