# This script updates the Google mobility data for the Canadian health regions
#
# This script should be called for a cron job (using "crontab -e") as:
#
#    bash weather_update_script.sh > stdout_weather_script 2> stderr_weather_script
#
filename="Global_Mobility_Report.csv"
outfilename="mobility.csv"

# Ensure there is no file of this name
rm ${filename}

wget https://www.gstatic.com/covid19/mobility/${filename}

$(which python3) get_google_mobility_data.py

# clean-up temp file
rm ${filename}

# move outfile into data directory
mv ${outfilename} ..
