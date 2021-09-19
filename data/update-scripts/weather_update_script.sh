# This script:
#   (1) updates the raw data for this month and the previous month (to get
#       the last couple of days, taking into account that the month might change),
#       and then
#   (2) re-does the full interpolation and averaging of the raw data to create the
#       static temperature files used in the dashboard.
#
# The first step takes about 1 minute to run (on Ben's computer), and the second
# step takes about 6 minutes to run.
#
# This entire script should be called for a cron job (using "crontab -e") as:
#
#    bash weather_update_script.sh > stdout_weather_script 2> stderr_weather_script
#

cd ../weather

$(which python3) get_actual_avg_weather_all_health_regions.py update_raw_data_two_months && \
    $(which python3) get_actual_avg_weather_all_health_regions.py create_actual_avg_all 
