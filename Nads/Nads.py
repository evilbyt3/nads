import npyscreen
import thread_job
import ni_plugin
import sniffer
import argparse
import os
from NetworkForm import NetworkForm
from WindowForm  import WindowForm



THEMES = {
    'elegant'       : npyscreen.Themes.ElegantTheme,
    'colorful'      : npyscreen.Themes.ColorfulTheme,
    'simple'        : npyscreen.Themes.DefaultTheme,
    'dark'          : npyscreen.Themes.TransparentThemeDarkText,
    'light'         : npyscreen.Themes.TransparentThemeLightText,
    'blackonwhite'  : npyscreen.Themes.BlackOnWhiteTheme
}


class App(npyscreen.NPSAppManaged):

     def __init__(self, sensor, sniff, theme):
        super(npyscreen.NPSAppManaged, self).__init__()
        self._FORM_VISIT_LIST = []
        self.NEXT_ACTIVE_FORM = self.__class__.STARTING_FORM
        self._LAST_NEXT_ACTIVE_FORM = None
        self._Forms     = {}
        self.sensor     = sensor
        self.sniffer    = sniff
        self.theme      = theme


     def _get_theme(self):
        self.themes = THEMES
        return self.themes[self.theme]

     def onStart(self):
        npyscreen.setTheme(self._get_theme())
        self.addForm('MAIN'   , WindowForm , name = 'def')
        self.addForm('NETWORK', NetworkForm, name = 'net')



try:
    if os.getenv("USER") == 'root':

        parser = argparse.ArgumentParser()
        parser.add_argument('-t', '--theme', dest='theme', type=str, required=False,
        help=
        '''
            Valid thems are :
                elegant
                colorful
                dark
                light
                simple
                blackonwhite
        ''')
        parser.add_argument('-i', '--interface', dest='interface', type=str, required=True, help='Interface to display info about')
        args = parser.parse_args()
        if args.theme:
            theme = args.theme
        else:
            theme = 'elegant'
    
    
        # Start the threads
        stop_event = thread_job.threading.Event()
        sensor     = ni_plugin.NISensor(stop_event, args.interface)
        sniff      = sniffer.Sniffer(stop_event, args.interface)
        sensor.generate()
        sniff.generate()
    
    
        # Run the app
        A = App(sensor, sniff, theme)
        A.run()
    else:
        print("[!] You need to be root to run this script.")

except KeyboardInterrupt:
    # Stop the threads if a interrupt signal is catched
    sensor.stop()
    sniff.stop()
    raise SystemExit
