"""
FP-Labs - Analyzer HMC maps

__date__ = '20210113'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'fp-labs'

General command line:
python fp_labs_analyzer_hmc_maps.py -settings_file configuration.json

Version(s):
20210113 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
from library.jupyter_generic.lib_jupyter_data_io_json import read_file_settings
from library.jupyter_generic.lib_jupyter_data_io_generic import define_file_path, define_file_template, fill_file_template, \
    create_darray_maps, define_file_var, create_time_range, validate_time_step, organize_file_template, \
    get_path_root, get_path_folders, get_folders_time

from library.jupyter_generic.lib_jupyter_data_geo_ascii import read_data_grid
from library.jupyter_generic.lib_jupyter_data_geo_shapefile import read_data_section

from library.jupyter_generic.lib_jupyter_data_io_netcdf import read_file_maps

from library.jupyter_generic.lib_jupyter_plot_map import plot_map_terrain, plot_map_var
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main(file_name_settings="fp_labs_analyzer_hmc_maps.json"):

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
    darray_map_terrain = read_data_grid(file_path_dset_static['terrain'], var_limit_min=0, var_limit_max=None)
    # Read river network datasets
    darray_map_river_network = read_data_grid(file_path_dset_static['river_network'], var_limit_min=0, var_limit_max=1)
    # Read sections shapefile
    dframe_section = read_data_section(file_path_dset_static['sections'])

    # Get domain, time and variable(s) information
    info_domain = settings_info['info']['domain_name']
    info_time_run = settings_info['time']['time_run']
    info_time_range_stamp, info_time_range_string = create_time_range(
        info_time_run,
        time_obs_period=settings_info['time']['time_observed_period'],
        time_obs_freq=settings_info['time']['time_observed_frequency'])

    info_time_analysis = settings_info['time']['time_analysis']
    info_var_list_forcing_obs_ws = settings_info['info']['var_list_forcing_obs_ws']
    info_var_list_outcome = settings_info['info']['var_list_outcome']

    # Validate time analysis
    valid_time_analysis = validate_time_step(info_time_analysis, info_time_range)

    # Fill dynamic file path(s)
    file_path_dset_dynamic_collections = {}
    file_path_dset_plot_collections = {}
    for info_time_step in info_time_range_stamp:

        string_time_step = info_time_step.strftime('%Y-%m-%d %H:00')

        file_template_filled = define_file_template(info_time_run, info_time_step,
                                                    domain_name=info_domain, template_default=settings_info['template'])
        file_path_dset_dynamic_filled = fill_file_template(file_path_dset_dynamic,
                                                    template_filled=file_template_filled,
                                                    template_default=settings_info['template'])
        file_path_dset_plot_filled = fill_file_template(file_path_dset_plot,
                                                 template_filled=file_template_filled,
                                                 template_default=settings_info['template'])

        file_path_dset_dynamic_collections[string_time_step] = file_path_dset_dynamic_filled
        file_path_dset_plot_collections[string_time_step] = file_path_dset_plot_filled

    file_name_forcing_obs_ws_list, file_time_forcing_obs_ws_list = organize_file_template(
        file_path_dset_dynamic_collections, file_dataset_tag='maps_forcing_obs_ws')

    file_name_outcome_list, file_time_outcome_list = organize_file_template(
        file_path_dset_dynamic_collections, file_dataset_tag='maps_outcome')

    # Read maps forcing and outcome datasets
    dset_maps_forcing_obs_ws_collections = read_file_maps(
        file_name_forcing_obs_ws_list, file_time_forcing_obs_ws_list,
        file_vars_list_select=info_var_list_forcing_obs_ws)
    dset_maps_outcome_collections = read_file_maps(
        file_name_outcome_list, file_time_outcome_list,
        file_vars_list_select=info_var_list_outcome)

    # Select variable(s) to plot time-series
    darray_map_rain, attrs_map_rain = create_darray_maps(
        dset_maps_forcing_obs_ws_collections,
        var_time=info_time_analysis, var_name_in='Rain', var_name_out='rain')
    darray_map_airt, attrs_map_airt = create_darray_maps(
        dset_maps_forcing_obs_ws_collections,
        var_time=info_time_analysis, var_name_in='Air_Temperature', var_name_out='air_temperature')
    darray_map_rh, attrs_map_rh = create_darray_maps(
        dset_maps_forcing_obs_ws_collections,
        var_time=info_time_analysis, var_name_in='Relative_Humidity', var_name_out='relative_humidity')

    darray_map_sm, attrs_map_sm = create_darray_maps(
        dset_maps_outcome_collections,
        var_time=info_time_analysis, var_name_in='SM', var_name_out='soil_moisture')
    darray_map_lst, attrs_map_lst = create_darray_maps(
        dset_maps_outcome_collections,
        var_time=info_time_analysis, var_name_in='LST', var_name_out='land_surface_temperature')

    # Plot map soil moisture
    file_name_map_sm = define_file_var(file_path_dset_plot_collections, file_time=info_time_analysis,
                                       var_name='soil_moisture', dataset_name='maps_outcome')
    plot_map_var(file_name_map_sm, darray_map_sm, info_time_analysis,
                 var_name_data='soil_moisture', var_units='[-]', var_name_geo_x='Longitude', var_name_geo_y='Latitude',
                 var_limit_min=0, var_limit_max=1)
    # Plot map air temperature
    file_name_map_airt = define_file_var(file_path_dset_plot_collections, file_time=info_time_analysis,
                                         var_name='air_temperature', dataset_name='maps_forcing_obs_ws')
    plot_map_var(file_name_map_airt, darray_map_airt, info_time_analysis,
                 var_name_data='air_temperature', var_units='[C]', var_name_geo_x='longitude', var_name_geo_y='latitude')

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    file_name_settings_default = "fp_labs_analyzer_hmc_maps.json"
    main(file_name_settings_default)
# ----------------------------------------------------------------------------
