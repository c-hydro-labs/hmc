"""
Library Features:

Name:          lib_jupyter_data_io_netcdf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os

import xarray as xr
import pandas as pd

from library.jupyter_generic.lib_jupyter_utils_system import get_dict_values, fill_tags2string
from library.jupyter_generic.lib_jupyter_info_args import logger_name, zip_extension
from library.jupyter_generic.lib_jupyter_utils_io import unzip_filename

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################
'SM', 'LST', 'Rain', 'AirTemperature', 'Wind', 'RelHumidity', 'IncRadiation' 'times'


# -------------------------------------------------------------------------------------
# Method to read netcdf maps file
def read_file_maps(file_name, file_time, file_vars_list_select=None, format_time='%Y-%m-%d %H:00'):

    if isinstance(file_name, str):
        file_name_list = [file_name]
    else:
        file_name_list = file_name

    if isinstance(file_time, str):
        file_time_list = [file_time]
    else:
        file_time_list = file_time

    file_name_unzip_list = []
    file_time_unzip_list = []
    for file_time_step, file_name_step in zip(file_time_list, file_name_list):
        if os.path.exists(file_name_step):
            if file_name_step.endswith(zip_extension):
                file_name_step_zip = file_name_step
                file_name_step_unzip = file_name_step.replace(zip_extension, '')
                unzip_filename(file_name_step_zip, file_name_step_unzip)
            else:
                file_name_step_unzip = file_name_step

            file_name_unzip_list.append(file_name_step_unzip)
            file_time_unzip_list.append(file_time_step)
        else:
            raise IOError('File ' + file_name_step + ' not found!')

    file_data_collections = {}
    for file_time_unzip_step, file_name_unzip_step in zip(file_time_unzip_list, file_name_unzip_list):

        file_handle = xr.open_dataset(file_name_unzip_step)
        file_vars_list_all = list(file_handle.data_vars)

        if file_vars_list_select is None:
            file_vars_list_select = file_vars_list_all

        file_vars_search = [var_step for var_step in file_vars_list_select if var_step in file_vars_list_all]
        dset_vars_search = file_handle[file_vars_search]

        file_data_collections[file_time_unzip_step] = dset_vars_search

    return file_data_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read netcdf time-series file
def read_file_ts_collections(file_name,
                             tag_rain_in='Rain', tag_rain_out='rain',
                             tag_air_temperature_in='AirTemperature', tag_air_temperature_out='air_temperature',
                             tag_wind_speed_in='Wind', tag_wind_speed_out='wind',
                             tag_relative_humidity_in='RelHumidity', tag_relative_humidity_out='relative_humidity',
                             tag_incoming_radiation_in='IncRadiation', tag_incoming_radiation_out='incoming_radiation',
                             tag_soil_moisture_in='SM', tag_soil_moisture_out='soil_moisture',
                             tag_lst_in='LST', tag_lst_out='land_surface_temperature',
                             tag_times_in='times', tag_time_out='time',
                             tag_index='time'):

    if os.path.exists(file_name):
        file_dset = xr.open_dataset(file_name)

    else:
        raise IOError('File ' + file_name + ' not found!')

    variable_list_in = [tag_times_in, tag_rain_in, tag_air_temperature_in,
                        tag_wind_speed_in, tag_relative_humidity_in, tag_incoming_radiation_in,
                        tag_soil_moisture_in, tag_lst_in]
    variable_list_out = [tag_time_out, tag_rain_out, tag_air_temperature_out,
                         tag_wind_speed_out, tag_relative_humidity_out, tag_incoming_radiation_out,
                         tag_soil_moisture_out, tag_lst_out]

    variable_list_file = list(file_dset.data_vars)

    file_data_dict = {}
    for var_name_in, var_name_out in zip(variable_list_in, variable_list_out):
        if var_name_in in variable_list_file:
            if var_name_out == tag_time_out:
                var_values = pd.DatetimeIndex(file_dset[var_name_in].values)
            else:
                var_values = file_dset[var_name_in].values
            file_data_dict[var_name_out] = var_values

    file_data_df = pd.DataFrame(data=file_data_dict)
    if tag_index in list(file_data_df.columns):
        file_data_df.set_index(tag_index, inplace=True)
    file_data_attrs = file_dset.attrs

    return file_data_df, file_data_attrs
# -------------------------------------------------------------------------------------

# Method to read file outcome gridded
def read_file_gridded_outcome(file_name):
    pass