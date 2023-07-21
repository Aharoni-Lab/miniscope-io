import os
import argparse
import serial
import multiprocessing
import coloredlogs, logging
from datetime import datetime
import numpy as np
import cv2
import sys
import time

parser = argparse.ArgumentParser("uart_image_capture")
parser.add_argument('port', help="serial port")
parser.add_argument('baudrate', help="baudrate")

class uart_daq:
    def __init__(self, frame_width: int = 304, frame_height: int = 304, preamble = b'\x34\x12'):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.preamble = preamble

    def _uart_recv(self, serial_buffer_read, comport: str, baudrate: int):
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(datetime.now().strftime('log/uart_recv/uart_recv_log%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)
        serial_port = serial.Serial(port=comport, baudrate=baudrate, timeout=5, stopbits=1)
        locallogs.info('Serial port: ' + str(serial_port.name))

        while 1:
            log_uart_buffer = bytearray(serial_port.read_until(self.preamble))
            serial_buffer_read.put(log_uart_buffer)            

        time.sleep(2) #time for ending other process 2sec
        serial_port.close()
        print('Close serial port')
        sys.exit(1)

    def _buffer_to_frame(self, serial_buffer_read, buffer_frame):
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(datetime.now().strftime('log/buffer_to_frame/buffer_to_frame_log%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)


        buffer_frame_copy = [b'\x00', b'\x00', b'\x00', b'\x00', b'\x00']
        buffer_frame_index = 0
        frame_num = 0
        

        while 1:
            if (serial_buffer_read.qsize() > 1): # for safety
                serial_buffer_copy = serial_buffer_read.get()
                
                locallogs.info('UART_RECV, FRAME_NUM, ' + str(int.from_bytes(serial_buffer_copy[4:8][::-1], "big")) + \
                    ', BUFFER_COUNT, ' + str(int.from_bytes(serial_buffer_copy[8:12][::-1], "big")) + \
                    ', LINKED_LIST, ' + str(int.from_bytes(serial_buffer_copy[0:4][::-1], "big")) + \
                    ', FRAME_BUFFER_COUNT, ' + str(int.from_bytes(serial_buffer_copy[12:16][::-1], "big")) + \
                    ', PIXEL_COUNT, ' + str(int.from_bytes(serial_buffer_copy[28:32][::-1], "big")) + \
                    ', TIMESTAMP, ' + str(int.from_bytes(serial_buffer_copy[24:28][::-1], "big")) + \
                    ', UART_recv_len, ' + str(len(serial_buffer_copy)))

                # if first buffer of the frame
                if int.from_bytes(serial_buffer_copy[4:8][::-1], "big") > frame_num and int.from_bytes(serial_buffer_copy[12:16][::-1], "big") == 0:
                    # update frame_num
                    frame_num = int.from_bytes(serial_buffer_copy[4:8][::-1], "big")
                    buffer_frame_copy[0] = serial_buffer_copy
                    buffer_frame_index += 1
                    
                # if same frame_num with previous buffer
                elif int.from_bytes(serial_buffer_copy[4:8][::-1], "big") == frame_num and int.from_bytes(serial_buffer_copy[12:16][::-1], "big") == buffer_frame_index:
                    buffer_frame_copy[buffer_frame_index] = serial_buffer_copy
                    locallogs.info('----buffer #' + str(buffer_frame_index) + "stored")
                    buffer_frame_index += 1
                    if buffer_frame_index == 5:
                        # full frame received
                        buffer_frame.put(buffer_frame_copy)
                        buffer_frame_index = 0
                        locallogs.info('----frame #' + str(frame_num) + " stored")

                # lost buffer -> reset index
                else:
                    buffer_frame_index = 0

    def _format_frame(self, buffer_frame, imagearray):
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(datetime.now().strftime('log/format_frame/format_frame_log%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        # This shouldn't be hardcoded
        buffer_numpixel_assert = [20440, 20440, 20440, 20440, 10656]

        HEADER_LENGTH = (10 - 1) * 4

        while 1:
            if(buffer_frame.qsize() > 0): # for safety
                locallogs.info('Found frame in queue')

                plot_buffer_copy = buffer_frame.get()

                num_frame_pixel = 0
                num_buffer_pixel = 0
                lost_frame_pixel = 0

                imagearray_copy = np.zeros(int(self.frame_width * self.frame_height), np.uint8)

                for i in range(0,5):
                    #num_buffer_pixel = int.from_bytes(plot_buffer_copy[i][28:32][::-1], "big")
                    
                    if len(plot_buffer_copy) >= buffer_numpixel_assert[i] + HEADER_LENGTH:
                        padded_temp_pixel_vector = bytearray(plot_buffer_copy[i][HEADER_LENGTH:HEADER_LENGTH + buffer_numpixel_assert[i]])
                    else:
                        temp_pixel_vector = bytearray(plot_buffer_copy[i][HEADER_LENGTH:-1])
                        lost_frame_pixel += num_buffer_pixel - len(temp_pixel_vector)
                        padded_temp_pixel_vector = bytearray([0] * (buffer_numpixel_assert[i] - len(temp_pixel_vector)))
                        padded_temp_pixel_vector.extend(temp_pixel_vector)
                    
                    '''
                    try:
                        assert len(temp_pixel_vector) == num_buffer_pixel
                    except:
                        locallogs.debug('Buffer pixel count warning: metadata and actual length do not match')
                        locallogs.debug('num_buffer_pixel: ' + str(num_buffer_pixel) + \
                                    ', len(pixel_vector): ' + str(len(temp_pixel_vector)) + \
                                    ', buffer_frame_index: ' + str(i) + \
                                    ', len(buffer_frame[i]): ' + str(len(plot_buffer_copy[i])) + '\n')
                    '''
                    if i == 0:
                        pixel_vector = padded_temp_pixel_vector
                    else:
                        pixel_vector.extend(padded_temp_pixel_vector)
                locallogs.info('FRAME: ' + str(int.from_bytes(plot_buffer_copy[0][4:8][::-1], "big")) + \
                            ', TOTAL_PX: ' + str(num_frame_pixel) + \
                            ', LOST_PX: ' + str(lost_frame_pixel))
                
                if len(pixel_vector) > self.frame_width * self.frame_height:
                    pixel_vector = pixel_vector[0:self.frame_width * self.frame_height]
                #if num_frame_pixel == self.num_pixel_assert:
                imagearray_copy[0::4] = np.uint8(pixel_vector[3::4])
                imagearray_copy[1::4] = np.uint8(pixel_vector[2::4])
                imagearray_copy[2::4] = np.uint8(pixel_vector[1::4])
                imagearray_copy[3::4] = np.uint8(pixel_vector[0::4])
                imagearray.put(imagearray_copy)
                locallogs.info('FRAME: ' + str(int.from_bytes(plot_buffer_copy[0][4:8][::-1], "big")) + ' stored!')

    # COM port should probably be automatically found but not sure yet how to distinguish with other devices.
    def capture(self, comport:str = 'COM3', baudrate:int = 1200000):
        logdirectories = ['log', 'log/uart_recv', 'log/format_frame', 'log/buffer_to_frame']
        for logpath in logdirectories:
            if not os.path.exists(logpath):
                os.makedirs(logpath)
        file = logging.FileHandler(datetime.now().strftime('log/logfile%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        globallogs = logging.getLogger(__name__)
        globallogs.setLevel(logging.DEBUG)

        globallogs.addHandler(file)
        coloredlogs.install(level=logging.DEBUG, logger=globallogs)

        #Queue size is hard coded
        queue_manager = multiprocessing.Manager()
        serial_buffer_read = queue_manager.Queue(10) # b'\x00' # hand over single buffer: uart_recv() -> buffer_to_frame()
        buffer_frame = queue_manager.Queue(5) #[b'\x00', b'\x00', b'\x00', b'\x00', b'\x00'] # hand over a frame (five buffers): buffer_to_frame()
        imagearray = queue_manager.Queue(5)
        imagearray.put(np.zeros(int(self.frame_width * self.frame_height), np.uint8))

        p_uart_recv = multiprocessing.Process(target=self._uart_recv, args=(serial_buffer_read, comport, baudrate, ))
        p_buffer_to_frame = multiprocessing.Process(target=self._buffer_to_frame, args=(serial_buffer_read, buffer_frame, ))
        p_format_frame = multiprocessing.Process(target=self._format_frame, args=(buffer_frame, imagearray, ))
        p_uart_recv.start()
        p_buffer_to_frame.start()
        p_format_frame.start()

        while 1: # Seems like GUI functions should be on main thread in scripts but not sure what it means for this case
            if imagearray.qsize() > 0:
                imagearray_plot = imagearray.get()
                image = imagearray_plot.reshape(self.frame_width, self.frame_height)
                #np.savetxt('imagearray.csv', imagearray, delimiter=',')
                #np.savetxt('image.csv', image, delimiter=',')
                cv2.imshow("image", image)
            if cv2.waitKey(1) == 27:
                cv2.destroyAllWindows()
                cv2.waitKey(100)
                break # esc to quit
        print('End capture')

        while True:
            print("[Terminating] uart_recv()")
            p_uart_recv.terminate()
            time.sleep(0.1)
            if not p_uart_recv.is_alive():
                p_uart_recv.join(timeout=1.0)
                print("[Terminated] uart_recv()")
                break # watchdog process daemon gets [Terminated]

        while True:
            print("[Terminating] buffer_to_frame()")
            p_buffer_to_frame.terminate()
            time.sleep(0.1)
            if not p_buffer_to_frame.is_alive():
                p_buffer_to_frame.join(timeout=1.0)
                print("[Terminated] buffer_to_frame()")
                break # watchdog process daemon gets [Terminated]

        while True:
            print("[Terminating] format_frame()")
            p_format_frame.terminate()
            time.sleep(0.1)
            if not p_format_frame.is_alive():
                p_format_frame.join(timeout=1.0)
                print("[Terminated] format_frame()")
                break # watchdog process daemon gets [Terminated]

def main():
    args = parser.parse_args()

    try:
        assert len(vars(args)) == 2
    except AssertionError as msg:
        print(msg)
        print("Usage: uart_daq.py [COM port] [baudrate]")
        sys.exit(1)

    try:
        comport = str(args.port)
    except (ValueError, IndexError) as e:
        print(e)
        sys.exit(1)

    try:
        baudrate = int(args.baudrate)
    except (ValueError, IndexError) as e:
        print(e)
        sys.exit(1)


    daq_inst = uart_daq()
    daq_inst.capture(comport = comport, baudrate = baudrate)    

if __name__ == '__main__':
    main()