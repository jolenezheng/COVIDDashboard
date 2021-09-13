# This script updates the Google mobility data for the Canadian health regions
#
# This script should be called for a cron job (using "crontab -e") as:
#
#    bash weather_update_script.sh > stdout_weather_script 2> stderr_weather_script
#
wget https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv

$(which python3) get_google_mobility_data.py
