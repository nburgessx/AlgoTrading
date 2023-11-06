# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24 06:40:16 2023

@author: nburgessx
"""

import ibapi as ib

print(ib.__version__)
print(dir(ib))

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
import time
from datetime import datetime


