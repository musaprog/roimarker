'''
General purpose marker/annotation tool.
'''


import re
import os
import csv
import math
import sys
import json

import tifffile
import numpy as np
import tkinter.messagebox
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector


class Marker:
    
    def __init__(self, fig, ax, image_fns, markings_savefn, clipping=True, old_markings=None,
            callback_on_exit=None):
        '''
        fig, ax             plt.subplots() generated
        image_fns           A list of image file names that are to be annotated
        markings_savefn     Filename where the annotations are saved
        old_markings        A filename to old markings
        '''
        
        self.fig = fig
        self.ax = ax
            
        self.fns = image_fns

        self.current = None
        self.current_i = -1

        self.markings = {}
        self.N_previous = 0
        
        self.clipping = clipping
        self.image_maxval = 1
        
        self.cid = self.fig.canvas.mpl_connect('key_press_event', self.__buttonPressed)
        self.rectangle = RectangleSelector(ax, self.__onSelectRectangle, useblit=True)
               
        self.markings_savefn = markings_savefn
        
        if old_markings:
            if type(old_markings) == type('string'):
                if os.path.isfile(old_markings):
                    self.loadMarkings(old_markings)
                else:
                    print("Warning! Couldn't import old_markings in Marker (marker.py)")
            elif type(old_markings) == type({}):
                print('Wrong oges')
                self.markings = old_marking
            elif type(old_markings) == type([]):
                raise NotImplementedError('Giving many old markings not yet implemented')
            else:
                raise TypeError('old_markings in incorrect type for Marker at marker.py')
         
        self.exit = False
        self.callback_on_exit = callback_on_exit
        self.fig.canvas.mpl_connect('close_event', lambda x: self.close())

    def run(self):
        self.nextImage()
        #plt.show()
        
        self.ax.text(0, 1.02, 'n: Next image\nx & z: Change brightness capping\nw: Save\nAutosave after the last image', transform=self.ax.transAxes,
                verticalalignment='bottom')

        while self.exit == False:
            try:
                plt.pause(0.02)
            except:
                break
    
        plt.close(self.fig)   
        
        #plt.disconnect(self.cid)
        if self.current_i == len(self.fns):
            self.saveMarkings()
            tkinter.messagebox.showinfo('All images processed',
                    'Markings saved at\n{}'.format(self.markings_savefn))
        
        if self.callback_on_exit:
            self.callback_on_exit()

    def __buttonPressed(self, event):
        '''
        A callback function connecting to matplotlib's event manager.
        '''


        # Navigating between the images
        if event.key == 'n':
            self.nextImage()
        elif event.key == 'w':
            self.saveMarkings()

        elif event.key == 'z':
            self.image_maxval -= 0.3
            self.updateImage()
        elif event.key == 'x':
            self.image_maxval += 0.3
            self.updateImage()
        
        #elif event.key == 'c':
        #    os.remove(self.current)
        #    self.nextImage()

    def __onSelectRectangle(self, eclick, erelease):
        
        # Get selection box coordinates and set the box inactive
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        #self.rectangle.set_active(False)
        
        x = int(min((x1, x2)))
        y = int(min((y1, y2)))
        width = int(abs(x2-x1))
        height = int(abs(y2-y1))

        try:
            self.markings[self.current]
        except KeyError:
            self.markings[self.current] = []
        
        self.markings[self.current].append([x, y, width, height])



    def nextImage(self):
        
        self.current_i += 1

        if self.current_i == len(self.fns):
            #self.saveMarkings()
            #plt.close('all')
            self.exit = True    
            return 0
            #sys.exit(0)

        for fn in self.fns[self.current_i:]:

            if not fn in self.markings.keys():
                self.current = fn
                break

            self.current_i += 1
        
        print('Annotating image {}/{}'.format(self.current_i+1+self.N_previous, len(self.fns)+self.N_previous))
        print(self.current)
        try:
            self.image = tifffile.imread(self.current).astype(np.float32)
            print(self.image.shape)
        except ValueError:
            print('Old markings')
            raise ValueError('Cannot read file {}'.format(self.current))
        self.image -= np.min(self.image)
        #print((self.image))
        self.image /= np.max(self.image)
        self.updateImage()


    def updateImage(self):
        
        image = self.image

        if self.clipping:
            capvals = (0, np.mean(image) *self.image_maxval)
            image = np.clip(image, *capvals)
            image /= np.max(image)

            #self.ax.imshow(self.image,cmap='gist_gray', interpolation='nearest', vmin=capvals[0], vmax=capvals[1])
            
        #else:
        #    #self.ax.imshow(self.image,cmap='gist_gray', interpolation='nearest')
        
        try:
            self.ax_imshow.set_data(image)
        except AttributeError:
            self.ax_imshow = self.ax.imshow(image,cmap='gist_gray', interpolation='nearest', vmin=0, vmax=1)


        plt.draw()
        #plt.draw()
       
    
    def setMarkingsSaveFn(self, fn):
        self.markings_savefn = fn

    def loadMarkings(self, fn):
        
        with open(fn, 'r') as fp:
            markings = json.load(fp)
        
        self.markings = markings

    def saveMarkings(self):
        '''
        Saves the markings as a json file
        '''
        with open(self.markings_savefn, 'w') as fp:
            json.dump(self.markings, fp)
    
    def getMarkings(self):
        return self.markings

    def getCurrentMarking(self):
        return [self.current, self.markings[self.current][-1]]

    
    def close(self):
        
        self.exit = True
        
        

if __name__ == "__main__":
    '''
    Running marker as a tool directly from terminal / command line.
    '''
    
    for arg in sys.argv:
        if os.path.exists(arg):
            image_dir = arg
            continue
    
    image_fns = [os.path.join(image_dir, fn) for fn in os.listdir(image_dir)]
    markings_save_fn = "markings.json"

    fig, ax = plt.subplots()
    marker = Marker(fig, ax, image_fns, markings_save_fn)
    marker.run()

