from telegram.ext import PicklePersistence
from job import JobMetadata

import pickle
import os.path

class CustomPersistence(PicklePersistence):
    def __init__(self, filename):
        super(CustomPersistence, self).__init__(filename)
        if os.path.isfile("{}_custom.pkl".format(self.filename)):
            with open("{}_custom.pkl".format(self.filename), "rb") as f:
                self.custom_data = pickle.load(f)
        else:
            self.custom_data = dict()
            self.custom_data['job_queue'] = dict()

    def save_custom_to_file(self):
        with open("{}_custom.pkl".format(self.filename), "wb") as f:
            pickle.dump(self.custom_data, f)

    def update_chat_data(self, chat_id, data):
        if 'job' in data:
            job = data['job']
            self.custom_data['job_queue'][job.name] = job
            self.save_custom_to_file()
        return super(CustomPersistence, self).update_chat_data(chat_id, data)

    def get_custom_data(self):
        return self.custom_data
