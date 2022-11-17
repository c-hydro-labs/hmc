#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='FP LABS - MANAGER - HMC NOTEBOOK DATASETS'
script_version="1.0.0"
script_date='2021/01/12'

# Get information of model execution
time_run="2021-01-28 12:22"
time_period=0 # run hour(s)

# Server remote settings (user and password are stored in .netrc file)
server_remote_name="server_hydro_marche"
server_remote_ip="10.198.26.21"
server_remote_user=$(awk '/'${server_remote_name}'/{getline; print $4}' ~/.netrc)
server_remote_password=$(awk '/'${server_remote_name}'/{getline; print $6}' ~/.netrc)
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Folder of remote and local machine(s)
folder_datasets_tag_list=(
    "STATIC DATA"
    "DYNAMIC DATA OUTCOME == WEATHER STATION REALTIME [ALL]"
    "DYNAMIC DATA SOURCE OBS == GROUND NETWORK == WEATHER STATION"
    "DYNAMIC DATA SOURCE OBS == GROUND NETWORK == RIVER STATION"
    "DYNAMIC DATA SOURCE OBS == SATELLITE == MODIS"
    "DYNAMIC DATA STATE/RESTART == WEATHER STATION REALTIME [GRIDDED]"
    "DYNAMIC DATA STATE/RESTART == WEATHER STATION REALTIME [POINT]"
)
folder_datasets_remote_list_raw=(
    "/hydro/data/data_static" 
    "/hydro/archive/weather_stations_realtime/%YYYY/%mm/%dd/%HH/"
    "/hydro/data/data_dynamic/outcome/obs/weather_stations/%YYYY/%mm/%dd/"
    "/hydro/data/data_dynamic/outcome/obs/river_stations/%YYYY/%mm/%dd/"
    "/hydro/data/data_dynamic/outcome/obs/satellite/modis/%YYYY/%mm/%dd/"
    "/hydro/archive/model_dset_restart/gridded/"
    "/hydro/archive/model_dset_restart/point/"
)
folder_datasets_local_list_raw=(
    "$HOME/fp_labs_datasets/" 
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_archive/"
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_forcing/ws/"
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_forcing/rs/"
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_forcing/satellite_modis/"
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_restart/"
    "$HOME/fp_labs_datasets/data_dynamic/%YYYY%mm%dd_%HH/data_restart/"
)
file_datasets_raw_list=(
    "ALL"
    "ALL"
    "ws.db.%YYYY%mm%dd%HH00.nc.gz"
    "rs.db.%YYYY%mm%dd%HH00.txt"
    "modis.snow.%YYYY%mm%dd%HH00.nc.gz"
    "hmc.state-grid.%YYYY%mm%dd%HH00.nc.gz"
    "hmc.state-point.%YYYY%mm%dd%HH00.txt"
)

file_extension_excluded_list=(
    "*.workspace*"
    "*.workspace*"
    "*.workspace*"
    "*.workspace*"
    "*.workspace*"
    "*.workspace*"
    "*.workspace*"
)
file_sync_activated_list=(
    true
    true
    true
    true
    true
    true
    true
)
time_period_datasets_list=(
    0
    0
    72
    72
    72
    73
    73
)
#-----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

# Define remote server address
server_remote_address="${server_remote_user}@${server_remote_ip}"

# Connection test
echo " ===> SERVER CONNECTION ... "
if ! sshpass -p ${server_remote_password} ssh ${server_remote_address} exit ; then
    echo " ===> SERVER CONNECTION ... FAILED. EXIT"
    break
else
    echo " ===> SERVER CONNECTION ... DONE"
fi

# Iterate over hours
time_run=$(date -d "$time_run" +'%Y-%m-%d %H:00')
for hour in $(seq 0 $time_period); do
    
    # ----------------------------------------------------------------------------------------
    # Get time run information
    time_step_run=$(date -d "$time_run ${hour} hour ago" +'%Y-%m-%d %H:00')
    
    year_step_run=$(date -u -d "$time_step_run" +"%Y")
    month_step_run=$(date -u -d "$time_step_run" +"%m")
    day_step_run=$(date -u -d "$time_step_run" +"%d")
    hour_step_run=$(date -u -d "$time_step_run" +"%H")
    minute_step_run=$(date -u -d "$time_step_run" +"%M")
    
    # Info time run start
    echo " ===> TIME RUN ${time_step_run} ... "
    # ----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------------
    # Iterate over tags
    for id_tag in "${!folder_datasets_tag_list[@]}"; do
        
        # ----------------------------------------------------------------------------------------
        # Get values of tag(s) and folder(s)        
        folder_tag=${folder_datasets_tag_list[id_tag]}
        folder_datasets_remote_raw=${folder_datasets_remote_list_raw[id_tag]}
        folder_datasets_local_raw=${folder_datasets_local_list_raw[id_tag]}
        file_extension_excluded=${file_extension_excluded_list[id_tag]} 
        
        file_datasets_raw=${file_datasets_raw_list[id_tag]}
        time_period_datasets=${time_period_datasets_list[id_tag]}
        
        file_sync_activated=${file_sync_activated_list[id_tag]} 
        
        # Info tag start
        echo " ====> SYNC DATASETS NAME ${folder_tag} ... "
        # ----------------------------------------------------------------------------------------
        
        # ----------------------------------------------------------------------------------------
        # Create time datasets list
        time_list_datasets=()
        for hour_datasets in $(seq 0 $time_period_datasets); do
            time_step_datasets=$(date -d "$time_step_run ${hour_datasets} hour ago" +'%Y-%m-%d %H:00')
            time_list_datasets+=( "$time_step_datasets" )
        done
        # echo "${time_list_datasets[@]}"
        # ----------------------------------------------------------------------------------------
        
        # ----------------------------------------------------------------------------------------
        # Iterate over time datasets step
        for id_time in "${!time_list_datasets[@]}"; do
            
            # ----------------------------------------------------------------------------------------
            # Get time datasets information
            time_step_datasets=${time_list_datasets[id_time]}
            
            year_step_datasets=$(date -u -d "$time_step_datasets" +"%Y")
            month_step_datasets=$(date -u -d "$time_step_datasets" +"%m")
            day_step_datasets=$(date -u -d "$time_step_datasets" +"%d")
            hour_step_datasets=$(date -u -d "$time_step_datasets" +"%H")
            minute_step_datasets=$(date -u -d "$time_step_datasets" +"%M")
            
            # Info time datasets start
            echo " =====> SYNC DATASETS TIME STEP ${time_step_datasets} ... "
            # ----------------------------------------------------------------------------------------
            
            # ----------------------------------------------------------------------------------------
            # Define remote and local folder(s)
            folder_datasets_remote_step=${folder_datasets_remote_raw/'%YYYY'/$year_step_datasets}
            folder_datasets_remote_step=${folder_datasets_remote_step/'%mm'/$month_step_datasets}
            folder_datasets_remote_step=${folder_datasets_remote_step/'%dd'/$day_step_datasets}
            folder_datasets_remote_step=${folder_datasets_remote_step/'%HH'/$hour_step_datasets}
            folder_datasets_remote_step=${folder_datasets_remote_step/'%MM'/$minute_step_datasets}
	
            folder_datasets_local_step=${folder_datasets_local_raw/'%YYYY'/$year_step_run}
            folder_datasets_local_step=${folder_datasets_local_step/'%mm'/$month_step_run}
            folder_datasets_local_step=${folder_datasets_local_step/'%dd'/$day_step_run}
            folder_datasets_local_step=${folder_datasets_local_step/'%HH'/$hour_step_run}
            folder_datasets_local_step=${folder_datasets_local_step/'%MM'/$minute_step_run}
            
            if [ $file_datasets_raw == "ALL" ]; then
                path_datasets_remote_step=$folder_datasets_remote_step
                path_datasets_local_step=$folder_datasets_local_step
            else
                # Define filename
                file_datasets_step=${file_datasets_raw/'%YYYY'/$year_step_datasets}
                file_datasets_step=${file_datasets_step/'%mm'/$month_step_datasets}
                file_datasets_step=${file_datasets_step/'%dd'/$day_step_datasets}
                file_datasets_step=${file_datasets_step/'%HH'/$hour_step_datasets}
                file_datasets_step=${file_datasets_step/'%MM'/$minute_step_datasets}
                
                path_datasets_remote_step=${folder_datasets_remote_step}${file_datasets_step}
                path_datasets_local_step=${folder_datasets_local_step}${file_datasets_step}
                
            fi
            # ----------------------------------------------------------------------------------------

            # ----------------------------------------------------------------------------------------
            # Define command-line(s)
            cmd_ls="sshpass -p $server_remote_password ssh ${server_remote_address} ls $folder_datasets_remote_step >/dev/null 2>&1"
            cmd_download="sshpass -p $server_remote_password rsync -avr --exclude ${file_extension_excluded} --progress ${server_remote_address}:$path_datasets_remote_step $path_datasets_local_step"
            
            echo " ======> SYNC DATASETS FILES ${path_datasets_remote_step} ... "
            if ${file_sync_activated} ; then
                if ! ${cmd_ls} ; then
                    # Info tag end (skipped)
                    echo " ======> SYNC DATASETS FILES ${path_datasets_remote_step} ... SKIPPED. FOLDER $folder_datasets_remote_step DOES NOT EXIST"
                else
                
                    # Create local folder
                    if [ ! -d "$folder_datasets_local_step" ]; then
                        mkdir -p $folder_datasets_local_step
                    fi
                
                    if ! ${cmd_download} ; then
                        # Info tag end (failed)
                        echo " ======> SYNC DATASETS FILES ${path_datasets_remote_step} ... FAILED. ERRORS IN EXECUTING $cmd_download COMMAND-LINE"
                    else
                        # Info tag end (completed)
                        echo " ======> SYNC DATASETS FILES ${path_datasets_remote_step} ... DONE"
                    fi
                
                fi
            else
                # Info tag end (not activated)
                echo " ======> SYNC DATASETS FILES ${path_datasets_remote_step} ... SKIPPED. RSYNC NOT ACTIVATED"
            fi
            
            echo " =====> SYNC DATASETS TIME STEP ${time_step_datasets} ... DONE"
        
        done
        
        echo " ====> SYNC DATASETS NAME ${folder_tag} ... DONE"
        
    done

    # Info time end
    echo " ===> TIME RUN ${time_step_run} ... DONE"
    # ----------------------------------------------------------------------------------------
    
done

# Info script end
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------


