import npyscreen
import sys
import ni_plugin
import thread_job
import drawille
import math
import sniffer
import itertools
import subprocess as sub
from WindowForm import PREVIOUS_TERMINAL_HEIGHT, PREVIOUS_TERMINAL_WIDTH
from widgets import *
from functools import partial



def format_first(string, pad):
    try:
        TP = 45
        VP = TP - pad - len(string)

        if VP < 0:
            return str('\t'*pad + string + '\t'*VP)[:-(-VP)] + "|"

        else:
            return str('\t'*pad + string + '\t'*VP + '|')

    except Exception as e:
        raise e


def format_second(string, pad):
    return '\t'*pad + string + '\n'



class NetworkForm(npyscreen.FormBaseNew):

    def create(self, *args, **kwargs):
        super(NetworkForm, self).create(*args, **kwargs)

        self.test = partial(self.switch)

        # Widgets
        self.nii         = None         # Network interface widget

        # Helper variables for network interface widget
        self.nii_dict    = {"one" : " ", "two" : " "}
        self.nii_val     = [format_first('Info', 15) + format_second('Status', 20)]
        self.nii_dict    = {}
        self.key_counter = 0

        # Helper variables for connections widget
        self.connections = None
        self.conn_val    = [format_first('TCP', 15) + format_second('UDP', 20)]
        self.conn_dict   = {}

        # Packets Widgets
        self.packets_received    = None
        self.packets_sent        = None
        self.packets_dropped_in  = None
        self.packets_dropped_out = None

        # Sniff Widget
        self.sniff      = None
        self.sniff_val  = []

        # Delay for calling while_waiting method
        self.keypress_timeout = 10

        # Handlers for key input
        self.add_handlers({
            "^S" : self.test
        })

        # PKTS chart
        self.pkts_sent_array = None
        self.pkts_recv_array = None
        self.pkts_dropped_in_array  = None
        self.pkts_dropped_out_array = None

        # Chart size
        self.CHART_HEIGHT = None
        self.CHART_WIDTH  = None

        self.draw()


    def draw_chart(self, canvas, y, chart_type):
        if chart_type == 'sent':
            chart_array = self.pkts_sent_array
        elif chart_type == 'receive':
            chart_array = self.pkts_recv_array
        elif chart_type == 'drop_in':
            chart_array = self.pkts_dropped_in_array
        else:
            chart_array = self.pkts_dropped_out_array

        for i in range(self.CHART_WIDTH):
            if i >= 2:
                chart_array[i-2] = chart_array[i]

        chart_array[self.CHART_WIDTH-1] = y
        chart_array[self.CHART_WIDTH-2] = y

        for x in xrange(0, self.CHART_WIDTH):
            for y in xrange(self.CHART_HEIGHT, self.CHART_HEIGHT - chart_array[x], -1):
                canvas.set(x,y)

        return canvas.frame(0,0,self.CHART_WIDTH, self.CHART_HEIGHT)





    def switch(self, *args, **keywords):
        self.parentApp.switchForm('MAIN')


    def while_waiting(self):
        terminal_width, terminal_height = drawille.getTerminalSize()

        # If the terminal height or width changes redraw and update the window
        if terminal_width != PREVIOUS_TERMINAL_WIDTH or terminal_height != PREVIOUS_TERMINAL_HEIGHT:
            self.erase()
            self.draw()
            self.update()
        # Else just update
        else:
            self.update()


    def draw(self):
        global PREVIOUS_TERMINAL_HEIGHT, PREVIOUS_TERMINAL_WIDTH

        # Setting the terminal dimension
        max_y, max_x = self.curses_pad.getmaxyx()
        PREVIOUS_TERMINAL_HEIGHT = max_y
        PREVIOUS_TERMINAL_WIDTH  = max_x

        # Minimun terminal size is used for scalling
        self.Y_SCALLING_FACTOR = float(max_y)/27
        self.X_SCALLING_FACTOR = float(max_x)/104

        # Defaults
        LEFT_OFFSET = 1
        TOP_OFFSET  = 1


        # -=-=-=-=-=-=-=-=-=-=-={ NETWORK INTERFACES INFO WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        NII_WIDGET_REL_X  = LEFT_OFFSET
        NII_WIDGET_REL_Y  = TOP_OFFSET

        NII_WIDGET_WIDTH  = int(50*self.X_SCALLING_FACTOR)
        NII_WIDGET_HEIGHT = int(12*self.Y_SCALLING_FACTOR)

        self.nii = self.add(
            PagerWidget, name = "-=-=-=-={ Interfaces Info }=-=-=-=-",
            relx = NII_WIDGET_REL_X, rely = NII_WIDGET_REL_Y,
            max_width = NII_WIDGET_WIDTH, max_height = NII_WIDGET_HEIGHT
        )
        self.nii.entry_widget.values          = []
        self.nii.entry_widget.editable        = True
        self.nii.entry_widget.scroll_exit     = True


        # -=-=-=-=-=-=-=-=-=-=-={ CONNECTIONS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-

        CONN_WIDGET_REL_X  = NII_WIDGET_REL_X + NII_WIDGET_WIDTH
        CONN_WIDGET_REL_Y  = TOP_OFFSET

        CONN_WIDGET_WIDTH  = int(50*self.X_SCALLING_FACTOR)
        CONN_WIDGET_HEIGHT = int(12*self.Y_SCALLING_FACTOR)

        self.connections = self.add(
            PagerWidget, name = "-=-=-=-={ Connections }=-=-=-=-",
            relx = CONN_WIDGET_REL_X, rely = CONN_WIDGET_REL_Y,
            max_width = CONN_WIDGET_WIDTH, max_height = CONN_WIDGET_HEIGHT
        )
        self.connections.entry_widget.values      = []
        self.connections.entry_widget.editable    = True
        self.connections.entry_widget.scroll_exit = True

        # -=-=-=-=-=-=-=-=-=-=-={ PACKETS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=


        # Packets Received
        PKTS_WIDGET_REL_X  = LEFT_OFFSET
        PKTS_WIDGET_REL_Y  = CONN_WIDGET_REL_Y + CONN_WIDGET_HEIGHT

        PKTS_WIDGET_WIDTH  = int(25*self.X_SCALLING_FACTOR)
        PKTS_WIDGET_HEIGHT = int(5*self.Y_SCALLING_FACTOR)

        self.packets_received = self.add(
            MultiLineWidget, name = "-=-=-=-={ Packets Received }=-=-=-=-",
            relx = PKTS_WIDGET_REL_X, rely = PKTS_WIDGET_REL_Y,
            max_width = PKTS_WIDGET_WIDTH, max_height = PKTS_WIDGET_HEIGHT
        )
        self.packets_received.values   = []
        self.packets_received.editable = False


        # Packets Sent
        PKTS1_WIDGET_REL_X  = PKTS_WIDGET_REL_X + PKTS_WIDGET_WIDTH
        PKTS1_WIDGET_REL_Y  = CONN_WIDGET_REL_Y + CONN_WIDGET_HEIGHT

        PKTS1_WIDGET_WIDTH  = int(25*self.X_SCALLING_FACTOR)
        PKTS1_WIDGET_HEIGHT = int(5*self.Y_SCALLING_FACTOR)

        self.packets_sent = self.add(
            MultiLineWidget, name = "-=-=-=-={ Packets Sent }=-=-=-=-",
            relx = PKTS1_WIDGET_REL_X, rely = PKTS1_WIDGET_REL_Y,
            max_width = PKTS1_WIDGET_WIDTH, max_height = PKTS1_WIDGET_HEIGHT
        )
        self.packets_sent.values   = []
        self.packets_sent.editable = False

        # Incoming Packets Dropped
        PKTS2_WIDGET_REL_X  = LEFT_OFFSET
        PKTS2_WIDGET_REL_Y  = PKTS1_WIDGET_REL_Y + PKTS1_WIDGET_HEIGHT

        PKTS2_WIDGET_WIDTH  = int(25*self.X_SCALLING_FACTOR)
        PKTS2_WIDGET_HEIGHT = int(5*self.Y_SCALLING_FACTOR)

        self.packets_dropped_in = self.add(
            MultiLineWidget, name = "-=-=-=-={ Incoming Packets Dropped }=-=-=-=-",
            relx = PKTS2_WIDGET_REL_X, rely = PKTS2_WIDGET_REL_Y,
            max_width = PKTS2_WIDGET_WIDTH, max_height = PKTS2_WIDGET_HEIGHT
        )
        self.packets_dropped_in.values   = []
        self.packets_dropped_in.editable = False


        # Outgoing Packets Dropped
        PKTS3_WIDGET_REL_X  = PKTS2_WIDGET_REL_X + PKTS2_WIDGET_WIDTH
        PKTS3_WIDGET_REL_Y  = PKTS2_WIDGET_REL_Y

        PKTS3_WIDGET_WIDTH  = int(25*self.X_SCALLING_FACTOR)
        PKTS3_WIDGET_HEIGHT = int(5*self.Y_SCALLING_FACTOR)

        self.packets_dropped_out = self.add(
            MultiLineWidget, name = "-=-=-=-={ Outgoing Packets Dropped }=-=-=-=-",
            relx = PKTS3_WIDGET_REL_X, rely = PKTS3_WIDGET_REL_Y,
            max_width = PKTS3_WIDGET_WIDTH, max_height = PKTS3_WIDGET_HEIGHT
        )
        self.packets_dropped_out.values   = []
        self.packets_dropped_out.editable = False




        # -=-=-=-=-=-=-=-=-=-=-={ SNIFF WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=


        TCPD_WIDGET_REL_X  = PKTS1_WIDGET_REL_X + PKTS1_WIDGET_WIDTH
        TCPD_WIDGET_REL_Y  = PKTS1_WIDGET_REL_Y

        TCPD_WIDGET_WIDTH  = int(50*self.X_SCALLING_FACTOR)
        TCPD_WIDGET_HEIGHT = int(10*self.Y_SCALLING_FACTOR)

        self.sniff = self.add(
            PagerWidget, name = "-=-=-=-={ Sniffer }=-=-=-=-",
            relx = TCPD_WIDGET_REL_X, rely = TCPD_WIDGET_REL_Y,
            max_width = TCPD_WIDGET_WIDTH, max_height = TCPD_WIDGET_HEIGHT
        )
        self.sniff.entry_widget.values   = []
        self.sniff.entry_widget.editable = False


        # -=-=-=-=-=-=-=-=-=-=-={ ACTIONS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        ACTIONS_WIDGET_REL_X = LEFT_OFFSET
        ACTIONS_WIDGET_REL_Y = TCPD_WIDGET_REL_Y + TCPD_WIDGET_HEIGHT + 8

        self.actions = self.add(
            npyscreen.FixedText,
            relx = ACTIONS_WIDGET_REL_X, rely = ACTIONS_WIDGET_REL_Y
        )
        self.actions.value = "\t\t^S:Switch To Main\t\tg:Top\t\tq:Switch Between Tabs"        #\t\tARP_WATCH\t\tTOR_ROUTING"
        self.actions.display()
        self.actions.editable = False


        # -=-=-=-=-=-=-=-=-=-=-={ PACKETS WIDGETS CHART }=-=-=-=-=-=-=-=-=-=-=-=-=-

        self.CHART_WIDTH  = int(math.floor(PKTS_WIDGET_WIDTH  -2)*2)
        self.CHART_HEIGHT = int(math.floor(PKTS_WIDGET_HEIGHT -2)*4)
        self.pkts_sent_array   = [0]*self.CHART_WIDTH
        self.pkts_recv_array   = [0]*self.CHART_WIDTH
        self.pkts_dropped_in_array    = [0]*self.CHART_WIDTH
        self.pkts_dropped_out_array   = [0]*self.CHART_WIDTH





    def update(self):


        # -=-=-=-=-=-=-=-=-=-=-={ NETWORK INTERFACE WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-

        # Store the sensors info and stats in 2 dictionaries
        self.nii_dict['one'] = self.parentApp.sensor.info['interfaces']['info']
        self.nii_dict['two'] = self.parentApp.sensor.info['interfaces']['stats']

        # Upload the formated result to the network interface value
        if self.key_counter == 0:
            for (key1, value1), (key2, value2) in zip( self.nii_dict['one'].items(), self.nii_dict['two'].items() ):
                self.nii_val.append( format_first(str(key1)+':', 1) + format_second(str(key2)+':', 3) )
                for v1 in value1:
                    self.nii_val.append( format_first("address   : "+str(v1.address)   , 5) + format_second('isup   :'+str(value2.isup)    , 7) )
                    self.nii_val.append( format_first("broadcast : "+str(v1.broadcast) , 5) + format_second('duplex :'+ str(value2.duplex) , 7) )
                    self.nii_val.append( format_first("family    : "+str(v1.family)    , 5) + format_second('speed  :'+ str(value2.speed)  , 7) )
                    self.nii_val.append( format_first("netmask   : "+str(v1.netmask)   , 5) + format_second('mtu    :'+str(value2.mtu)     , 7) )
                self.key_counter += 1
        self.nii.entry_widget.values = [x for x in self.nii_val]     # Set the widgets values to the formated result


        # -=-=-=-=-=-=-=-=-=-=-={ CONNECTIONS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-

        # Store the sensors tcp and udp connections in 2 dictionaries
        self.conn_dict['one'] = self.parentApp.sensor.info['conn']['tcp']
        self.conn_dict['two'] = self.parentApp.sensor.info['conn']['udp']
        k = 1

        # Upload the formated result to the connections value
        if self.key_counter == 4:
            for tcp, udp in zip(self.conn_dict['one'], self.conn_dict['two']):
                self.conn_val.append( format_first("Connection " + str(k), 1) )
                self.conn_val.append( format_first("fd          : " + str(tcp.fd)      , 5) + format_second("fd          : " + str(udp.fd)     , 7) )
                self.conn_val.append( format_first("family      : " + str(tcp.family)  , 5) + format_second("family      : " + str(udp.family) , 7) )
                self.conn_val.append( format_first("type        : " + str(tcp.type)    , 5) + format_second("type        : " + str(udp.type)   , 7) )
                self.conn_val.append( format_first("local_addr  : " + str(tcp.laddr[0]) + ":" + str(tcp.laddr[1])      , 5) + format_second("local_addr  : " + str(udp.laddr[0]) + ":" + str(udp.laddr[1]) , 7) )
                if tcp.raddr == () and udp.raddr == ():
                    self.conn_val.append( format_first("remote_addr : " + str(tcp.raddr), 5) + format_second("remote_addr : " + str(udp.raddr) , 5) )
                else:
                    if tcp.raddr == ():
                        self.conn_val.append( format_first("remote_addr : " + str(tcp.raddr), 5) + format_second("remote_addr : " + str(udp.raddr[0] + str(udp.raddr[1])) , 5) )
                    if udp.raddr == ():
                        self.conn_val.append( format_first("remote_addr : " + str(tcp.raddr[0] + str(tcp.raddr[1])), 5) + format_second("remote_addr : " + str(udp.raddr) , 5) )
                self.conn_val.append( format_first("status      : " + str(tcp.status)   , 5) + format_second("status      : " + str(udp.status), 7) )
                self.key_counter += 1
                k += 1
        self.connections.entry_widget.values = [x for x in self.conn_val]       # Set the widgets values to the formated result


        # -=-=-=-=-=-=-=-=-=-=-={ PACKETS WIDGETS }=-=-=-=-=-=-=-=-=-=-=-=-=-


        # Packets Sent
        pkts_sent_canvas  = drawille.Canvas()
        next_peak_height  = int(math.ceil((float(self.parentApp.sensor.info['graph']['sent'])/100)*self.CHART_HEIGHT))
        self.packets_sent.value = self.draw_chart(pkts_sent_canvas, next_peak_height, 'sent')
        self.packets_sent.update(clear=True)


        # Packets Received
        pkts_recv_canvas  = drawille.Canvas()
        next_peak_height  = int(math.ceil((float(self.parentApp.sensor.info['graph']['received'])/100)*self.CHART_HEIGHT))
        self.packets_received.value = self.draw_chart(pkts_recv_canvas, next_peak_height, 'received')
        self.packets_received.update(clear=True)


        # Packets Dropped In
        pkts_drop_in_canvas  = drawille.Canvas()
        next_peak_height  = int(math.ceil((float(self.parentApp.sensor.info['graph']['drop_in'])/100)*self.CHART_HEIGHT))
        self.packets_dropped_in.value = self.draw_chart(pkts_drop_in_canvas, next_peak_height, 'drop_in')
        self.packets_dropped_in.update(clear=True)


        # Packets Dropped Out
        pkts_drop_out_canvas  = drawille.Canvas()
        next_peak_height  = int(math.ceil((float(self.parentApp.sensor.info['graph']['drop_out'])/100)*self.CHART_HEIGHT))
        self.packets_dropped_out.value = self.draw_chart(pkts_drop_out_canvas, next_peak_height, 'drop_out')
        self.packets_dropped_out.update(clear=True)


        # -=-=-=-=-=-=-=-=-=-=-={ SNIFF WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-

        # If a new packet needs to be displayed, display it
        if ( self.parentApp.sniffer.counter - len(self.sniff_val) ) > 0:
            self.sniff_val.append(str(self.parentApp.sniffer.info))
            self.sniff.entry_widget.values = [x for x in self.sniff_val]

        # If the max packets displayed on the widget are touched, reset everything
        if self.parentApp.sniffer.counter > 30:
            self.sniff_val = []
            self.sniff.entry_widget.values = []
            self.parentApp.sniffer.counter = 0

        self.DISPLAY()
