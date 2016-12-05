#
"""
"""


import ujson
import sys


def set_config(driver_obj, config_dict):
    """
    """

    for key in config_dict:
        try:
            driver_obj.SetParam(key, config_dict[key])
        except:
            pass
