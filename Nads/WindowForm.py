import npyscreen
import os
import subprocess
import drawille
import ni_plugin
import thread_job
import math
import sys
from functools import partial
from widgets import *



PREVIOUS_TERMINAL_HEIGHT = 0
PREVIOUS_TERMINAL_WIDTH  = 0


ascii = '''
\t\t\t\t\t\t\t\t\t\t\t\t      __
\t\t\t\t\t\t\t\t\t\t\t\t    ('__`>        <-- OOL
\t\t\t\t\t\t\t\t\t\t\t\t    //"-(         ,   ~~~
\t\t\t\t\t\t\t\t\t\t\t\t    /:__/        /   ___________
\t\t\t\t\t\t\t\t\t\t\t\t   / /_/\       /____\__________)____________
\t\t\t\t\t\t\t\t\t\t\t\t  **/ ) \\     /                       \\  \ `.
\t\t\t\t\t\t\t\t\t\t\t\t    | |  \\  _J                        \\  \  |
\t\t\t\t\t\t\t\t\t\t\t\t    |  \_J,)|                          \\  \  ;
\t\t\t\t\t\t\t\t\t\t\t\t     \._/' `|_______________,------------+-+-'
\t\t\t\t\t\t\t\t\t\t\t\t      `.___.  \     ||| /                | |
\t\t\t\t\t\t\t\t\t\t\t\t     |_..__.'. \    |||/         OOL' BAND -->
'''



def daemons_cmd():
    xls = subprocess.Popen(["xlsclients"], stdout=subprocess.PIPE)
    cut = subprocess.Popen(["cut", "-f3", "-d "], stdin=xls.stdout, stdout=subprocess.PIPE)
    paste = subprocess.Popen(["paste", "-", "-s", "-d,"], stdin=cut.stdout, stdout=subprocess.PIPE)

    out, err = paste.communicate()
    out = out.split('\n')[0]

    cmd = subprocess.check_output(["ps -C " + out +" --ppid 2 --pid 2 --deselect -o user,group,pid,ppid,sess,lstart,etime,%cpu,%mem,rss,vsz,comm"], shell=True)
    return cmd.split('\n')



def network_services_cmd():
    cmd = subprocess.check_output(["sudo", "netstat", "-plantu"])
    return cmd.split('\n')



class WindowForm(npyscreen.FormBaseNew):
    '''
        Frameless Form
    '''

    def create(self, *args, **kwargs):
        super(WindowForm, self).create(*args, **kwargs)

        self.test = partial(self.switch)

        # Delay for calling while_waiting method
        self.keypress_timeout = 10

        # NI chart
        self.ni_array = None

        # Widgets
        self.daemons           = None
        self.network_services  = None
        self.image             = None
        self.network_interface = None
        self.actions           = None

        # Chart size
        self.CHART_WIDTH  = None
        self.CHART_HEIGHT = None

        self.add_handlers({
            "^Q" : self.exit,
            "^S" : self.test
        })

        self.draw()

    def switch(self, *args, **kwargs):
        self.parentApp.switchForm('NETWORK')


    def exit(self, *args, **kwargs):
        # Stop the threads and then exit
        self.parentApp.sensor.stop()
        self.parentApp.sniffer.stop()
        sys.exit(-1)



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



    def handle_command(self, value):
        if "kill -" in value:
            value = value.split('-')[1]
            self.command.entry_widget.value = value
            os.system("kill " + value)


    def draw_chart(self, canvas, y):
        chart_array = self.ni_array

        for i in range(self.CHART_WIDTH):
            if i >= 2:
                chart_array[i-2] = chart_array[i]

        chart_array[self.CHART_WIDTH-1] = y
        chart_array[self.CHART_WIDTH-2] = y

        for x in xrange(0, self.CHART_WIDTH):
            for y in xrange(self.CHART_HEIGHT, self.CHART_HEIGHT - chart_array[x], -1):
                canvas.set(x,y)

        return canvas.frame(0,0,self.CHART_WIDTH, self.CHART_HEIGHT)



    def draw(self):
        global PREVIOUS_TERMINAL_HEIGHT, PREVIOUS_TERMINAL_WIDTH, ascii

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


        # -=-=-=-=-=-=-=-=-=-=-={ DAEMONS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        DAEMONS_WIDGET_REL_X  = LEFT_OFFSET
        DAEMONS_WIDGET_REL_Y  = TOP_OFFSET

        DAEMONS_WIDGET_HEIGHT = int( 8*self.Y_SCALLING_FACTOR )
        DAEMONS_WIDGET_WIDTH  = int( 101.8*self.X_SCALLING_FACTOR )

        self.daemons = self.add(
            PagerWidget, name="-=-=-=-={ Daemons }=-=-=-=-",
            relx = DAEMONS_WIDGET_REL_X, rely = DAEMONS_WIDGET_REL_Y,
            max_width = DAEMONS_WIDGET_WIDTH, max_height = DAEMONS_WIDGET_HEIGHT
        )
        self.daemons.entry_widget.values        = []
        self.daemons.entry_widget.scroll_exit   = True
        self.daemons.entry_widget.editable      = True



        # -=-=-=-=-=-=-=-=-=-=-={ NETWORK SERVICES WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        NS_WIDGET_REL_X  = LEFT_OFFSET
        NS_WIDGET_REL_Y  = DAEMONS_WIDGET_REL_Y + DAEMONS_WIDGET_HEIGHT

        NS_WIDGET_HEIGHT = int(8*self.Y_SCALLING_FACTOR)
        NS_WIDGET_WIDTH  = int(101.8*self.X_SCALLING_FACTOR)


        self.network_services   = self.add(
            PagerWidget, name="-=-=-=-={ Network Services }=-=-=-=-",
            relx = NS_WIDGET_REL_X, rely = NS_WIDGET_REL_Y,
            max_width = NS_WIDGET_WIDTH, max_height = NS_WIDGET_HEIGHT
        )
        self.network_services.entry_widget.values       = []
        self.network_services.entry_widget.slow_scroll  = True
        self.network_services.entry_widget.scroll_exit  = True
        self.network_services.entry_widget.editable     = True



        # -=-=-=-=-=-=-=-=-=-=-={ NETWORK INTERFACE WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-

        NI_WIDGET_REL_X     = LEFT_OFFSET
        NI_WIDGET_REL_Y     = NS_WIDGET_REL_Y + NS_WIDGET_HEIGHT

        NI_WIDGET_HEIGHT    = int(6.5*self.Y_SCALLING_FACTOR)
        NI_WIDGET_WIDTH     = int(60*self.X_SCALLING_FACTOR)

        self.network_interface = self.add(
            MultiLineWidget, name = "-=-=-=-={ Network Traffic }=-=-=-=-",
            relx = NI_WIDGET_REL_X, rely = NI_WIDGET_REL_Y,
            max_width = NI_WIDGET_WIDTH, max_height = NI_WIDGET_HEIGHT
        )
        self.network_interface.value    = ""
        self.network_interface.entry_widget.editable = False


        # -=-=-=-=-=-=-=-=-=-=-={ IMAGE WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        IMAGE_WIDGET_REL_X  = NI_WIDGET_REL_X + NI_WIDGET_WIDTH
        IMAGE_WIDGET_REL_Y  = NI_WIDGET_REL_Y

        IMAGE_WIDGET_HEIGHT = int(6.5*self.Y_SCALLING_FACTOR)
        IMAGE_WIDGET_WIDTH  = int(40*self.X_SCALLING_FACTOR)

        self.image = self.add(
            npyscreen.MultiLine,
            relx = IMAGE_WIDGET_REL_X, rely = IMAGE_WIDGET_REL_Y,
            max_width = IMAGE_WIDGET_WIDTH, max_height = IMAGE_WIDGET_HEIGHT
        )
        ascii = ascii.split('\n')
        self.image.values   = [x for x in ascii]
        self.image.editable = False


        # -=-=-=-=-=-=-=-=-=-=-={ COMMAND WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        COMMAND_WIDGET_REL_X  = LEFT_OFFSET
        COMMAND_WIDGET_REL_Y  = IMAGE_WIDGET_REL_Y + IMAGE_WIDGET_HEIGHT

        COMMAND_WIDGET_HEIGHT = int(3.2*self.Y_SCALLING_FACTOR)
        COMMAND_WIDGET_WIDTH  = int(50.9*self.X_SCALLING_FACTOR)

        self.command = self.add(
            MultiLineWidget, name = "-=-=-=-={ Command handler}=-=-=-=-",
            relx = COMMAND_WIDGET_REL_X, rely = COMMAND_WIDGET_REL_Y,
            max_width = COMMAND_WIDGET_WIDTH, max_height = COMMAND_WIDGET_HEIGHT
        )
        self.command.entry_widget.editable  = True
        self.command.entry_widget.values    = []



        HELP_WIDGET_REL_X  = COMMAND_WIDGET_REL_X + COMMAND_WIDGET_WIDTH
        HELP_WIDGET_REL_Y  = COMMAND_WIDGET_REL_Y

        HELP_WIDGET_HEIGHT = int(3.2*self.Y_SCALLING_FACTOR)
        HELP_WIDGET_WIDTH  = int(50.9*self.X_SCALLING_FACTOR)

        self.help = self.add(
            PagerWidget, name = '-=-=-=-={ HELP }=-=-=-=-',
            relx = HELP_WIDGET_REL_X, rely= HELP_WIDGET_REL_Y,
            max_width = HELP_WIDGET_WIDTH, max_height = HELP_WIDGET_HEIGHT
        )
        self.help.values   = ["kill -{pid of program} " + "\t"*10 +"----> \t\t\t\tkills the specific pid"]
        self.help.editable = False



        # -=-=-=-=-=-=-=-=-=-=-={ ACTIONS WIDGET }=-=-=-=-=-=-=-=-=-=-=-=-=-


        ACTIONS_WIDGET_REL_X = LEFT_OFFSET
        ACTIONS_WIDGET_REL_Y = COMMAND_WIDGET_REL_Y + COMMAND_WIDGET_HEIGHT

        self.actions = self.add(
            npyscreen.FixedText,
            relx = ACTIONS_WIDGET_REL_X, rely = ACTIONS_WIDGET_REL_Y
        )
        self.actions.value = "\t\t^S:Switch To Network\t\tq: Switch Between Tabs\t\tg: Top\t\t^Q: Quit"
        self.actions.display()
        self.actions.editable = False


        # -=-=-=-=-=-=-=-=-=-=-={ NETWORK INTERFACE CHART }=-=-=-=-=-=-=-=-=-=-=-=-=-

        self.CHART_WIDTH  = int(math.floor(NI_WIDGET_WIDTH -2)*2)
        self.CHART_HEIGHT = int(math.floor(NI_WIDGET_HEIGHT-2)*4)
        self.ni_array     = [0]*self.CHART_WIDTH




    def update(self):
        # Daemons And Network Services Display
        self.daemons.entry_widget.values          = [str(x) for x in daemons_cmd()]
        self.daemons.entry_widget.update(clear=True)

        self.network_services.entry_widget.values = [str(x) for x in network_services_cmd()]
        self.network_services.entry_widget.update(clear=True)


        # Network Interface Display
        ni_canvas = drawille.Canvas()
        next_peak_height = int(math.ceil((float(self.parentApp.sensor.info['graph']['percentage'])/100)*self.CHART_HEIGHT))
        self.network_interface.value = self.draw_chart(ni_canvas, next_peak_height)
        self.network_interface.update(clear=True)

        # Command Widget Handler
        self.handle_command(self.command.entry_widget.value)

        self.DISPLAY()
