
import collections

import matplotlib.patches


class ArrowSelector:
    '''
    Idea similar to matplotlib's RectangleSelector.
    '''

    def __init__(self, ax, callback, auto_connect=True):
        '''
        ax              Matlab axes intance
        callback        Gets eclick erelease, as in RectangleSelector
        auto_connect    Calls self.connect at initialization
        '''

        self.ax = ax
        self.callback = callback

        self.fig = ax.figure

        self.p0 = None
        self.p1 = None

        self.cid1 = None
        self.cid2 = None
        self.cid3 = None

        self.arrows = []
        
        if auto_connect:
            self.connect()



    def connect(self):
        '''
        Add ArrowSelector to the figure.

        Calls mpl_connect on self.fig.canvas 
        '''
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.cid2 = self.fig.canvas.mpl_connect('button_release_event', self._on_release)



    def disconnect():
        '''
        Does the opposite of connect, removes the rectangle selector
        from the figure.
        '''
        self.fig.canvas.mpl_disconnect(self.cid1)
        self.fig.canvas.mpl_disconnect(self.cid2)



    def _on_press(self, event):
        '''
        Called when pressing the figure with mouse.
        '''
        if event.inaxes == self.ax:
            self.p0 = (event.xdata, event.ydata)
            print(self.p0)

            # Set up updating the arrow
            self.cid3 = self.fig.canvas.mpl_connect('motion_notify_event', self._update_arrow)

        else:
            self.p0 = None



    def _clear_arrows(self):
        '''
        Remove any existing arrows from the figure
        '''
        if len(self.arrows) > 0:
            for arrow in self.arrows:
                arrow.remove()
            self.arrows = []
       


    def _update_arrow(self, event):
        '''
        Called when dragging the arrow around.
        '''
        if event.inaxes == self.ax:
            
            self._clear_arrows()
            
            # Arrow thickness
            width = 10

            dx = event.xdata - self.p0[0]
            dy = event.ydata - self.p0[1]
            arrow = matplotlib.patches.Arrow(*self.p0, dx, dy, width=width)
            
            # Add arrow to the figure
            self.ax.add_patch(arrow)
            self.arrows.append(arrow)

            self.fig.canvas.draw_idle()
        else:
            pass



    def _on_release(self, event):
        '''
        Called then releasing the mouse press.
        '''

        if self.cid3 is not None:
            self.fig.canvas.mpl_disconnect(self.cid3)
            self.cid3 = None

        if event.inaxes == self.ax and self.p0 is not None:
            self.p1 = (event.xdata, event.ydata)
            print(self.p1)
            
            # To roughly match RectangleSelector behaviour
            p0 = collections.namedtuple('eclick', ['xdata', 'ydata'])(self.p0[0], self.p0[1])
            p1 = collections.namedtuple('eclick', ['xdata', 'ydata'])(self.p1[0], self.p1[1])
            
            self._clear_arrows()

            self.callback(p0, p1)
        else:
            self.p0 = None
            self.p1 = None

