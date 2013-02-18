import yaml
class Settings(object):
    def __init__(self, filename):
        with open(filename) as f:
            self.__dict__.update(yaml.load(f))

