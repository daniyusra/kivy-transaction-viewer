# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 19:43:02 2020

@author: ASUS
"""

import pandas as pd
import matplotlib as plt
import database_manager

databaseManager = database_manager.DatabaseManager()

print(databaseManager.details_read_all())

a = databaseManager.details_read_all()

print({ b[0]: b[1] for b in a})

del databaseManager