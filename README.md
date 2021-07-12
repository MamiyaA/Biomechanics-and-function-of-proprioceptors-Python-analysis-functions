# Biomechanics and function of proprioceptors: Python analysis class and functions

Jupyter notebook containing python class and functions for analyzing calcium imaging and cell movement tracking data recorded from the leg of fruit flies.

Brief description of the notebook/functions

## **Python class for preprocessing two-photon imaging data and example usages**

* Read image files recorded by ScanImage and demultiplex the images into green and red channel.

* Filter images with gaussian filter (of specified kernel size).

* Subpixel image motion correcion using FFT.

* Use end-of-the-frame signals for two-photon images and IR high-speed camera images to synchronize the two imaging stream.

* Make a movie that shows two-photon images (both green and red channel) and IR high-speed camera images simultaneously for quick review.



---
* *This example Jupyter notebook is set to run on google colab using data on google drive.*
* *Parameters in the .yaml files are set for downstairs two-photon microscope.*
