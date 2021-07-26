
"""### A python class for preprocessing two-photon images and calculate response maps for piezo stimuli

* **filter_ScanImageFile_separate_z**: load ScanImage file, demultiplex the data into green and red channel, demultiplex into each z-level, filter images with gaussian filter.

* **motion_correction_separate_z**: correct for motion artifact at subpixel resolution using FFT. Correct motion at each z-level.

* **detect_camera_imaging_frames2**: use frame signals and mirror signals recorded for the two-photon image and IR high-speed camera to synchronize the two imaging streams.

* **make_synchronized_video_gray**: make a video that shows two-photon images (both green and red channel) and IR high-speed camera images simultaneously for a quick review of the data.

* **make_synchronized_video_gray_piezo**: same as above, but for piezo experiments (does not have IR high-speed camera images).

* parameters are set in .yaml file

"""

#Import packages
from ScanImageTiffReader import ScanImageTiffReader
import numpy as np
import os
import fnmatch
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, median_filter
import pickle
import scipy.signal
import re
import pandas as pd
import seaborn as sns
import cv2
import yaml

from skimage import data
from skimage.registration import phase_cross_correlation
from skimage.registration._phase_cross_correlation import _upsampled_dft
from scipy.ndimage import fourier_shift

# Define a class "LegVibration_separate_z" for analyzing two-photon calcium imaging data in response to the
#vibration stimuli (high frequency vibration with Piezo).
#Includes, preprocessing (demulitplexing, filtering, motion-correction),
#making exaple video (synchronizing video images with two-photon images by detecting frame signals),
# and generating response maps (detecting frames where vibration stimuli occured and making DF/F and DR/R maps).
#This class will keep all z-levels separate until the end where we make the DR/R and DF/F.

class LegVibration_separate_z:
  """
  This class initializes a LegVibration_separate_z objects with attributes: data_file_path, frame_signal_filepath,
  config_filepath, etc (all parameters are included in the config.yaml configuration file)
  and methods: filter_ScanImageFile_separate_z, motion_correction_separate_z, detect_camera_imaging_frames2,
  detect_piezo_start_frames, make_synchronized_video_gray_piezo, get_piezo_response_map_separate_z,
  and merge_piezo_response_map
  """
  def __init__(self,data_filepath,frame_signal_filepath,config_filepath):

    with open(config_filepath, "r") as file:
            config = yaml.safe_load(file) # read from config.yaml

    self.gaussian_sigma = config[0]['gaussian_filter']
    self.number_of_channels = config[0]['number_of_channels']
    self.camera_channel = config[0]['camera_channel']
    self.imaging_channel = config[0]['imaging_channel']
    self.piezo_channel = config[0]['piezo_channel']
    self.c_height = config[0]['c_height']
    self.c_width = config[0]['c_width']
    self.c_distance = config[0]['c_distance']
    self.i_height = config[0]['i_height']
    self.i_width = config[0]['i_width']
    self.i_distance = config[0]['i_distance']
    self.window_width = config[0]['window_width']
    self.skip_interval = config[0]['skip_interval']

    self.n_of_z = config[0]['n_of_z']
    self.frames_per_second = config[0]['frames_per_second']
    self.min_range1 = config[0]['min_range1']
    self.max_range1 = config[0]['max_range1']
    self.min_range2 = config[0]['min_range2']
    self.max_range2 = config[0]['max_range2']
    self.min_range3 = config[0]['min_range3']
    self.max_range3 = config[0]['max_range3']
    self.gcamp_threshold = config[0]['gcamp_threshold']
    self.tdTomato_threshold = config[0]['tdTomato_threshold']
    self.ratio_threshold = config[0]['ratio_threshold']
    self.response_range = config[0]['response_range']
    self.base_range = config[0]['base_range']

    self.upsample = config[0]['upsample']
    self.registration_channel = config[0]['registration_channel']

    self.data_filepath = data_filepath
    self.frame_signal_filepath = frame_signal_filepath
    self.gcamp_filtered_path = None
    self.tdTomato_filtered_path = None
    self.gcamp_registered_path = None
    self.tdTomato_registered_path = None
    self.frame_data_path = None
    self.piezo_data_path = None
    self.map_data_path = None
    self.merged_path = None


  def filter_ScanImageFile_separate_z(self):
    """
    This method loads the image generated by scanImage, demultiplex it into
    green and red channels, divide into each z-level, and gaussian filter it
    with the specified gamma. This method will keep all z-levels separate rather
    than collapsing them together.
    Recommended gauusian gamma [0, 5, 5] for single Z recording with upstairs 2P.
    [3, 5, 5] for single Z downstairs 2P.
    [1, 5, 5] for fast-Z recordings?
    """
    #
    file_name=self.data_filepath
    gaussian_sigma_array=self.gaussian_sigma
    n_of_z=self.n_of_z

    #Load the image using ScanImageTiffReader
    TimeSeries=ScanImageTiffReader(file_name).data()
    #Close the file
    ScanImageTiffReader(file_name).close()

    #Currently the images are multiplexed so NofFrames*NoChannels*n_of_z
    #is the first dimension.

    #We first split into two channels because we know they all have two channels
    #for the 1st channel (start with 1 and take every other frame)
    Channel_1_Index=np.arange(0, TimeSeries.shape[0],2)
    Channel_2_Index=np.arange(1,TimeSeries.shape[0],2)

    #assuming GCaMP is channel 1 and tdT is channel 2
    #This is true for all downstairs experiments

    GCaMPSignal=TimeSeries[Channel_1_Index]
    tdTomatoSignal=TimeSeries[Channel_2_Index]
    del TimeSeries

    #Split into different z-levels and apply 3D gaussian filter
    #First for the GCaMP signal.
    depth_avg_image_GCaMP=np.zeros((n_of_z,GCaMPSignal.shape[0]//n_of_z,GCaMPSignal.shape[1],GCaMPSignal.shape[2]))

    for depth in range(n_of_z):
        depthIndex=np.arange(depth,GCaMPSignal.shape[0],n_of_z)
        depth_avg_image_GCaMP[depth,:,:,:] = gaussian_filter(GCaMPSignal[depthIndex], sigma=gaussian_sigma_array)

    #save the depth_avg_image
    image_file_name=file_name.split('.')
    GCaMP_name=(image_file_name[0]+"GCaMP_Filtered_Zs")
    print(GCaMP_name)
    with open(GCaMP_name, "wb") as f:
      pickle.dump(depth_avg_image_GCaMP,f)
    del depth_avg_image_GCaMP

    #Do the same for the tdTomato signal.
    depth_avg_image_tdTomato=np.zeros((n_of_z,tdTomatoSignal.shape[0]//n_of_z,tdTomatoSignal.shape[1],tdTomatoSignal.shape[2]))

    for depth in range(n_of_z):
        depthIndex=np.arange(depth,tdTomatoSignal.shape[0],n_of_z)
        depth_avg_image_tdTomato[depth,:,:,:] = gaussian_filter(tdTomatoSignal[depthIndex], sigma=gaussian_sigma_array)

    #save the depth_avg_image
    image_file_name=file_name.split('.')
    tdTomato_name=(image_file_name[0]+"tdTomato_Filtered_Zs")
    print(tdTomato_name)
    with open(tdTomato_name, "wb") as f:
      pickle.dump(depth_avg_image_tdTomato,f)
    del depth_avg_image_tdTomato

    self.gcamp_filtered_path = GCaMP_name
    self.tdTomato_filtered_path = tdTomato_name

    return self.gcamp_filtered_path, self.tdTomato_filtered_path

  def motion_correction_separate_z(self):

    """
    This method loads the filtered image data, and register
    individual images to the average image. Use subpixel registration algorithm
    that uses FFT. Use the registration_channel to register images. Use the same
    shift for both channels in the two-photon images.
    """
    registration_channel=self.registration_channel
    gcamp_filtered_path = self.gcamp_filtered_path
    tdTomato_filtered_path = self.tdTomato_filtered_path
    upsample = self.upsample
    n_of_z = self.n_of_z

    #This version keeps each z level separate and register each one.
    ### For now use the average of gaussian filtered data to register the images.
    #use the registration channel to correct for motion.
    #apply the same shift to the other channel.

    #Get filtered images for registration channel
    if registration_channel==1:
      #use gcamp signal to register
      with open(gcamp_filtered_path, "rb") as f:
        filtered_images=pickle.load(f)
      #load the tdTomato signal as well
      with open(tdTomato_filtered_path, "rb") as f:
        filtered_images2=pickle.load(f)
    else:
      #use tdTomato signal to register
      with open(tdTomato_filtered_path, "rb") as f:
        filtered_images=pickle.load(f)
      #load the gcamp signal as well
      with open(gcamp_filtered_path, "rb") as f:
        filtered_images2=pickle.load(f)

    #filtered_images is np array with [n_of_z, frames, rows, columns]
    n_of_frames=filtered_images.shape[1]

    #initialize an array with the same size and data type as filtered images
    registered_images=np.zeros_like(filtered_images)
    registered_images2=np.zeros_like(filtered_images2)

    #run motion correction for each z-level.
    for z_level in range(n_of_z):
      #make an average image to register to.
      average_image=np.mean(filtered_images[z_level,:,:,:],axis=0)

      for frame in range(n_of_frames):

        # subpixel precision
        shift, error, diffphase = phase_cross_correlation(average_image, filtered_images[z_level,frame,:,:],upsample_factor=upsample)
        #correct for the movement
        new_image = fourier_shift(np.fft.fftn(filtered_images[z_level,frame,:,:]), shift)
        new_image2 = fourier_shift(np.fft.fftn(filtered_images2[z_level,frame,:,:]), shift)
        new_image = np.fft.ifftn(new_image)
        new_image2 = np.fft.ifftn(new_image2)
        new_image = new_image.real
        new_image2 = new_image2.real
        registered_images[z_level,frame,:,:]=new_image
        registered_images2[z_level,frame,:,:]=new_image2

    #Save the registered images
    if registration_channel==1:

      #we used gcamp signal to register.
      outfile_name=(gcamp_filtered_path+"_registered_Zs")
      print(outfile_name)
      with open(outfile_name, "wb") as f:
        pickle.dump(registered_images,f)
      self.gcamp_registered_path = outfile_name
      #Also save tdTomato signals
      outfile_name=(tdTomato_filtered_path+"_registered_Zs")
      print(outfile_name)
      with open(outfile_name, "wb") as f:
        pickle.dump(registered_images2,f)
      self.tdTomato_registered_path = outfile_name

    else:
      #we used tdTomato signal to register.
      outfile_name=(tdTomato_filtered_path+"_registered_Zs")
      print(outfile_name)
      with open(outfile_name, "wb") as f:
        pickle.dump(registered_images,f)
      self.tdTomato_registered_path = outfile_name
      #Also save gcamp signals
      outfile_name=(gcamp_filtered_path+"_registered_Zs")
      print(outfile_name)
      with open(outfile_name, "wb") as f:
        pickle.dump(registered_images2,f)
      self.gcamp_registered_path = outfile_name



    return self.gcamp_registered_path, self.tdTomato_registered_path


  def detect_camera_imaging_frames2(self):
    """
    a method for finding the match between the imaging frame and the camera frames.

    * each object should have the path to the frame info file.
    * number_of_channels: number of channels in the data. Should be 7.
    * camera_channel: the channel that contains the camera exposure signal. Should be channel 1 (2nd channel).
    * imaging_channel: the channel that contains the imaging frame signal. Should be channel 2 (3rd channel).
    * c_height, c_width, c_distance: parameters for detecting camera signal with scipy.signal.findpeaks
    * i_height, i_width, i_distance: same for the imaging frames.
    * window_width: window to average the frame signals (necessary if sampling rate is too high). Should be 10.
    """
    input_file=self.frame_signal_filepath

    number_of_channels=self.number_of_channels
    camera_channel=self.camera_channel
    imaging_channel = self.imaging_channel
    c_height = self.c_height
    c_width = self.c_width
    c_distance = self.c_distance
    i_height = self.i_height
    i_width = self.i_width
    i_distance = self.i_distance
    window_width = self.window_width


    #read the binary file.
    frame_data=np.fromfile(input_file)

    #Check the number of data points
    number_of_data=frame_data.shape[0]

    #Get the camera exposure signal
    camera_frame_signal_index=np.arange(camera_channel,number_of_data,number_of_channels)
    camera_frame_signal=frame_data[camera_frame_signal_index]

    #Get the image frame signal
    image_frame_signal_index=np.arange(imaging_channel,number_of_data,number_of_channels)
    image_frame_signal=frame_data[image_frame_signal_index]
    #Convolve the image_frame_signal
    image_frame_signal=np.convolve(image_frame_signal,np.ones((window_width,))/window_width, mode='valid')


    #See how the camera signal changes and find the peaks
    camera_diff=np.diff(camera_frame_signal)
    #Use scipy.signal.find_peaks to get the peaks in the diff data.
    peaks_camera, _ =scipy.signal.find_peaks(camera_diff,height=c_height, width=c_width, distance=c_distance)

    #Do the same for the imaging signal
    image_diff=np.diff(image_frame_signal)
    #Use scipy.signal.find_peaks to get the peaks in the diff data.
    peaks_image, _ =scipy.signal.find_peaks(image_diff,height=i_height, width=i_width, distance=i_distance)

    #plot to camera and frame interval to check the detection.
    camera_interval=np.diff(peaks_camera)
    plt.figure(figsize=(10,3))
    plt.plot(camera_interval)
    sns.despine()

    image_interval=np.diff(peaks_image)
    plt.figure(figsize=(10,3))
    plt.plot(image_interval)
    sns.despine()

    #Go through each imaging frame and find the camera frame with the closest index
    #This camera frame will be closest to the beginning of the image acquisition.
    image_in_camera_index=np.zeros((peaks_image.shape[0],1), dtype=np.int)

    #keep track of how far away the camera signal was relative to the imaging signal.
    camera_minus_image_index=np.zeros((peaks_image.shape[0],1), dtype=np.int)

    for n in range(peaks_image.shape[0]):
        #take the absolute difference in the index between the image acquisition and all camera images
        time_to_camera=np.absolute(peaks_camera-peaks_image[n])
        #Find the camera image that is closest (frame number)
        image_in_camera_index[n]=np.argmin(time_to_camera)
        #find the time between the image peak and the closest camera peak. positive indicates that the camera began after the start of image acquisition
        camera_minus_image_index[n]=peaks_camera[image_in_camera_index[n]]-peaks_image[n]

    #Save the two index in a pickle file
    new_file_name=input_file+'frame_data'

    with open(new_file_name, "wb") as f:
      pickle.dump([image_in_camera_index,camera_minus_image_index], f)
    print(new_file_name)

    self.frame_data_path = new_file_name

    return self.frame_data_path

  def detect_piezo_start_frames(self):
    """
    a method for finding the imaging frame where the piezo stimulus starts.

    * each object should have the path to the frame info file.
    * number_of_channels: number of channels in the data. Should be 7.
    * piezo_channel: the channel that contains the piezo signal. Should be channel 6.
    * imaging_channel: the channel that contains the imaging frame signal. Should be channel 2 (3rd channel).
    * i_height, i_width, i_distance: parameters for detecting image frame signal with scipy.signal.findpeaks.
    * window_width: window to average the frame signals (necessary if sampling rate is too high). Should be 10.
    * n_of_z: number of z-levels in the fast-z image stack
    * skip_interval: number of samples to skip from the initial piezo start for the detection of the second stimulus
    """
    input_file=self.frame_signal_filepath

    number_of_channels=self.number_of_channels
    piezo_channel=self.piezo_channel
    imaging_channel = self.imaging_channel
    i_height = self.i_height
    i_width = self.i_width
    i_distance = self.i_distance
    window_width = self.window_width
    n_of_z = self.n_of_z
    skip_interval = self.skip_interval


    #read the binary file.
    frame_data=np.fromfile(input_file)

    #Check the number of data points
    number_of_data=frame_data.shape[0]

    #Get the piezo signal
    piezo_signal_index=np.arange(piezo_channel,number_of_data,number_of_channels)
    piezo_signal=frame_data[piezo_signal_index]

    #find when the piezo was on: define "On" as time point that it reaches half max amplitude.
    piezo_threshold=(np.max(piezo_signal)-np.min(piezo_signal))/2+np.min(piezo_signal)
    piezo_on=piezo_signal>=piezo_threshold

    #find first start
    first_start=np.argmax(piezo_on)

    #Find second start: hard coded for now
    second_start=np.argmax(piezo_on[first_start+skip_interval:])+first_start+skip_interval

    #Get the image frame signal
    image_frame_signal_index=np.arange(imaging_channel,number_of_data,number_of_channels)
    image_frame_signal=frame_data[image_frame_signal_index]
    #Convolve the image_frame_signal
    image_frame_signal=np.convolve(image_frame_signal,np.ones((window_width,))/window_width, mode='valid')

    #see how the image signal changes
    image_diff=np.diff(image_frame_signal)
    #Use scipy.signal.find_peaks to get the peaks in the diff data.
    peaks_image, _ =scipy.signal.find_peaks(image_diff,height=i_height, width=i_width, distance=i_distance)

    image_interval=np.diff(peaks_image)
    plt.figure(figsize=(10,3))
    plt.plot(image_interval)
    sns.despine()

    #we need to divide by n_of_z to convert to the volume number from the frame number

    #Find the frame that's closest to the piezo start
    time_to_piezo=np.absolute(peaks_image-first_start)
    #Find the image that is closest (frame number)
    first_piezo_frame=np.argmin(time_to_piezo)
    #Find the volume that started after the piezo on.
    first_piezo_frame=first_piezo_frame//n_of_z+1
    print(first_piezo_frame)

    #Find the frame that's closest to the second start
    #Find the frame that's closest to the piezo start
    time_to_piezo=np.absolute(peaks_image-second_start)
    #Find the image that is closest (frame number)
    second_piezo_frame=np.argmin(time_to_piezo)
    second_piezo_frame=second_piezo_frame//n_of_z+1
    print(second_piezo_frame)

    #Save the two start times in a pickle file
    new_file_name=input_file+'piezo_data'

    with open(new_file_name, "wb") as f:
      pickle.dump([first_piezo_frame,second_piezo_frame], f)
    print(new_file_name)

    self.piezo_data_path = new_file_name

    return self.piezo_data_path

  def make_synchronized_video_gray_piezo(self):
    """
    For Piezo trials that don't have the videos.
    a method to load the filtered and registered data for both tdTomato and GCaMP
    and make a synchronized .avi movie.
    *tdTomato_file: a pickle file that contains the filtered and registered tdTomato images.
    Each object should have a path to this file
    *GCaMP_file: same for the GCaMP.
    * n_of_z: number of z levels
    * frames_per_second: defines how many fps for the video.
    *min_range and max_range defines the min and max for the tdTomato (1) and GCaMP (2) image.


    """
    tdTomato_file=self.tdTomato_registered_path
    GCaMP_file=self.gcamp_registered_path

    n_of_z = self.n_of_z
    frames_per_second = self.frames_per_second
    min_range1 = self.min_range1
    max_range1 = self.max_range1
    min_range2 = self.min_range2
    max_range2 = self.max_range2

    #Get tdTomato images
    with open(tdTomato_file, "rb") as f:
      tdTomato_Filtered=pickle.load(f)
    #Get GCaMP images
    with open(GCaMP_file, "rb") as f:
      GCaMP_Filtered=pickle.load(f)

    #Number of frames should be the same for tdTomato and GCaMP.
    total_frames=tdTomato_Filtered.shape[0]
    x_size=tdTomato_Filtered.shape[2]#number of columns
    y_size=tdTomato_Filtered.shape[1]#number of rows

    #Make a video with the tdTomato signal + GCaMP signal + prep image
    video_name = (tdTomato_file+"synchronized_video_gray.avi")
    #Image width will be 2 * imaging_width
    #Final "0" necessary for gray scale image
    video = cv2.VideoWriter(video_name,cv2.VideoWriter_fourcc(*'mp4v'),frames_per_second,(x_size*2,y_size),0)


    #For making video, all numbers below min_range1 will be treated as 0.
    #all numbers above max_range1 will be treated as max_range1 value.
    #Then normalize the image to be between 0 to 255.
    tdTomato_Filtered[tdTomato_Filtered<=min_range1]=0
    tdTomato_Filtered[tdTomato_Filtered>=max_range1]=max_range1
    range_adjusted_tdTomato=(tdTomato_Filtered/max_range1)*255

    #For GCaMP
    GCaMP_Filtered[GCaMP_Filtered<=min_range2]=0
    GCaMP_Filtered[GCaMP_Filtered>=max_range2]=max_range2
    range_adjusted_GCaMP=(GCaMP_Filtered/max_range2)*255

    #Initialize the frame
    frame_original=np.zeros((y_size,x_size*2))

    for video_frame in range(total_frames):
      #Insert images in the right location.
      frame_original[:,0:x_size]=range_adjusted_tdTomato[video_frame,:,:]
      frame_original[:,x_size:x_size*2]=range_adjusted_GCaMP[video_frame,:,:]

      frame=np.uint8(frame_original)

      video.write(frame)

    video.release()

  def get_piezo_response_map_separate_z(self):
    """
    a method to generate the DF/F and DR/R response map in separate z level
    for the piezo stimulation:
    load the filtered and registered data for both tdTomato and GCaMP and calculate
    the DF/F and DR/R map during the two piezo stimuli and average them.
    *tdTomato_file: a pickle file that contains the filtered and registered tdTomato images.
    Each object should have a path to this file
    *GCaMP_file: same for the GCaMP.
    *piezo_data_file: a file that contains first and second piezo start frames (volumes)
    *min_range and max_range defines the min and max for the DF/F and DR/R images.


    """
    tdTomato_file=self.tdTomato_registered_path
    gcamp_file=self.gcamp_registered_path
    piezo_data_file=self.piezo_data_path
    min_range3 = self.min_range3
    max_range3 = self.max_range3
    gcamp_threshold = self.gcamp_threshold
    tdTomato_threshold = self.tdTomato_threshold
    ratio_threshold = self.ratio_threshold

    response_range = self.response_range
    base_range = self.base_range
    n_of_z = self.n_of_z

    #load the info on piezo start frame and get the tdTomato and gcamp data (filtered and registered)
    with open(piezo_data_file, "rb") as f:
      [first_piezo_start,second_piezo_start]=pickle.load(f)

    with open(tdTomato_file,"rb") as f:
      tdTomato_registered=pickle.load(f)

    with open(gcamp_file,"rb") as f:
      gcamp_registered=pickle.load(f)

    #tdTomato_registered and gcamp_registered may contain negative pixel values.
    #image brightness should always be positive (or zero), so subtract the min
    #value to make all values above zero.
    tdTomato_registered=tdTomato_registered-np.min(tdTomato_registered)
    gcamp_registered=gcamp_registered-np.min(gcamp_registered)

    #initialize the data array
    average_tdTomato_all=np.zeros((n_of_z,tdTomato_registered.shape[2],tdTomato_registered.shape[3]))
    average_gcamp_all=np.zeros_like(average_tdTomato_all)
    base_tdTomato_all=np.zeros_like(average_tdTomato_all)
    base_gcamp_all=np.zeros_like(average_tdTomato_all)
    ratio_response_all=np.zeros_like(average_tdTomato_all)
    ratio_baseline_all=np.zeros_like(average_tdTomato_all)
    DF_F_map_all=np.zeros_like(average_tdTomato_all)
    DR_R_map_all=np.zeros_like(average_tdTomato_all)


    #calcuate the baseline and the response images for each z-level
    for z_level in range(n_of_z):
      #
      average_tdTomato=np.average(tdTomato_registered[z_level,first_piezo_start:first_piezo_start+response_range,:,:],axis=0)
      average_tdTomato2=np.average(tdTomato_registered[z_level,second_piezo_start:second_piezo_start+response_range,:,:],axis=0)
      average_tdTomato=(average_tdTomato+average_tdTomato2)/2

      average_gcamp=np.average(gcamp_registered[z_level,first_piezo_start:first_piezo_start+response_range,:,:], axis=0)
      average_gcamp2=np.average(gcamp_registered[z_level,second_piezo_start:second_piezo_start+response_range,:,:], axis=0)
      average_gcamp=(average_gcamp+average_gcamp2)/2

      base_tdTomato=np.average(tdTomato_registered[z_level,first_piezo_start-base_range:first_piezo_start,:,:],axis=0)
      base_tdTomato2=np.average(tdTomato_registered[z_level,second_piezo_start-base_range:second_piezo_start,:,:],axis=0)
      base_tdTomato=(base_tdTomato+base_tdTomato2)/2

      base_gcamp=np.average(gcamp_registered[z_level,first_piezo_start-base_range:first_piezo_start,:,:],axis=0)
      base_gcamp2=np.average(gcamp_registered[z_level,second_piezo_start-base_range:second_piezo_start,:,:],axis=0)
      base_gcamp=(base_gcamp+base_gcamp2)/2

      #initialize the response map to zero
      ratio_response=np.zeros_like(base_gcamp)
      ratio_baseline=np.zeros_like(base_gcamp)
      DF_F_map=np.zeros_like(base_gcamp)
      DR_R_map=np.zeros_like(base_gcamp)

      #calculate ratio, but we need to exclude pixels with very low tdTomato value to avoid high noise
      ratio_response=np.divide(average_gcamp,average_tdTomato, where=((average_tdTomato>=tdTomato_threshold)&(base_tdTomato>=tdTomato_threshold)))
      ratio_baseline=np.divide(base_gcamp,base_tdTomato, where=((average_tdTomato>=tdTomato_threshold)&(base_tdTomato>=tdTomato_threshold)))

      #plot in a figure
      fig, axs = plt.subplots(1,3, figsize=(12,5),tight_layout = True)

      axs[0].imshow(base_gcamp)
      axs[0].set_yticks([])
      axs[0].set_xticks([])
      axs[0].set_title('gcamp baseline', fontsize=20)

      #DF/F calculated only for pixels whose base_gcamp value is above the threshold
      DF_F_map=np.divide((average_gcamp-base_gcamp),base_gcamp,where=(base_gcamp>=gcamp_threshold))
      axs[1].imshow(DF_F_map,vmin=min_range3,vmax=max_range3)
      axs[1].set_yticks([])
      axs[1].set_xticks([])
      axs[1].set_title('DF/F map', fontsize=20)

      #DR/R calculated only for pixels whose ratio_baseline is above the threshold and we have certain level of baseline gcamp
      DR_R_map=np.divide((ratio_response-ratio_baseline),ratio_baseline,where=((ratio_baseline>=ratio_threshold)&(base_gcamp>=gcamp_threshold)))
      axs[2].imshow(DR_R_map,vmin=min_range3,vmax=max_range3)
      axs[2].set_yticks([])
      axs[2].set_xticks([])
      axs[2].set_title('DR/R map', fontsize=20)

      #Place in the appropriate data array.
      average_tdTomato_all[z_level,:,:]=average_tdTomato
      average_gcamp_all[z_level,:,:]=average_gcamp
      base_tdTomato_all[z_level,:,:]=base_tdTomato
      base_gcamp_all[z_level,:,:]=base_gcamp
      ratio_response_all[z_level,:,:]=ratio_response
      ratio_baseline_all[z_level,:,:]=ratio_baseline
      DF_F_map_all[z_level,:,:]=DF_F_map
      DR_R_map_all[z_level,:,:]=DR_R_map

    #Save the data array.
    outfile_name=gcamp_file+'_maps'

    with open(outfile_name, "wb") as f:
      pickle.dump([average_tdTomato_all,average_gcamp_all,base_tdTomato_all, base_gcamp_all, ratio_response_all, ratio_baseline_all, DF_F_map_all, DR_R_map_all], f)
    print(outfile_name)

    self.map_data_path = outfile_name

    return self.map_data_path

  def merge_piezo_response_map(self):
    """
    a method to merge the DF/F and DR/R response map from separate z level
    into one response map.
    load the response map and take the max response for each pixel.
    *map_data_file: a pickle file that contains all the response maps.
    *min_range and max_range defines the min and max for the DF/F and DR/R images.
    """
    map_data_file=self.map_data_path
    min_range3 = self.min_range3
    max_range3 = self.max_range3

    #load all the response maps
    with open(map_data_file, "rb") as f:
      [average_tdTomato_all,average_gcamp_all,base_tdTomato_all, base_gcamp_all, ratio_response_all, ratio_baseline_all, DF_F_map_all, DR_R_map_all]=pickle.load(f)

    #take the maximum intensity projection of the responses.
    base_gcamp_projection=np.nanmax(base_gcamp_all,axis=0)
    DF_F_projection=np.nanmax(DF_F_map_all,axis=0)
    DR_R_projection=np.nanmax(DR_R_map_all,axis=0)

    #plot in a figure
    fig, axs = plt.subplots(1,3, figsize=(12,5),tight_layout = True)

    axs[0].imshow(base_gcamp_projection)
    axs[0].set_yticks([])
    axs[0].set_xticks([])
    axs[0].set_title('gcamp merged', fontsize=20)


    axs[1].imshow(DF_F_projection,vmin=min_range3,vmax=max_range3)
    axs[1].set_yticks([])
    axs[1].set_xticks([])
    axs[1].set_title('DF/F merged', fontsize=20)

    axs[2].imshow(DR_R_projection,vmin=min_range3,vmax=max_range3)
    axs[2].set_yticks([])
    axs[2].set_xticks([])
    axs[2].set_title('DR/R merged', fontsize=20)

    #Save the merged maps.
    outfile_name=map_data_file+'_merged'

    with open(outfile_name, "wb") as f:
      pickle.dump([base_gcamp_projection, DF_F_projection, DR_R_projection], f)
    print(outfile_name)

    self.merged_path = outfile_name

    return self.merged_path
