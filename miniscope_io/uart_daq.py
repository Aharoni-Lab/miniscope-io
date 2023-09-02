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

# Parsers for daq inputs
daqParser = argparse.ArgumentParser("uart_image_capture")
daqParser.add_argument('port', help="serial port")
daqParser.add_argument('baudrate', help="baudrate")

# Parsers for update LED
updateDeviceParser = argparse.ArgumentParser("updateDevice")
updateDeviceParser.add_argument('port', help="serial port")
updateDeviceParser.add_argument('baudrate', help="baudrate")
updateDeviceParser.add_argument('module', help="module to update")
updateDeviceParser.add_argument('value', help="LED value")

class uart_daq:
    def __init__(self, frame_width: int = 304, frame_height: int = 304, preamble = b'\x78\x56\x34\x12'):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.preamble = preamble

    # Receive buffers and push into serial_buffer_queue
    def _uart_recv(self, serial_buffer_queue, comport: str, baudrate: int):
        #set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(datetime.now().strftime('log/uart_recv/uart_recv_log%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        #set up serial port
        serial_port = serial.Serial(port=comport, baudrate=baudrate, timeout=5, stopbits=1)
        locallogs.info('Serial port open: ' + str(serial_port.name))
        
        # Throw away the first buffer because it won't fully come in
        log_uart_buffer = bytearray(serial_port.read_until(self.preamble))

        while 1:
            # read UART data until preamble and put into queue
            log_uart_buffer = bytearray(serial_port.read_until(self.preamble))
            serial_buffer_queue.put(log_uart_buffer)            

        time.sleep(1) #time for ending other process
        serial_port.close()
        print('Close serial port')
        sys.exit(1)

    # Pull out data buffers from serial_buffer_queue
    # Make a list of buffers forming a frame and push into frame_buffer_queue
    def _buffer_to_frame(self, serial_buffer_queue, frame_buffer_queue):
        #set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(datetime.now().strftime('log/buffer_to_frame/buffer_to_frame_log%Y_%m_%d_%H_%M.log'))
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        # List for containing buffer data for a frame. Number of element shouldn't be hard coded.
        frame_buffer = [b'\x00', b'\x00', b'\x00', b'\x00', b'\x00']

        frame_buffer_index = 0 # Index of buffer within frame
        frame_num = 0 # Frame number

        while 1:
            if (serial_buffer_queue.qsize() > 0): # Higher is safe but lower should be faster.
                serial_buffer = serial_buffer_queue.get() # grab one buffer from queue
                
                #log metadata
                locallogs.debug('UART_RECV, FRAME_NUM, ' + str(int.from_bytes(serial_buffer[4:8][::-1], "big")) + \
                    ', BUFFER_COUNT, ' + str(int.from_bytes(serial_buffer[8:12][::-1], "big")) + \
                    ', LINKED_LIST, ' + str(int.from_bytes(serial_buffer[0:4][::-1], "big")) + \
                    ', FRAME_BUFFER_COUNT, ' + str(int.from_bytes(serial_buffer[12:16][::-1], "big")) + \
                    ', PIXEL_COUNT, ' + str(int.from_bytes(serial_buffer[28:32][::-1], "big")) + \
                    ', TIMESTAMP, ' + str(int.from_bytes(serial_buffer[24:28][::-1], "big")) + \
                    ', UART_recv_len, ' + str(len(serial_buffer)))

                # if first buffer of a frame
                if int.from_bytes(serial_buffer[4:8][::-1], "big") != frame_num:

                    # push frame_buffer into frame_buffer queue
                    if frame_num != 0:
                        frame_buffer_queue.put(frame_buffer)
                        frame_buffer_index = 0

                    # update frame_num
                    frame_num = int.from_bytes(serial_buffer[4:8][::-1], "big")
                    # init frame_buffer
                    frame_buffer = [b'\x00', b'\x00', b'\x00', b'\x00', b'\x00']

                    if int.from_bytes(serial_buffer[12:16][::-1], "big") == 0:
                        frame_buffer[0] = serial_buffer

                    frame_buffer_index += 1
                    
                # if same frame_num with previous buffer.
                elif int.from_bytes(serial_buffer[4:8][::-1], "big") == frame_num and int.from_bytes(serial_buffer[12:16][::-1], "big") >= frame_buffer_index:
                    if int.from_bytes(serial_buffer[12:16][::-1], "big") > frame_buffer_index:
                        frame_buffer_index = int.from_bytes(serial_buffer[12:16][::-1], "big")
                    frame_buffer[frame_buffer_index] = serial_buffer
                    locallogs.debug('----buffer #' + str(frame_buffer_index) + " stored")
                    frame_buffer_index += 1
                    
                # if lost frame from buffer -> reset index
                else:
                    frame_buffer_index = 0

    def _format_frame(self, frame_buffer_queue, imagearray):
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
            if(frame_buffer_queue.qsize() > 0): # Higher is safe but lower is fast.
                locallogs.debug('Found frame in queue')

                frame_data = frame_buffer_queue.get() # pixel data for single frame

                num_pixel_in_frame = 0 #total number of pixels in frame
                num_pixel_in_buffer = 0 #number of pixels in frame (Metadata)
                num_pixel_lost_in_frame = 0 #number of pixels lost in frame

                imagearray_frame = np.zeros(int(self.frame_width * self.frame_height), np.uint8) # frame data to store in imagearray queue

                for i in range(0,5): # Number of buffers per frame. This shouldn't be hardcoded.
                    num_pixel_in_buffer = int.from_bytes(frame_data[i][28:32][::-1], "big")
                    
                    #
                    if len(frame_data) >= buffer_numpixel_assert[i] + HEADER_LENGTH:
                        padded_temp_pixel_vector = bytearray(frame_data[i][HEADER_LENGTH:HEADER_LENGTH + buffer_numpixel_assert[i]])
                    else:
                        temp_pixel_vector = bytearray(frame_data[i][HEADER_LENGTH:-1])
                        num_pixel_lost_in_frame += num_pixel_in_buffer - len(temp_pixel_vector)
                        padded_temp_pixel_vector = bytearray([0] * (buffer_numpixel_assert[i] - len(temp_pixel_vector)))
                        padded_temp_pixel_vector.extend(temp_pixel_vector)
                    
                    '''
                    try:
                        assert len(temp_pixel_vector) == num_pixel_in_buffer
                    except:
                        locallogs.debug('Buffer pixel count warning: metadata and actual length do not match')
                        locallogs.debug('num_pixel_in_buffer: ' + str(num_pixel_in_buffer) + \
                                    ', len(pixel_vector): ' + str(len(temp_pixel_vector)) + \
                                    ', frame_buffer_index: ' + str(i) + \
                                    ', len(frame_buffer_queue[i]): ' + str(len(frame_data[i])) + '\n')
                    '''
                    if i == 0:
                        pixel_vector = padded_temp_pixel_vector
                    else:
                        pixel_vector.extend(padded_temp_pixel_vector)
                
                if len(pixel_vector) > self.frame_width * self.frame_height:
                    pixel_vector = pixel_vector[0:self.frame_width * self.frame_height]
                #if num_frame_pixel == self.num_pixel_assert:
                imagearray_frame[0::4] = np.uint8(pixel_vector[3::4])
                imagearray_frame[1::4] = np.uint8(pixel_vector[2::4])
                imagearray_frame[2::4] = np.uint8(pixel_vector[1::4])
                imagearray_frame[3::4] = np.uint8(pixel_vector[0::4])
                imagearray.put(imagearray_frame)
                locallogs.info('FRAME: ' + str(int.from_bytes(frame_data[0][4:8][::-1], "big")) + \
                            ', TOTAL_PX: ' + str(num_pixel_in_frame) + \
                            ', LOST_PX: ' + str(num_pixel_lost_in_frame))

    # COM port should probably be automatically found but not sure yet how to distinguish with other devices.
    def capture(self, comport:str = 'COM3', baudrate:int = 1200000, mode:str = 'DEBUG'):
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
        serial_buffer_queue = queue_manager.Queue(10) # b'\x00' # hand over single buffer: uart_recv() -> buffer_to_frame()
        frame_buffer_queue = queue_manager.Queue(5) #[b'\x00', b'\x00', b'\x00', b'\x00', b'\x00'] # hand over a frame (five buffers): buffer_to_frame()
        imagearray = queue_manager.Queue(5)
        imagearray.put(np.zeros(int(self.frame_width * self.frame_height), np.uint8))

        p_uart_recv = multiprocessing.Process(target=self._uart_recv, args=(serial_buffer_queue, comport, baudrate, ))
        p_buffer_to_frame = multiprocessing.Process(target=self._buffer_to_frame, args=(serial_buffer_queue, frame_buffer_queue, ))
        p_format_frame = multiprocessing.Process(target=self._format_frame, args=(frame_buffer_queue, imagearray, ))
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

def updateDevice():
    args = updateDeviceParser.parse_args()
    moduleList = ['LED', 'EWL']

    ledMAX = 100
    ledMIN = 0

    ewlMAX = 255
    ewlMIN = 0

    ledDeviceTag = 0 # 2-bits each for now
    ewlDeviceTag = 1 # 2-bits each for now

    deviceTagPos = 4
    preamblePos = 6

    Preamble = [2, 1] # 2-bits each for now

    uartPayload = 4
    uartRepeat = 5
    uartTimeGap = 0.01

    try:
        assert len(vars(args)) == 4
    except AssertionError as msg:
        print(msg)
        print("Usage: updateDevice [COM port] [baudrate] [module] [value]")
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

    try:
        module = str(args.module)
        assert module in moduleList
    except AssertionError as msg:
        print(msg)
        print("Available modules:")
        for module in moduleList:
            print('\t' + module)
        sys.exit(1)

    try:
        value = int(args.value)
    except Exception as e:
        print(e)
        print("Value needs to be an integer")
        sys.exit(1)

    try:
        if module == 'LED':
            assert (value <= ledMAX and value >= ledMIN)
        if module == 'EWL':
            assert (value <= ewlMAX and value >= ewlMIN)
    except AssertionError as msg:
        print(msg)
        if module == 'LED':
            print("LED value need to be a integer within 0-100")
        if module == 'EWL':
            print("EWL value need to be an integer within 0-255")
        sys.exit(1)
    
    if(module == 'LED'):
        deviceTag = ledDeviceTag << deviceTagPos
    elif(module == 'EWL'):
        deviceTag = ewlDeviceTag << deviceTagPos

    command = [0,0]

    command[0] = int(Preamble[0] * 2 ** preamblePos + deviceTag + np.floor(value/(2**uartPayload))).to_bytes(1, 'big')
    command[1] = int(Preamble[1] * 2 ** preamblePos + deviceTag + value%(2**uartPayload)).to_bytes(1, 'big')

    #set up serial port
    try:
        serial_port = serial.Serial(port=comport, baudrate=baudrate, timeout=5, stopbits=1)
    except Exception as e:
        print(e)
        sys.exit(1)
    print('Open serial port')

    for uartCommand in command:
        for repeat in range(uartRepeat):
            # read UART data until preamble and put into queue
            serial_port.write(uartCommand)
            time.sleep(uartTimeGap)
    
    serial_port.close()
    print('\t' + module + ': ' +str(value))
    print('Close serial port')
    sys.exit(1)

def main():
    args = daqParser.parse_args()

    try:
        assert len(vars(args)) == 2
    except AssertionError as msg:
        print(msg)
        print("Usage: uart_image_capture [COM port] [baudrate]")
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