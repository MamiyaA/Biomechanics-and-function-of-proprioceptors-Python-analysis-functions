# Biomechanics and function of proprioceptors: Python analysis class and functions

### Jupyter notebook containing python class and functions for analyzing calcium imaging and cell movement tracking data recorded from the leg of fruit flies.

## Brief description of the notebook/class/functions
---
### Manually_selecting_ROI_for_vibration_response_at_individual_z_level.ipynb:
**Jupyter notebook containing a class and scripts for manually selecting the ROI for the vibration responses at the individual z level**
* shows the example usage and the actual ROI selection for all the data in the paper.
* configured to run on the local computer instead of on google colab.
---
### Manually_selecting_the_most_right_and_left_club_dendritic_tips.ipynb:
**Jupyter notebook containing a class and scripts for manually selecting the most right and left dendritic tips of the club neurons**
* shows the example usage and the actual tip selection for all the data in the paper.
* configured to run on the local computer instead of on google colab.
---
### 20210712_python_class_for_preprocessing_two_photon_imaging_data.ipynb: 

**Python class for preprocessing two-photon imaging data and example usages**

* Read image files recorded by ScanImage and demultiplex the images into green and red channel.

* Filter images with gaussian filter (of specified kernel size).

* Subpixel image motion correcion using FFT.

* Use end-of-the-frame signals for two-photon images and IR high-speed camera images to synchronize the two imaging stream.

* Make a movie that shows two-photon images (both green and red channel) and IR high-speed camera images simultaneously for quick review.

* *This example Jupyter notebook is set to run on google colab using data on google drive.*

* *Parameters in the .yaml files are set for downstairs two-photon microscope.*
---
