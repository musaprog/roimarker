# Roimarker

A simple region of interest (ROI) creator using matplotlib to
annotate images with rectangular ROI.

**Warning**: Roimarker is still quite plain and unfinished.


## Installing

```
pip install roimarker
```

## Usage

Both (1) and (2) (below) launch the same interface, iterating
over the given images.

### 1) Standalone

```
python -m roimarker DIRECTORY
```

where DIRECTORY contains all the image files to annotate.
This saves *markings.json* file when finished (see below).


### 2) As part of your program

```python
import matplotlib.pyplot as plt
from roimarker import Marker

# Create matplotlib figure and ax
fig, ax = plt.subplots()

# List of images to annotate
image_fns = ['image1.tif', 'image2.tif', 'image3.tif']

marker = Marker(fig, ax, image_fns, 'markings.json')
marker.run()
```

This opens a window where the user can draw a number of rectangle
ROIs on the images. Pressing *n* advances to the next image,
and *z*, *x*, *c* and *v* can be used to adjust brightness/contrast.
After going through all the images or when manually pressing *w*,
a *markings.json* file in the current directory, containin
the ROIs in the following format

```python
{fn1: [ROI_1, ROI_2, ROI_3, ..], fn2: [ROI_1, ...], ...}

where
	ROI_i = [x,y,w,h]
```
