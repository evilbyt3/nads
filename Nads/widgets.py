import npyscreen


class PagerWidget(npyscreen.BoxTitle):
    '''
        A framed widget containing the scrolling through multiline text
    '''

    _contained_widget = npyscreen.Pager


class MultiLineWidget(npyscreen.BoxTitle):
    '''
        A framed widget containing multiline text
    '''
    _contained_widget = npyscreen.MultiLineEdit

