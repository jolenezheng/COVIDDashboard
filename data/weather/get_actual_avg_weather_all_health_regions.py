import math
import numpy as np
import pandas as pd
import datetime as dt
import urllib

#=== Get 4-year average for these dates
#      (use average as actual when calculating
#       average for future dates)
date_avg_start = "2010-01-01"
date_avg_end = "2023-01-01"
#date_avg_end = "2023-01-01"

#=== solar angle info
#
# zero angle day (returned to every 4 years)
angle_zeroday = "2017-01-01"
# angle traveled per day (rad)
angle_delta = 2.0*math.pi / 365.25
# half-range over which to average (+/- 20h)
#
#     In the 4 years prior, there will be seven
#     "days" to average/do-regression over, if
#     we choose a range:
#
#          angle +/- <20h in solar angle>
#
angle_averaging_halfrange = 20.0/24.0 * angle_delta

#=== weather download information
#
# e.g., for TORONTO CITY, climate_id = 6158355, the weather
# on 2021-05-01 is found in:
#
#  https://dd.weather.gc.ca/climate/observations/daily/csv/ON/
#            climate_daily_ON_6158355_2021-05_P1D.csv
#
# Note that climate_id is a 7-character string, with numbers
# or capital letters (e.g., 702S006 is Montreal/Pierre Elliot Trudeau)
#
weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/'
def get_weather_file_url(prov_id, climate_id, year, month):
    try:
        # in case it's a non-integer number
        climate_id = int(climate_id)
    except:
        pass
    filename = "climate_daily_" + prov_id + '_' + str(climate_id) \
        + '_' + str(year) + '-' + f"{int(month):02d}" + "_P1D.csv"
    return weather_base_url + prov_id + '/' + filename
# column names are ugly, but they are basically these (temp in C):
weather_cols = ['lon', 'lat', 'station', 'climate_id', 'date', 'year',
                'month', 'day', 'quality', 'temp_max', 'temp_max_flag',
                'temp_min', 'temp_min_flag', 'temp_mean', 'temp_mean_flag',
                'heat_deg_days', 'heat_deg_days_flag',
                'cool_deg_days', 'cool_deg_days_flag',
                'total_rain_mm', 'total_rain_flag',
                'total_snow_cm', 'total_snow_flag',
                'total_precip_mm', 'total_precip_flag',
                'snow_on_ground_cm', 'snow_on_ground_flag',
                'dir_max_gust', 'dir_max_gust_flag',
                'speed_max_gust', 'speed_max_gust_flag']
#=== Health region information file
#
#  cols = [province_name, prov_id, health_region, hr_uid, temp_region,
#          sub_region_2, climate_id, landarea, total_pop, pwpd, pop80,
#          frac80, house, anndeath, prov_pop, geo_code, pop_sparsity]
#
df_hr = pd.read_csv(r'../health_regions_static_data.csv', encoding='Latin-1')

############# Main Code ################

#=== prep dates for looping over all months in range
startdate = dt.datetime.strptime(date_avg_start, "%Y-%m-%d")
enddate = dt.datetime.strptime(date_avg_end, "%Y-%m-%d")
nowdate = dt.datetime.now()
if (nowdate < enddate):
    enddate = nowdate
year_start = startdate.year
year_end = enddate.year
month_start = startdate.month
month_end = enddate.month

#=== Loop over the health regions
for index, row in df_hr.iterrows():
    prov_id = row.prov_id
    climate_ids = [row.climate_id, row.climate_id_alt, row.climate_id_alt2]
    stations = [row.temp_region, row.temp_region_alt, row.temp_region_alt2]
    region = row.health_region
    hr_uid = row.hr_uid
    print("====== " + prov_id + " --- " + region + " (" + str(hr_uid) +  ") ======")
    for i in range(3):
        if (not pd.isnull(climate_ids[i])):
            print("\t", i, stations[i] + " (" + str(climate_ids[i]) + ")")
    #=== create an empty list-of-dataframes to pd.concat(...)
    dfs = []
    startindex = 0
    for y in range(year_start, year_end + 1):
        for m in range(1,13):
            if (
                    #(prov_id == "YT") &
                    (hr_uid == 2407) &                    
                    #True &                    
                    (
                        ( (year_start == year_end) & (m >= month_start) & (m <= month_end) )
                        | ( (year_start != year_end) &
                            ( (y == year_start) & (m >= month_start) )
                            | ( (y == year_end) & (m <= month_end) )
                            | (y not in [year_start, year_end]) )
                    )
            ):
                gotit = False
                #for id in [climate_id, climate_id_alt, climate_id_alt2]:
                for i in range(3):
                    try:
                        print(i, end=' ')
                        id = climate_ids[i]
                        station = stations[i]
                        if (str(id) == "6105978"):
                            # for Outaouis, QC allow Ottawa weather station
                            url = get_weather_file_url('ON', id, y, m)
                        else:
                            url = get_weather_file_url(prov_id, id, y, m)                        
                        # Read in file
                        df = pd.read_csv(url, encoding='Latin-1')
                        gotit=True
                        outfile = "climate_id/" + prov_id + '_' + str(id) + ".csv"
                        print(url)
                        break
                    except(urllib.error.HTTPError):
                        #print("\tData not found in " + station + " (" + str(id) + ")")
                        pass
                if gotit:
                    # Rename columns and get a YYYY-mm-dd date string
                    df.columns = weather_cols
                    df['monthstr'] = df['month'].astype(str).str.zfill(2)
                    df['daystr'] = df['day'].astype(str).str.zfill(2)                
                    df['datestr'] = \
                        df['year'].astype(str) + '-' + df['monthstr'] \
                        + '-' + df['daystr']
                    # Keep only [date, temp_mean, temp_min, temp_max]
                    df = df[['datestr', 'temp_mean', 'temp_min', 'temp_max']]
                    df.columns = ['date', 'temp_mean', 'temp_min', 'temp_max']
                    # Append to list of dataframes
                    dfs.append(df)
                else:
                    print("\n**** ERROR ****  Data not found for ",
                          prov_id, region, str(y) + '-' + str(m) + "\n")

