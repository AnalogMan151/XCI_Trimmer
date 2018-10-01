#!/usr/bin/env python3
# Author: AnalogMan
# Thanks to Destiny1984 (https://github.com/Destiny1984)
# Modified Date: 2018-06-11
# Purpose: Trims or pads extra bytes from XCI files

import os
import hashlib
import argparse
from shutil import copyfile

# Global variables
filename = ""
ROM_size = 0
padding_offset = 0
filesize = 0
cartsize = 0
copy_bool = False

# Retrieve N bytes of data in little endian from passed data set starting at passed offset
def readLE(data, offset, n):
    return (int.from_bytes(data[offset:offset+(n)], byteorder='little'))

# Obtain expected ROM size and game data size (in GiB) from XCI header along with address padding begins
def getSizes():
    ROM_size = 0
    Data_size = 0.0
    padding_offset = 0

    with open(filename, 'rb') as f:
        XCI = f.read(512)
        cart_size = readLE(XCI, 0x10D, 1)
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

# Check if file is already trimmed. If not, verify padding has no unexpected data. If not, truncate file at padding address
def trim():
    global filename
    pad_check = bytearray(b'\xFF' * (100 * 1024 * 1024))
    pad_remainder = bytearray()

    if filesize == padding_offset:
        print('ROM is already trimmed')
        return

    print('Checking for data in padding...')

    i = cartsize - padding_offset
    chunks = int(i/(100 * 1024 * 1024))
    remainder = i - (chunks * (100 * 1024 * 1024))
    pad_remainder += b'\xFF' * remainder

    with open(filename, 'rb') as f:
        f.seek(padding_offset)
        for _ in range(chunks):
            pad = f.read(100 * 1024 * 1024)
            if pad != pad_check:
                print('Unexpected data found in padding! Aborting Trim.')
                return
        pad = f.read(remainder)
        if pad != pad_remainder:
            print('Unexpected data found in padding! Aborting Trim.')
            return

    print('Trimming {:s}...\n'.format(filename))

    if copy_bool:
        copypath = filename[:-4] + '_trimmed.xci'
        copyfile(filename, copypath)
        filename = copypath

    with open(filename, 'r+b') as f:
        f.seek(padding_offset)
        f.truncate()

# Check if file is already padded. If not, check if copy file flag is set and copy file if so. Add padding to end of file until file reached cart size
def pad():
    global filename

    padding = bytearray(b'\xFF' * (100 * 1024 * 1024))
    pad_remainder = bytearray()

    print('Padding {:s}...\n'.format(filename))

    if filesize == cartsize:
        print('ROM is already padded')
        return

    if copy_bool:
        copypath = filename[:-4] + '_padded.xci'
        copyfile(filename, copypath)
        filename = copypath

    i = cartsize - filesize
    chunks = int(i/(100 * 1024 * 1024))
    remainder = i - (chunks * (100 * 1024 * 1024))
    pad_remainder += b'\xFF' * remainder

    with open(filename, 'ab') as f:
        for _ in range(chunks):
            f.write(padding)
        f.write(pad_remainder)


# if rom is trimmed, output md5 hash of both trimmed and padded rom
def md5sum(block_size=2**20):

    trimmed = False
    if filesize < cartsize:
        trimmed = True

    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        data = f.read(block_size)
        while data:
            md5.update(data)
            data = f.read(block_size)
    hash = md5.hexdigest()

    suffix = ''
    if trimmed:
        padding = bytearray(b'\xFF' * block_size)
        pad_remainder = bytearray()

        i = cartsize - filesize
        chunks = int(i/block_size)
        remainder = i - (chunks * block_size)
        pad_remainder += b'\xFF' * remainder

        for _ in range(chunks):
            md5.update(padding)
        md5.update(pad_remainder)

        suffix = ' // trim size: {}'.format(filesize)
        print('{}  {}{}'.format(hash, filename, suffix))

        suffix = ' // cart size: {}'.format(cartsize)
        hash = md5.hexdigest()

    print('{}  {}{}'.format(hash, filename, suffix))


def main():

    # Arg parser for program options
    parser = argparse.ArgumentParser(description='Trim or Pad XCI rom files')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('filename', help='Path to XCI rom file')
    group.add_argument('-t', '--trim', action='store_true', help='Trim excess bytes')
    group.add_argument('-p', '--pad', action='store_true', help='Restore excess bytes')
    group.add_argument('-m', '--md5', action='store_true', help='Compute md5 hash')
    parser.add_argument('-c', '--copy', action='store_true', help='Creates a copy instead of modifying original file')

    # Check passed arguments
    args = parser.parse_args()

    # Check if required files exist
    if os.path.isfile(args.filename) == False:
        print('ROM cannot be found\n')
        return 1

    global filename, ROM_size, padding_offset, filesize, cartsize, copy_bool
    filename = args.filename

    ROM_size, Data_size, padding_offset = getSizes()

    # If ROM_size does not match one of the expected values, abort
    if ROM_size == 0:
        print('Could not determine ROM size. Sizes supported: 2G, 4G, 8G, 16G, 32G\n')
        return 1

    filesize = os.path.getsize(filename)
    cartsize = (ROM_size * 1024 - (ROM_size * 0x48)) * 1024 * 1024

    # If filesize is too small or too large, abort
    if filesize < padding_offset or filesize > cartsize:
        print('ROM is improperly trimmed or padded. Aborting.\n')
        return 1

    # mimic output of md5sum on linux
    if args.md5:
        md5sum()
        return

    print('\n========== XCI Trimmer ==========\n')
    print('ROM  Size:     {:5d} GiB'.format(ROM_size))
    print('Trim Size:     {:5.2f} GiB\n'.format(Data_size))

    if args.copy:
        copy_bool = True
    if args.trim:
        trim()
    if args.pad:
        pad()

    print('Done!\n')

if __name__ == "__main__":
    main()
