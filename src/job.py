from telegram.ext import Job
class JobMetadata():
    def __init__(self, interval, name, context):
        self.name = name
        self.interval = interval
        self.context = context
