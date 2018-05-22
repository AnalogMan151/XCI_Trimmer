#!/usr/bin/env python3
# Author: AnalogMan
# Thanks to Destiny1984 (https://github.com/Destiny1984)
# Modified Date: 2018-05-22
# Purpose: Trims or pads extra bytes from XCI files

import os
import argparse

filename = ""
ROM_size = 0
padding_offset = 0

def readBE(data, offset, n):
    return (int.from_bytes(data[offset:offset+(n)], byteorder='big'))

def readLE(data, offset, n):
    return (int.from_bytes(data[offset:offset+(n)], byteorder='little'))

def getSizes():
    ROM_size = 0
    Data_size = 0.0
    padding_offset = 0
    with open(filename, 'rb') as f:
        XCI = f.read(512)
        cart_size = readBE(XCI, 0x10C, 2)
        if cart_size == 0xF8:
            ROM_size = 2
        elif cart_size == 0xF0:
            ROM_size = 4
        elif cart_size == 0xE0:
            ROM_size = 8
        elif cart_size == 0xE1:
            ROM_size = 16
        elif cart_size == 0xE2:
            ROM_size = 32
        else:
            ROM_size = 0
        padding_offset = (readLE(XCI, 0x118, 4) * 512) + 512
        Data_size = padding_offset / (1024 * 1024 * 1024)

    return ROM_size, Data_size, padding_offset


def trim():
    print('Checking for data in padding...')
    with open(filename, 'rb') as f:
        f.seek(padding_offset)
        while True:
            b = f.read(1)
            if not b:
                # eof
                break
            if b != b'\xFF':
                print('Unexpected data found in padding! Aborting Trim.')
                return
    quicktrim()

def quicktrim():
        print('Trimming {:s}...\n'.format(filename))
        with open(filename, 'r+b') as f:
            f.seek(padding_offset)
            f.truncate()

def pad():
    padding = bytearray()
    print('Padding {:s}...\n'.format(filename))
    i = ((ROM_size * 1024 - (ROM_size * 0x48)) * 1024 * 1024) - padding_offset
    with open(filename, 'ab') as f:
        if f.tell() > padding_offset:
            print('ROM is already padded')
            return
        padding += b'\xFF' * i
        f.write(padding)
            
def main():
    print('\n========== XCI Trimmer ==========\n')

    # Arg parser for program options
    parser = argparse.ArgumentParser(description='Trim or Pad XCI rom files')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('filename', help='Path to XCI rom file')
    group.add_argument('-t', '--trim', action='store_true', help='Trim excess bytes')
    group.add_argument('-qt', '--quicktrim', action='store_true', help='Trims without safety check for unexpected game data')
    group.add_argument('-p', '--pad', action='store_true', help='Restore excess bytes')

    # Check passed arguments
    args = parser.parse_args()

    # Check if required files exist
    if os.path.isfile(args.filename) == False:
        print('ROM cannot be found\n')
        return 1
    
    global filename, ROM_size, padding_offset
    filename = args.filename

    ROM_size, Data_size, padding_offset = getSizes()
    if ROM_size == 0:
        print('Could not determine ROM size. Sizes supported: 2G, 4G, 8G, 16G, 32G\n')
        return 1

    print('ROM  Size:     {:5d} GiB'.format(ROM_size))
    print('Trim Size:     {:5.2f} GiB\n'.format(Data_size))
    
    if args.trim:
        trim()
    if args.quicktrim:
        quicktrim()
    if args.pad:
        pad()

    print('Done!\n\n')

if __name__ == "__main__":
    main()
