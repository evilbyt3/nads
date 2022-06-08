import thread_job
from scapy.all import *


class Sniffer:
    def __init__(self, stop_event, interface):
        self.interface  = interface
        self.stop_event = stop_event    # Stop event for thread
        self.job        = None          # Thread
        self.counter    = 0             # Counter of packets
        self.info       = None          # Packet data
        self.stopped    = False         # Stop boolean

    def generate(self):
        # Start the thread
        self.job = thread_job.ThreadJob(self.update, self.stop_event, 0.1)
        self.job.start()

    def stop(self):
        self.stopped = True
        self.job.stop()

    def check(self):
        return self.stopped


    def handle_pkts(self, packet):
        self.info = "%s\n" % (str(packet.summary()))
        self.counter += 1

    def update(self):
        sniff(iface=self.interface, filter='ip', prn=self.handle_pkts, stop_filter=lambda p: self.check)


