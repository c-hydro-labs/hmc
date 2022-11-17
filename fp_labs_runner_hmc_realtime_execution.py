"""
FP-Labs - Analyzer HMC time-series

__date__ = '20210113'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'fp-labs'

General command line:
python fp_labs_analyzer_hmc_timeseries.py -settings_file configuration.json

Version(s):
20210113 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Libraries
import argparse
import time
import os
import pandas as pd
import numpy as np

from library.jupyter_generic.lib_jupyter_data_io_generic import define_file_path, define_file_template, \
    fill_file_template, create_dframe_ts, get_path_root, get_path_folders, get_folders_time

from library.jupyter_generic.lib_jupyter_utils_io import update_json_file

from library.jupyter_generic.lib_jupyter_data_io_json import read_file_settings
from library.jupyter_generic.lib_jupyter_data_geo_shapefile import read_data_section
from library.jupyter_generic.lib_jupyter_data_io_ascii import read_file_ascii_hydrograph
from library.jupyter_generic.lib_jupyter_plot_realtime import plot_ts_realtime, adjust_ts_realtime, get_info_realtime

# Import coupler and driver classes
from hmc.driver.configuration.drv_configuration_hmc_logging import ModelLogging
from hmc.coupler.cpl_hmc_manager import ModelInitializer, ModelCleaner
from hmc.coupler.cpl_hmc_builder import ModelBuilder
from hmc.coupler.cpl_hmc_runner import ModelRunner
from hmc.coupler.cpl_hmc_finalizer import ModelFinalizer
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main(script_time,
         script_settings_algorithm_default="fp_labs_runner_hmc_algorithm_default.json",
         script_settings_datasets_default='fp_labs_runner_hmc_datasets_default.json',
         script_settings_algorithm_defined="fp_labs_runner_hmc_algorithm_defined.json",
         script_settings_datasets_defined="fp_labs_runner_hmc_datasets_defined.json",
         script_settings_file='fp_labs_runner_hmc_realtime_execution.json'):

    # -------------------------------------------------------------------------------------
    # Variable(s) environment
    folder_home_env = os.path.expanduser('~')
    # -------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------
    # Read data from settings algorithm file
    settings_info = read_file_settings(script_settings_file)

    info_time_run = settings_info['info']['time_run']
    info_domain = settings_info['info']['domain_name']
    info_run_name = settings_info['info']['run_name']

    script_settings_default = define_file_path(settings_info['configuration_info']['default'])
    script_settings_defined = define_file_path(settings_info['configuration_info']['defined'])

    script_datasets_defined = define_file_path(settings_info['datasets_info'])

    # Get filename and folder(s)
    file_path_section_shp = script_datasets_defined['data_static']
    file_path_run_ts_img = script_datasets_defined['run_realtime_ts_images']
    file_path_run_ts_hydro = script_datasets_defined['run_realtime_ts_hydrograph']

    folder_name_dynamic_root = get_path_folders(script_datasets_defined['data_dynamic'])

    # Define filename by template definition(s)
    file_template_filled = define_file_template(
        info_time_run, run_name=info_run_name, domain_name=info_domain, template_default=settings_info['template'])

    script_settings_defined['settings_algorithm'] = fill_file_template(
        script_settings_defined['settings_algorithm'],
        template_filled=file_template_filled, template_default=settings_info['template'])

    script_settings_defined['settings_datasets'] = fill_file_template(
        script_settings_defined['settings_datasets'],
        template_filled=file_template_filled, template_default=settings_info['template'])

    file_path_run_ts_img = fill_file_template(
        file_path_run_ts_img, template_filled=file_template_filled, template_default=settings_info['template'])
    file_path_run_ts_hydro = fill_file_template(
        file_path_run_ts_hydro, template_filled=file_template_filled, template_default=settings_info['template'])

    # Define list of available folders and time(s)
    time_run_available = get_folders_time(folder_name_dynamic_root)

    info_time_run = pd.Timestamp(time_run_available[0])
    info_time_env = info_time_run.strftime("%Y%m%d_%H")

    print(script_settings_defined['settings_algorithm'])
    print(script_settings_defined['settings_datasets'])
    # ------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set environment variables to json settings file(s)
    update_json_file(script_settings_default['settings_algorithm'], script_settings_defined['settings_algorithm'],
                     update_dict={'$ENV_HOME': folder_home_env,
                                  '$ENV_TIME': info_time_env, '$ENV_RUN_NAME': info_run_name})

    update_json_file(script_settings_default['settings_datasets'], script_settings_defined['settings_datasets'],
                     update_dict={'$ENV_HOME': folder_home_env,
                                  '$ENV_TIME': info_time_env, '$ENV_RUN_NAME': info_run_name})
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set logging file
    driver_hmc_logging = ModelLogging(script_settings_algorithm_defined)
    log_stream = driver_hmc_logging.configure_logging()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Configure model initializer class
    driver_hmc_initializer = ModelInitializer(file_algorithm=script_settings_algorithm_defined,
                                              file_datasets=script_settings_datasets_defined, time=info_time_run)

    # Configure algorithm
    time_series_collections, time_info_collections, \
        run_info_collections, run_cline_collections = driver_hmc_initializer.configure_algorithm()

    # Configure ancillary datasets
    ancillary_datasets_collections = driver_hmc_initializer.configure_ancillary_datasets(time_info_collections)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Configure model builder class
    driver_hmc_builder = ModelBuilder(
        obj_geo_reference=driver_hmc_initializer.dset_ref_geo,
        obj_args=driver_hmc_initializer.obj_args,
        obj_run=driver_hmc_initializer.obj_run,
        obj_ancillary=driver_hmc_initializer.obj_ancillary)

    # LIVE PLOT FRAMEWORK
    # Read sections shapefile
    dset_section = read_data_section(file_path_section_shp)

    # Define sections list
    section_list_all = ['_'.join([sec_domain, sec_name]) for sec_name, sec_domain in
                           zip(dset_section['section_name'], dset_section['section_domain'])]

    # Define section groups
    section_n_graph = 10
    section_n_tot = section_list_all.__len__()
    section_range = np.arange(0, section_n_tot, section_n_graph).tolist()
    section_range.append(section_n_tot)
    section_range = sorted(list(set(section_range)))

    section_range_lower = section_range[:-1]
    section_range_upper = section_range[1:]

    # Read hydrograph file
    file_dframe_live = read_file_ascii_hydrograph(file_path_run_ts_hydro, file_columns=section_list_all)

    # Get file information realtime
    time_stamp_min, time_stamp_max = get_info_realtime(file_dframe_live)
    # Adjust file structure realtime
    file_dframe_adjust = adjust_ts_realtime(file_dframe_live, time_series_collections['deterministic'].index)

    # Plot file datasets realtime
    group_str = '01'
    file_path_step_ts_img = file_path_run_ts_img.format(
        time_name=time_stamp_max.strftime('%Y%d%m_%H00'), group_name=group_str)

    section_list_select = section_list_all[20:25]
    file_dframe_select = file_dframe_adjust[section_list_select]
    plot_ts_realtime(file_path_step_ts_img, time_stamp_max, file_dframe_select, fig_jupyter=False)
    ###

    # Configure static datasets
    static_datasets_collections = driver_hmc_builder.configure_static_datasets(ancillary_datasets_collections)
    # Configure dynamic datasets
    forcing_datasets_collections = driver_hmc_builder.configure_dynamic_datasets(
        time_series_collections, time_info_collections, static_datasets_collections, ancillary_datasets_collections)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Configure model runner class
    driver_hmc_runner = ModelRunner(time_info=time_info_collections, run_info=run_info_collections,
                                    command_line_info=run_cline_collections,
                                    obj_args=driver_hmc_initializer.obj_args,
                                    obj_ancillary=driver_hmc_initializer.obj_ancillary)
    # Configure model execution
    driver_hmc_runner.configure_execution(ancillary_datasets_collections)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Configure model finalizer class
    driver_hmc_finalizer = ModelFinalizer(
        collection_dynamic=forcing_datasets_collections,
        obj_geo_reference=driver_hmc_initializer.dset_ref_geo,
        obj_args=driver_hmc_initializer.obj_args,
        obj_run=driver_hmc_initializer.obj_run,
        obj_ancillary=driver_hmc_initializer.obj_ancillary)

    # Configure outcome datasets
    outcome_datasets_collections = driver_hmc_finalizer.configure_dynamic_datasets(
        time_series_collections, time_info_collections, static_datasets_collections, ancillary_datasets_collections)
    # Configure summary datasets
    driver_hmc_finalizer.configure_summary_datasets(
        time_series_collections, time_info_collections, static_datasets_collections, outcome_datasets_collections)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Configure model cleaner class
    driver_hmc_cleaner = ModelCleaner(
        collections_ancillary=ancillary_datasets_collections,
        obj_args=driver_hmc_initializer.obj_args,
        obj_run=driver_hmc_initializer.obj_run,
    )
    # Configure cleaning tmp datasets
    driver_hmc_cleaner.configure_cleaner()
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    time_run = pd.Timestamp('2021-01-22 06:00')

    file_name_algorithm_default = "fp_labs_runner_hmc_algorithm_default.json"
    file_name_datasets_default = "fp_labs_runner_hmc_datasets_default.json"

    main(time_run, file_name_algorithm_default, file_name_datasets_default)
# ----------------------------------------------------------------------------
