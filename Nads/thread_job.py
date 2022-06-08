import threading

class ThreadJob(threading.Thread):
    def __init__(self, callback, stop_event, interval):
        self.callback   = callback      # Callback function
        self.event      = stop_event    # Tells when to stop
        self.interval   = interval      # Interval to call callback func
        super(ThreadJob,self).__init__()

    def stop(self):
        self.event.set()

    def stopped(self):
        return self.event.is_set()

    def run(self):
        while not self.event.wait(self.interval):
            self.return_val = self.callback()
