import argparse
import sys
import time
import numpy as np
import serial

from miniscope_io import init_logger

# Parsers for update LED
updateDeviceParser = argparse.ArgumentParser("updateDevice")
updateDeviceParser.add_argument("port", help="serial port")
updateDeviceParser.add_argument("baudrate", help="baudrate")
updateDeviceParser.add_argument("module", help="module to update")
updateDeviceParser.add_argument("value", help="LED value")

def updateDevice():
    '''
    Script to update hardware settings over a generic UART-USB converter.
    This script currently supports updating the excitation LED brightness and electrical wetting lens driver gain.
    Not tested after separating from stream_daq.py.

    Examples
    --------
    >>> updateDevice [COM port] [baudrate] [module] [value]

    ..todo::
        Test to see if changing package structure broke anything.
    '''
    logger = init_logger('streamDaq')

    args = updateDeviceParser.parse_args()
    moduleList = ["LED", "EWL"]

    ledMAX = 100
    ledMIN = 0

    ewlMAX = 255
    ewlMIN = 0

    ledDeviceTag = 0  # 2-bits each for now
    ewlDeviceTag = 1  # 2-bits each for now

    deviceTagPos = 4
    preamblePos = 6

    Preamble = [2, 1]  # 2-bits each for now

    uartPayload = 4
    uartRepeat = 5
    uartTimeGap = 0.01

    try:
        assert len(vars(args)) == 4
    except AssertionError as msg:
        logger.exception("Usage: updateDevice [COM port] [baudrate] [module] [value]")
        raise msg

    try:
        comport = str(args.port)
    except (ValueError, IndexError) as e:
        logger.exception(e)
        raise e

    try:
        baudrate = int(args.baudrate)
    except (ValueError, IndexError) as e:
        logger.exception(e)
        raise e

    try:
        module = str(args.module)
        assert module in moduleList
    except AssertionError as msg:
        err_str = "Available modules:\n"
        for module in moduleList:
            err_str += "\t" + module + '\n'
        logger.exception(err_str)
        raise msg

    try:
        value = int(args.value)
    except Exception as e:
        logger.exception("Value needs to be an integer")
        raise e

    try:
        if module == "LED":
            assert value <= ledMAX and value >= ledMIN
        if module == "EWL":
            assert value <= ewlMAX and value >= ewlMIN
    except AssertionError as msg:
        if module == "LED":
            logger.exception("LED value need to be a integer within 0-100")
        if module == "EWL":
            logger.exception("EWL value need to be an integer within 0-255")
        raise msg

    if module == "LED":
        deviceTag = ledDeviceTag << deviceTagPos
    elif module == "EWL":
        deviceTag = ewlDeviceTag << deviceTagPos

    command = [0, 0]

    command[0] = int(
        Preamble[0] * 2**preamblePos
        + deviceTag
        + np.floor(value / (2**uartPayload))
    ).to_bytes(1, "big")
    command[1] = int(
        Preamble[1] * 2**preamblePos + deviceTag + value % (2**uartPayload)
    ).to_bytes(1, "big")

    # set up serial port
    try:
        serial_port = serial.Serial(
            port=comport, baudrate=baudrate, timeout=5, stopbits=1
        )
    except Exception as e:
        logger.exception(e)
        raise e
    logger.info("Open serial port")

    for uartCommand in command:
        for repeat in range(uartRepeat):
            # read UART data until preamble and put into queue
            serial_port.write(uartCommand)
            time.sleep(uartTimeGap)

    serial_port.close()
    logger.info("\t" + module + ": " + str(value))
    logger.info("Close serial port")
    sys.exit(1)

