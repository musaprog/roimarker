# Roimarker

Annotates region of interest (ROI) using matplotlib
and Python.

- Draw rectangular ROIs with your mouse
- Quickly change to the next image by pressing *N*
- Adjust brightness/contrast with keys *Z*,*X*,*C*,*V*
- Undo with *Ctrl+Z*

## Installing

```
pip install roimarker
```

## Usage

### A) Standalone tool

```
python -m roimarker DIRECTORY
```

Here, replace DIRECTORY with the folder containing all the
image files to be annotated.

When finished, a *markings.json* file
is created to the current working directory
with the following structure:

```python
{fn1: [ROI_1, ROI_2, ROI_3, ..], fn2: [ROI_1, ...], ...}

where
	ROI_i = [x,y,w,h]
```

### B) In your programs

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
