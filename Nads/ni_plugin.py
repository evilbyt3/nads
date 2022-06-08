import psutil
from thread_job import ThreadJob

class NISensor:
    def __init__(self, stop_event, interface):

        # Main dict that stores info about interfaces and traffic
        self.interface          = interface
        self.info               = {}
        self.info['conn']       = {}
        self.info['interfaces'] = {
            'info' : psutil.net_if_addrs(),
            'stats': psutil.net_if_stats()
        }
        self.info['traffic']    = psutil.net_io_counters(pernic=True)
        self.info['graph']      = {'percentage' : ''}
        self.pkts_recv          = self.info['traffic'][self.interface][3]
        self.pkts_sent          = self.info['traffic'][self.interface][2]
        self.pkts_drop_in       = self.info['traffic'][self.interface][6]
        self.pkts_drop_out      = self.info['traffic'][self.interface][7]
        self.stop_event         = stop_event    # Stop event for thread
        self.job                = None          # Thread


    def generate(self):
        # Start a thread job that calls update periodically
        self.job = ThreadJob(self.update, self.stop_event, 0.5)
        self.job.start()


    def stop(self):
        self.job.stop()


    def update(self):

        # Update the connections
        self.info['conn']['tcp']       = psutil.net_connections(kind = 'tcp')
        self.info['conn']['udp']       = psutil.net_connections(kind = 'udp')
        self.info['conn']['all']       = psutil.net_connections(kind = 'all')

        # Update the interface traffic
        self.info['traffic']    = psutil.net_io_counters(pernic=True)
        pkts_recv     = self.info['traffic'][self.interface][3]
        pkts_sent     = self.info['traffic'][self.interface][2]
        pkts_drop_in  = self.info['traffic'][self.interface][5]
        pkts_drop_out = self.info['traffic'][self.interface][6]
        self.info['graph']['percentage'] = (pkts_recv + pkts_sent) - (self.pkts_recv + self.pkts_sent)
        self.info['graph']['sent']     = pkts_sent - self.pkts_sent
        self.info['graph']['received'] = pkts_recv - self.pkts_recv
        self.info['graph']['drop_in' ] = pkts_drop_in  - self.pkts_drop_in
        self.info['graph']['drop_out'] = pkts_drop_out - self.pkts_drop_out
        self.pkts_recv     = pkts_recv
        self.pkts_sent     = pkts_sent
        self.pkts_drop_in  = pkts_drop_in
        self.pkts_drop_out = pkts_drop_out
