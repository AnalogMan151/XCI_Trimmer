# XCI_Trimmer
Python3 script to trim and pad XCI ROM files. Works on Windows, Linux, macOS and any OS that can run python3.

```
usage: XCI_Trimmer.py [-h] (-t | -qt | -p) filename

Trim or Pad XCI rom files

positional arguments:
  filename          Path to XCI rom file

optional arguments:
  -h, --help        show this help message and exit
  -t, --trim        Trim excess bytes
  -qt, --quicktrim  Trims without safety check for unexpected game data
  -p, --pad         Restore excess bytes
  ```
