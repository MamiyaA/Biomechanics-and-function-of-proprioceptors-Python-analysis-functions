
parameter_file = [
                  {'gaussian_filter' : [1,5,5],# size of the gaussian filter kernel [1,5,5] is recommended for downstairs 2P with 5 Hz volume acquisition @ 512 x 512 resolution.
                  'number_of_channels': 7,# number of channels in the analog input data
                  'camera_channel': 1,# channel that contains the camera signal (ch1 for downstairs: counting from channel 0)
                  'imaging_channel': 2, # channel that conains the Y mirros signal (ch2 for downstairs)
                  'piezo_channel': 6, # channel that contains the piezo stimulation signal.
                  'c_height': 0.3, # camera frame detection peak height
                  'c_width': 0.1, # camera frame detection peak width
                  'c_distance': 50, # camera frame detection interpeak distance
                  'i_height': 1, # image frame detection peak height
                  'i_width': 1, # image frame detection peak width
                  'i_distance': 100, #image frame detection interpeak distance
                  'window_width': 1, # width of window average
                  'skip_interval': 100000, # number of sample point to skip after the initial piezo detection
                  'n_of_z': 6, #number of z levels in the image
                  'frames_per_second': 10, # number of frames per second for the new video
                  'min_range1': 25, # min value for the tdTomato channel
                  'max_range1': 700, # max value for the tdTomato channel
                  'min_range2': 10, # min value for the GCaMP channel
                  'max_range2': 200, # max value for the GCaMP channel
                  'min_range3': 0, #min value for the DF/F and DR/R
                  'max_range3': 3, #max value for the DF/F and DR/R
                  'gcamp_threshold': 10, #threshold for gcamp to calculate the DF/F and DR/R
                  'tdTomato_threshold': 40, #threshold for tdTomato to calculate the DR/R
                  'ratio_threshold': 0.1,#threshold for gcamp/tdTomato ratio to calculate the DR/R
                  'response_range': 20, #number of frames after the start of the piezo stimulus to use as the response
                  'base_range': 20, #number of frames before the start of the piezo stimulus to use as the baseline
                  'upsample': 4, # upsampling factor. Will register to 1/upsample pixels
                  'registration_channel': 2 # imaging channel to use for registering images
                   }
]

outfile_name=path+'/config.yaml'

with open(outfile_name, 'w') as yaml_file:
    parameters = yaml.dump(parameter_file, yaml_file)

print(outfile_name)
