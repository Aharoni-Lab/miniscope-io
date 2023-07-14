import serial
import multiprocessing
import coloredlogs, logging
from datetime import datetime
import numpy as np
import cv2
import sys
import time
#import copy
#import queue
#import warnings

def main(imagearray):
    while 1: # GUI functions on main thread
        if imagearray.qsize() > 0:
            imagearray_plot = imagearray.get()
            image = imagearray_plot.reshape(304,304)
            #np.savetxt('imagearray.csv', imagearray, delimiter=',')
            #np.savetxt('image.csv', image, delimiter=',')
            cv2.imshow("image", image)
        if cv2.waitKey(1) == 27:
            cv2.destroyAllWindows()
            cv2.waitKey(100)
            break # esc to quit

    print('End capture')

def uart_recv(serial_buffer_read, preamble):
    locallogs = logging.getLogger(__name__)
    locallogs.setLevel(logging.DEBUG)

    file = logging.FileHandler(datetime.now().strftime('log/uart_recv/uart_recv_log%Y_%m_%d_%H_%M.log'))
    file.setLevel(logging.DEBUG)
    fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
    file.setFormatter(fileformat)

    locallogs.addHandler(file)
    coloredlogs.install(level=logging.INFO, logger=locallogs)



    serial_port = serial.Serial('COM3', 1200000, timeout=100, stopbits=1)
    locallogs.info('Serial port: ' + str(serial_port.name))

    for uart_buffer_index in range(0,200): # how many buffers to see
        log_uart_buffer = bytearray(serial_port.read_until(preamble))
        serial_buffer_read.put(log_uart_buffer)
        

    time.sleep(2) #time for ending other process 2sec
    serial_port.close()
    print('Close serial port')
    sys.exit(1)

def buffer_to_frame(serial_buffer_read, buffer_frame):
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

def plot_frame(buffer_frame, imagearray, num_pixel_assert):
    locallogs = logging.getLogger(__name__)
    locallogs.setLevel(logging.DEBUG)

    file = logging.FileHandler(datetime.now().strftime('log/plot_frame/plot_frame_log%Y_%m_%d_%H_%M.log'))
    file.setLevel(logging.DEBUG)
    fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
    file.setFormatter(fileformat)

    locallogs.addHandler(file)
    coloredlogs.install(level=logging.INFO, logger=locallogs)

    buffer_numpixel_assert = [20440, 20440, 20440, 20440, 10656]

    HEADER_LENGTH = (10 - 1) * 4
    while 1:
        if(buffer_frame.qsize() > 0): # for safety
            locallogs.info('Found frame in queue')

            plot_buffer_copy = buffer_frame.get()

            num_frame_pixel = 0
            num_buffer_pixel = 0
            lost_frame_pixel = 0

            imagearray_copy = np.zeros(int(num_pixel_assert), np.uint8)

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
            
            if len(pixel_vector) > num_pixel_assert:
                pixel_vector = pixel_vector[0:num_pixel_assert]
            #if num_frame_pixel == num_pixel_assert:
            if 1:
                imagearray_copy[0::4] = np.uint8(pixel_vector[3::4])
                imagearray_copy[1::4] = np.uint8(pixel_vector[2::4])
                imagearray_copy[2::4] = np.uint8(pixel_vector[1::4])
                imagearray_copy[3::4] = np.uint8(pixel_vector[0::4])
            if 0:
                for pixel_index in range(0, num_frame_pixel):
                    if pixel_index % 4 == 0:
                        #imagearray_copy[pixel_index] = np.uint8(pixel_vector[pixel_index + 3])
                        imagearray_copy[pixel_index] = np.uint8(pixel_vector[pixel_index + 3])
                    elif pixel_index % 4 == 1:
                        imagearray_copy[pixel_index] = np.uint8(pixel_vector[pixel_index + 1])
                    elif pixel_index % 4 == 2:
                        imagearray_copy[pixel_index] = np.uint8(pixel_vector[pixel_index - 1])
                    elif pixel_index % 4 == 3:
                        imagearray_copy[pixel_index] = np.uint8(pixel_vector[pixel_index - 3])
            imagearray.put(imagearray_copy)
            locallogs.info('FRAME: ' + str(int.from_bytes(plot_buffer_copy[0][4:8][::-1], "big")) + ' stored!')


def process_map(f):
    return f()

if __name__ == '__main__':
    # global variables
    num_pixel_assert = 304 * 304
    preamble = b'\x34\x12'
    
    globallogs = logging.getLogger(__name__)
    globallogs.setLevel(logging.DEBUG)

    file = logging.FileHandler(datetime.now().strftime('log/logfile%Y_%m_%d_%H_%M.log'))
    file.setLevel(logging.DEBUG)
    fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
    file.setFormatter(fileformat)

    globallogs.addHandler(file)
    coloredlogs.install(level=logging.DEBUG, logger=globallogs)

    serial_buffer_read = multiprocessing.Queue(10) # b'\x00' # hand over single buffer: uart_recv() -> buffer_to_frame()
    buffer_frame = multiprocessing.Queue(5) #[b'\x00', b'\x00', b'\x00', b'\x00', b'\x00'] # hand over a frame (five buffers): buffer_to_frame()
    imagearray = multiprocessing.Queue(5)
    imagearray.put(np.zeros(int(num_pixel_assert), np.uint8))

    p_uart_recv = multiprocessing.Process(target=uart_recv, args=(serial_buffer_read, preamble))
    p_buffer_to_frame = multiprocessing.Process(target=buffer_to_frame, args=(serial_buffer_read, buffer_frame))
    p_plot_frame = multiprocessing.Process(target=plot_frame, args=(buffer_frame, imagearray, num_pixel_assert))
    p_uart_recv.start()
    p_buffer_to_frame.start()
    p_plot_frame.start()

    main(imagearray)
