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
# Complete library
from library.jupyter_generic.lib_jupyter_data_io_json import read_file_settings, read_file_ts_hydrograph
from library.jupyter_generic.lib_jupyter_data_io_generic import define_file_path, define_file_template, \
    fill_file_template, create_dframe_ts, get_path_root, get_path_folders, get_folders_time

from library.jupyter_generic.lib_jupyter_data_geo_ascii import read_data_grid
from library.jupyter_generic.lib_jupyter_data_geo_shapefile import read_data_section, find_data_section

from library.jupyter_generic.lib_jupyter_data_io_netcdf import read_file_ts_collections

from library.jupyter_generic.lib_jupyter_plot_ts import plot_ts_discharge, plot_ts_forcing
from library.jupyter_generic.lib_jupyter_plot_map import plot_map_terrain
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main(file_name_settings="fp_labs_analyzer_hmc_timeseries.json"):

    # Read data from settings algorithm file
    settings_info = read_file_settings(file_name_settings)

    # Define static and dynamic file path(s)
    file_path_dset_static = define_file_path(settings_info['source']['static'])
    file_path_dset_dynamic = define_file_path(settings_info['source']['dynamic'])
    file_path_dset_plot = define_file_path(settings_info['destination']['plot'])

    # Define dynamic path root
    file_path_dynamic_root = get_path_root(list(file_path_dset_dynamic.values())[0])
    # Define list of available folders and time(s)
    list_folder_dynamic_root = get_path_folders(file_path_dynamic_root)
    list_time_dynamic_root = get_folders_time(list_folder_dynamic_root)

    # Read terrain datasets
    darray_terrain = read_data_grid(file_path_dset_static['terrain'], var_limit_min=0, var_limit_max=None)
    # Read river network datasets
    darray_river_network = read_data_grid(file_path_dset_static['river_network'], var_limit_min=0, var_limit_max=1)
    # Read sections shapefile
    dframe_section = read_data_section(file_path_dset_static['sections'])

    # Get domain, section and time information
    info_section = find_data_section(dframe_section, section_name=settings_info['info']['section_name'],
                                     basin_name=settings_info['info']['basin_name'])
    info_domain = settings_info['info']['domain_name']
    info_time_run = settings_info['time_run']

    # Fill dynamic file path(s)
    file_template_filled = define_file_template(
        info_time_run, section_name=info_section['section_name'], basin_name=info_section['basin_name'],
        domain_name=info_domain, template_default=settings_info['template'])
    file_path_dset_dynamic = fill_file_template(file_path_dset_dynamic,
                                                template_filled=file_template_filled,
                                                template_default=settings_info['template'])
    file_path_dset_plot = fill_file_template(file_path_dset_plot,
                                             template_filled=file_template_filled,
                                             template_default=settings_info['template'])

    # Read collections file path
    dframe_ts_cls, attrs_cls = read_file_ts_collections(file_path_dset_dynamic['time_series_collections'])
    dframe_ts_hydro, attrs_ts = read_file_ts_hydrograph(file_path_dset_dynamic['time_series_hydrograph'])

    # Select variable(s) to plot time-series
    dframe_ts_discharge_obs = create_dframe_ts(dframe_ts_hydro, var_name_in='discharge_observed', var_name_out='discharge_observed')
    dframe_ts_discharge_sim = create_dframe_ts(dframe_ts_hydro, var_name_in='discharge_simulated', var_name_out='discharge_simulated')
    dframe_ts_rain = create_dframe_ts(dframe_ts_cls, var_name_in='rain', var_name_out='rain')
    dframe_ts_sm = create_dframe_ts(dframe_ts_cls, var_name_in='soil_moisture', var_name_out='soil_moisture')

    dframe_ts_airt = create_dframe_ts(dframe_ts_cls, var_name_in='air_temperature', var_name_out='air_temperature')
    dframe_ts_incrad = create_dframe_ts(dframe_ts_cls, var_name_in='incoming_radiation', var_name_out='incoming_radiation')
    dframe_ts_rh = create_dframe_ts(dframe_ts_cls, var_name_in='relative_humidity', var_name_out='relative_humidity')
    dframe_ts_wind = create_dframe_ts(dframe_ts_cls, var_name_in='wind', var_name_out='wind')

    # Plot map terrain with section
    file_name_section_locator = file_path_dset_plot['section_locator']
    plot_map_terrain(file_name_section_locator, darray_terrain, darray_river_network, info_section,
                     mask_terrain=False)

    # Plot ts discharge
    file_name_ts_discharge = file_path_dset_plot['time_series_discharge']
    plot_ts_discharge(file_name_ts_discharge, dframe_ts_discharge_sim, attrs_ts,
                      df_discharge_obs=dframe_ts_discharge_obs, df_rain=dframe_ts_rain,
                      df_soil_moisture=dframe_ts_sm)

    # Plot ts forcing
    file_name_ts_forcing = file_path_dset_plot['time_series_forcing']
    plot_ts_forcing(file_name_ts_forcing,
                    df_rain=dframe_ts_rain, df_airt=dframe_ts_airt, df_incrad=dframe_ts_incrad,
                    df_rh=dframe_ts_rh, df_winds=dframe_ts_wind,
                    attrs_forcing=attrs_ts)

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    file_name_settings_default = "fp_labs_analyzer_hmc_timeseries.json"
    main(file_name_settings_default)
# ----------------------------------------------------------------------------
