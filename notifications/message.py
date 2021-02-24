

class Message:

    def __init__(self, message=None):
        self.message = message or {'body': '', 'type': None} 

    def serialize(self):
        return self.message