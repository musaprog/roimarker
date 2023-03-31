'''roimarker - A general purpose marker/annotation tool.
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
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector

from roimarker.arrow_selector import ArrowSelector


class Marker:
    '''Opens a matplotlib figure for annotating images.

    See also documentation at the __init__ method.

    Attributes
    ----------
    visible_rectangles : list
        Contains the matplotlib Rectangle-patches for the selected ROIs
        in the current image.
    '''
    
    def __init__(self, fig, ax, image_fns, markings_savefn, crops=None, clipping=True, old_markings=None,
            callback_on_exit=None, reselect_fns=None,
            relative_fns_from=None, drop_imagefn = False,
            selection_type='box'):
        '''
        Marking interests of region (ROIs) on images.

        After selecting the ROIs, a separate json file (markings_savefn) is created, which
        contains dictionary {image1_fn: [[ROI1, ROI2, ...]], ...}
            where ROI = [x,y,w,h]    (or [x1,y1,x2,y2] when selection_type='arrow')
        
        Arguments
        ---------
        fig, ax : objects
            What matplotlib plt.subplots() gives you
        image_fns : list of strings
            A list of image file names that are to be annotated
        markings_savefn : string
            Filename where the annotations are saved. If None do not save
        crops : sequence of 4 ints
            List where an item is crop[ [x,y,w,h] for each image.
            It is save to (accidentally) crop over the image coordinates.
        old_markings : string or dict or True
            Either filename to old markings (a string),
            loaded old markings (dict {fn: [x,y,w,h]}, ...),
            or True to load from markings_savefn.
        callback_on_exit : callable
            This gets called on successfull exit
        reslect_fns: list of strings
            List of image filenames should be remarked even if previous markings
            exist.
        relative_fns_from : string
            If a valid path, the saved markings contain relative filenames starting from
            this directory instead of the full, absolute filenames.
        drop_imagefn : bool
            Omits the image file name from the final markings dictionary.
            May be usefull if marking made for the image in the folder
            is to be used for all other images in the folder as well.
        selection_type : string
            'box' or 'arrow'
        '''
        
        self.fig = fig
        self.ax = ax
            
        self.fns = image_fns
        
        self.crops = crops

        self.current = None
        self.current_i = -1

        self.markings = {}
        self.N_previous = 0
        self.reselect_fns = reselect_fns
        
        if relative_fns_from is not None and not os.path.isdir(relative_fns_from):
            raise ValueError("relative_fns_from if set, has to be a proper a proper directory")

        self.relative_fns_from = relative_fns_from
        self.drop_imagefn = drop_imagefn

        self.clipping = clipping
        self.image_maxval = 1
        self.image_minval = 0 
        
        self.image = None
        self.previous_image_shape = None

        self.cid = self.fig.canvas.mpl_connect('key_press_event', self.__button_pressed)
        
        if selection_type == 'box':
            self.rectangle = RectangleSelector(ax, self._on_select_rectangle, useblit=True)
        elif selection_type == 'arrow':
            self.rectangle = ArrowSelector(ax, self._on_select_arrow)
        else:
            raise ValueError('Selection type for Marker has to be "box or "arrow", not {}'.format(selection_type))
        
        self.markings_savefn = markings_savefn
        
        if old_markings:
            if old_markings is True:
                self.load_markings(self.markings_savefn)
            elif type(old_markings) == type('string'):
                if os.path.isfile(old_markings):
                    self.load_markings(old_markings)
                else:
                    print("Warning! Couldn't import old_markings in Marker (marker.py)")
            elif type(old_markings) == type({}):
                print('Wrong oges')
                self.markings = old_marking
            elif type(old_markings) == type([]):
                raise NotImplementedError('Giving many old markings not yet implemented')
            else:
                raise TypeError('old_markings in incorrect type for Marker at marker.py')
            

            # If relative_fns_from is set, it is expected that for any previous
            # ROI selections, relative_fns_from was also set even if the directory may
            # have been different.
            # If this is not the case, previous data is not use but in the case of
            # platform (OS) jump problems arise for sure. FIXME?
            self.markings = {os.path.join(relative_fns_from, fn): rois for fn, rois in self.markings.items()
                    if not os.path.isabs(fn)}

        self.exit = False
        self.callback_on_exit = callback_on_exit
        self.fig.canvas.mpl_connect('close_event', lambda x: self.close())

        self.visible_rectangles = []


    def _get_relative_markings(self):
        '''
        Returns self.markings but with relative filesnames with rescpect to
        self.relative_fns_from if set. If not set, just returns self.markings
        '''

        if self.relative_fns_from:
            fns = {os.path.relpath(fn, start=self.relative_fns_from): rois for fn, rois in self.markings.items()}
        else:
            fns =  self.markings
        
        if self.drop_imagefn:
            fns = {os.path.dirname(fn): rois for fn, rois in fns.items()}
        
        return fns


    def run(self):
        '''
        Run the marking process where user selects ROIs for each given image.

        Returns self.markings that is a dictionary with image filenames as keys
        and ROIs as items.
        '''
        self.next_image()
        
        self.ax.text(0, 1.02, 'n: Next image\nx & z: Change brightness capping\nw: Save\nAutosave after the last image', transform=self.ax.transAxes,
                verticalalignment='bottom')
        
        plt.show(block=False)
        
        while self.exit == False:
            try:
                self.fig.canvas.start_event_loop(0.1)
            except:
                break
    
        plt.close(self.fig)   
        
        if self.current_i == len(self.fns):
            self.save_markings()
            tkinter.messagebox.showinfo('All images processed',
                    'Markings saved at\n{}'.format(self.markings_savefn))
        
        if self.callback_on_exit:
            self.callback_on_exit()
        
        return self._get_relative_markings()


    def __button_pressed(self, event):
        '''A callback funtion for matplotlib's event manager to handle buttons.
        '''
        key = event.key

        # Navigating between the images
        if key == 'n':
            self.next_image()
        elif key == 'w':
            self.save_markings()

        elif key == 'z':
            self.image_maxval -= 0.3
            self.update_image()
        elif key == 'x':
            self.image_maxval += 0.3
            self.update_image()
        elif key == 'c':
            self.image_minval -= 0.2
            self.update_image()
        elif key == 'v':
            self.image_minval += 0.2
            self.update_image()
        
        elif event.key == 'ctrl+z':
            if self.markings[self.current]:
                self.markings[self.current].pop(-1)

            if self.visible_rectangles:
                self.visible_rectangles.pop(-1).remove()
                plt.draw()


    def _on_select_rectangle(self, eclick, erelease):
        
        # Get selection box coordinates and set the box inactive
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        x = int(min((x1, x2)))
        y = int(min((y1, y2)))
        width = int(abs(x2-x1))
        height = int(abs(y2-y1))

        try:
            self.markings[self.current]
        except KeyError:
            self.markings[self.current] = []
        
        self.markings[self.current].append([x, y, width, height])
        
        # Add a static rectangle to show the made selection
        rectangle = Rectangle(
                (x,y), width, height,
                alpha=0.2)
        self.ax.add_patch(rectangle)
        self.visible_rectangles.append(rectangle)
        plt.draw()


    def _on_select_arrow(self, eclick, erelease):
        
        try:
            self.markings[self.current]
        except KeyError:
            self.markings[self.current] = []
        
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata       
        
        self.markings[self.current].append([x1, y1, x2, y2])

       

    def next_image(self):
        
        self.current_i += 1

        if self.current_i >= len(self.fns):
            self.exit = True    
            return 0

        for fn in self.fns[self.current_i:]:
            print(fn)
            if not fn in self.markings.keys() and self.reselect_fns is None:
                self.current = fn
                break

            if os.path.basename(os.path.dirname(fn)) in self.reselect_fns:
                self.current = fn
                break          
            self.current_i += 1
        
        if self.current_i >= len(self.fns):
            self.current_i == len(self.fns)
            self.exit = True
            return 0
        
        # Remove rectangle visible selections
        for patch in self.visible_rectangles:
            patch.remove()
        self.visible_rectangles = []

        # Set marking to empty
        self.markings[self.current] = []
       
        self.fig.suptitle(self.current, fontsize=8)

        print('Annotating image {}/{}'.format(self.current_i+1+self.N_previous, len(self.fns)+self.N_previous))
        print(self.current)
        if self.image is not None:
            self.previous_image_shape = self.image.shape
        
        try:
            self.image = tifffile.TiffFile(self.current).asarray(key=0).astype(np.float32)
        except ValueError as e:
            print('Old markings')
            raise ValueError('\n{}Cannot read file {}'.format(self.current))
        
        # If stack, take the first image
        if len(self.image.shape) == 3:
            self.image = self.image[0,:,:]
        
        self.image -= np.min(self.image)
        self.image /= np.max(self.image)
        self.update_image()


    def update_image(self):
        
        image = self.image

        if self.clipping:
            capvals = (np.mean(image) * self.image_minval, np.mean(image) *self.image_maxval)
            image = np.clip(image, *capvals) - capvals[0]
            image /= np.max(image)

        if image.shape == self.previous_image_shape:
            self.ax_imshow.set_data(image)
        else:
            self.ax_imshow = self.ax.imshow(image, cmap='gist_gray', interpolation='nearest', vmin=0, vmax=1) #extent=[0, image.shape[0], 0, image.shape[1]])
        
        if self.crops:
            c = self.crops[self.current_i]
            self.ax.set_xlim(c[0], c[0]+c[2])
            self.ax.set_ylim(c[1]+c[3], c[1])

        # If previous image shape not set at this point (opening the first image),
        # then use current shape as the previous also (othewise a bug that on the
        # first image setting brightess is slow and slows down the program
        # progressively)
        if self.previous_image_shape is None:
            self.previous_image_shape = self.image.shape

        plt.draw()
       
    
    def set_markings_savefn(self, fn):
        self.markings_savefn = fn


    def load_markings(self, fn):
        
        with open(fn, 'r') as fp:
            markings = json.load(fp)
        self.markings = markings


    def save_markings(self):
        '''
        Saves the markings as a json file
        '''
        if self.markings_savefn is None:
            return None

        with open(self.markings_savefn, 'w') as fp:
            json.dump(self._get_relative_markings(), fp)


    def get_markings(self):
        return self._get_relative_markings()


    def get_current_marking(self):
        return [self.current, self.markings[self.current][-1]]

    
    def close(self):
        self.exit = True
        

def main(): 
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
       

if __name__ == "__main__":
    main()

