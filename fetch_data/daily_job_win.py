# Workaround for python in windows...
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)

from fetch_data.daily_fetch_forsale import daily_forsale
from fetch_data.daily_fetch_rent import daily_rent

if __name__ == '__main__':
    daily_forsale()
    daily_rent()
