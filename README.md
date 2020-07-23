# Biomechanics and function of proprioceptors: Python analysis functions

Jupyter notebook containing python functions for analyzing calcium imaging and cell movement tracking data recorded from the leg of fruit flies.

Brief description of the notebook/functions

Filter_ScanImage_tiff_files_average_fastZ.ipynb : Read in .tiff files acquired using the ScanImage (3D fast Z setting) and filter them using a gaussian 3D filter

make_video_with_filtered_tdTomato_signals.ipynb: Read in the tdTomato signal generated from the "Filter_ScanImage_tiff_files_average_fastZ.ipynb" mentioned above,and make a video overlaying raw tdTomato signal (representing cell position) with user specified threshold level. 

make_video_with_filtered_GCaMP_signals.ipynb: Python function for creating a video that shows the calcium activities of the cells during imaging. Uses OpenCV to create a video of GCaMP (calcium indicator) fluorescent images overlayed on top of the thresholded image.Read in the GCaMP signal generated from the "Filter_ScanImage_tiff_files_average_fastZ.ipynb" mentioned above.
