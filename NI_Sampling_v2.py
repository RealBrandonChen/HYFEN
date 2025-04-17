import nidaqmx
from nidaqmx.constants import (AcquisitionType,RegenerationMode, Edge, TerminalConfiguration, VoltageUnits)
import numpy as np
import matplotlib
matplotlib.use('qt5agg') # use Qt5 as the background engine, defacut matplot engine is Tk, will casue loop processes error
import matplotlib.pyplot as plt
import datetime

class daq_samp():

    dev_name = 'Dev1'
    task_ai = [] # DAQmx task handle for analog input

    def __init__(self, sample_rate, im_size, showplot, autosetup=True, savefig=False):
        # to eliminate the Gaussian noise, we acquire 10 samples per focused image,
        self.multisampling = 10
        self.sample_rate = sample_rate * self.multisampling 
        self.im_size = 256 
        self.scanning_points = self.im_size**2 
        self.showplot = showplot
        self.savefig = savefig
        self.img_sum = []
        self.framesTotal = 0
        
        if autosetup:
            self.set_up_daq()
        if showplot:
            self.setup_plot()
            
    def set_up_daq(self):
        self.task_ai = nidaqmx.Task()
        self.task_ai.ai_channels.add_ai_voltage_chan('%s/ai5' % self.dev_name, terminal_config=TerminalConfiguration.RSE, min_val=-5.0, max_val=5.0, units=VoltageUnits.VOLTS)
        self.task_ai.timing.cfg_samp_clk_timing(self.sample_rate * 1.1, source= "/Dev1/PFI0", active_edge=Edge.RISING, samps_per_chan=self.scanning_points * self.multisampling,
                                                sample_mode=AcquisitionType.CONTINUOUS)
        # Set conversion rate (resampling)
        # self.task_ai.timing.ai_conv_rate = 5
        # Set start trigger with DMD first pulse
        self.task_ai.triggers.start_trigger.cfg_dig_edge_start_trig("/Dev1/PFI0", Edge.RISING)

        # NOTE: must explicitly set the input buffer so that it's a multiple
        # of the number of samples per frame. Setting the samples per channel 
        # (above) does not achieve this.
        self.task_ai.in_stream.input_buf_size = self.scanning_points * 2 * self.multisampling
        
        # * Register a a callback function to be run every N samples
        self.task_ai.register_every_n_samples_acquired_into_buffer_event(self.scanning_points * self.multisampling, self.read_and_display_last_frame)
        # self.task_ai.register_every_n_samples_acquired_into_buffer_event(self.scanning_points * self.multisampling, self.callback)
        
    def setup_plot(self):
        plt.ion()
        # plt.switch_backend('agg')
        dummy = np.random.randint(0,1000,size=(self.im_size, self.im_size))
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.window = self.ax.imshow(dummy)
    
    def daq_data_process(self):
        data = self.task_ai.read(number_of_samples_per_channel=self.scanning_points * self.multisampling)
        data_std = np.std(data)
        data_mean = np.mean(data)
        print("The mean value and the std of the data are: {0} and {1}".format(data_mean, data_std))
        return data_std, data_mean

    def start_acquisition(self):
        if not self._task_created():
            return
        self.task_ai.start()
    
    def stop_acquisition(self):
        if not self._task_created():
            return
        
        if self.savefig:
            np.save("Acquisition\Fluorescence_images_{0}".format(datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), np.array(self.img_sum).transpose(1,2,0))
            
        self.task_ai.stop()
        
    def close_tasks(self):
        # Nothing to do here
        if not self._task_created():
            return

        self.task_ai.close()
    
    # House-keeping methods follow
    def _task_created(self):
        # Nothing to do here
        '''
        Return True if a task has been created
        '''

        if isinstance(self.task_ai,nidaqmx.task.Task):
            return True
        else:
            print('No tasks created: run the set_up_tasks method')
            return False
        
    def read_and_display_last_frame(self,tTask, event_type, num_samples, callback_data):
        # Callback function that extract data and update plots
        data_multi = self.task_ai.read(number_of_samples_per_channel=self.scanning_points * self.multisampling)
        data = np.mean(np.array(data_multi).reshape(-1, self.multisampling), axis=1)
        # Convert data to 16bit depth image
        data_int16 = np.uint16(data * -2731) # Use 1.5 as maximum analog voltage of PMT is 1.5 Volt 4096/1.5=2731
        # check if all intensities are positive b/c readings from DAQ could be negative
        _im = data_int16.reshape(self.im_size,self.im_size)

        if self.showplot:
            self.window.set_data(np.transpose(_im))
            self.window.figure.canvas.draw()
            self.window.figure.canvas.flush_events()
        
        if self.savefig:
            self.img_sum.append(_im)
            self.framesTotal+=1
            print("Recorded frame number: " + str(self.framesTotal))
        return 0
    
    total_read = 0
    def callback(self,task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        """Callback function for reading signals."""
        read = len(self.task_ai.read(number_of_samples_per_channel=number_of_samples))
        self.total_read += read
        print(f"Acquired data: {read} samples. Total {self.total_read}.", end="\r")

        return 0
            
    