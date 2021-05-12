import os
import sys
import math
import numpy as np
import pandas as pd
import datetime as dt
import urllib

commandline = True  # if False, specify runmode options below

# also, must specify start/end dates within the code (see below)

#============================================================#
#              run mode and run mode options                 #
#============================================================#
# runmode choices:
#
#     download_raw_all, download_raw_one_province,
#     download_raw_one_hr,
#
#     create_actual_avg_all, create_actual_avg_one_hr,
#
#     update_raw_data_two_months
#
# For:
#     * downloading the raw data
#     * creating the interpolated and future-averaged data files
#     * updating with most recent dates
#
def print_help_and_exit():
    print("\nCommandline options are:\n\n"
          + "\t <scriptname> download_raw_all\n"
          + "\t <scriptname> create_actual_avg_all\n"
          + "\t <scriptname> update_raw_data_two_months\n"
          + "\t <scriptname> download_raw_one_province <prov_abb>\n"
          + "\t <scriptname> download_raw_one_hr <hr_uid>\n"
          + "\t <scriptname> create_actual_avg_one_hr <hr_uid>\n\n"
          + "The start and end dates for raw data collection and "
          + "final output are set within the script.\n")
    exit(0)
if commandline:
    #=== Parse the command-line options
    if (len(sys.argv) == 1):
        print_help_and_exit()
    elif (len(sys.argv) == 2):
        if sys.argv in ['h', '-h', 'help', '--help']:
            print_help_and_exit()
        runmode = sys.argv[1]
        if runmode not in ["download_raw_all", "create_actual_avg_all",
                           "update_raw_data_two_months"]:
            print("\n***Error: Unless doing \"all\", you must specify the"
                  + " province abbrev or hr_uid as a second argument\n")
            exit(0)
    else:
        runmode = sys.argv[1]
        par = sys.argv[2]
        try:
            selected_hruid = int(par)
            if runmode not in ['download_raw_one_hr',
                               'create_actual_avg_one_hr']:
                print("\n***Error: hr_uid is to be used with either "
                      + "\'download_raw_one_hr\' or \'create_actual_avg_one_hr\'\n")
                sys.exit(1)
            print(f"***Warning: assuming {selected_hruid:d} is the hr_uid.")
        except SystemExit:
            sys.exit(2)
        except:
            selected_province_abb = par.upper()
            if selected_province_abb \
               not in ['AB', 'BC', 'MB', 'NB', 'NL', 'NS',
                       'NU', 'NT', 'ON', 'PE', 'QC', 'SK', 'YT']:
                print("\n***Error: Province abbreviation not recognized.\n")
                exit(0)
            elif (runmode != "download_raw_one_province"):
                print("\n***Error: Province abbreviation is to be used with "
                      + "\'download_raw_one_province\'\n")
                exit(0)
            print(f"***Warning: assuming " + par + " is a province abbreviation "
                  + "for running \'download_raw_one_province\'\n")
else:
    #=== Not assuming commandline options, just specify manually here
    runmode = "create_actual_avg_all"
    selected_province_abb = 'SK'          # for runmode=download_raw/create_province
    selected_hruid = 592                 # for runmode=download_raw/create_hr

#=== download mode options
#
# Dates to download raw data
#
#   *** Note ***  These dates are also used to specify
#                 the raw-data file for "create".
#
download_raw_date_start = "2016-01-01"
download_raw_date_end = "2023-01-01"     # if a future date, will stop at "now"
#=== create mode options
#
# Dates to start and end interpolation and averaging
#      (also adjust download_raw dates above...
#       need data from 4-y prior to create_date_start)
create_date_start = "2020-01-01"
create_date_end = "2023-01-01"
create_no_averaging = False    # if True, just make an interpolated file of actual data

#=== Health region static information file
#
#  cols = [province_name, prov_id, health_region, hr_uid, temp_region,
#          sub_region_2, climate_id, landarea, total_pop, pwpd, pop80,
#          frac80, house, anndeath, prov_pop, geo_code, pop_sparsity]
#
df_hr_static = pd.read_csv(r'../health_regions_static_data.csv', encoding='Latin-1')

#============================================================#
#              downloading raw temperature data              #
#============================================================#
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

#=== dealing with missing days
nmissing_tol = 5  # number of missing days to tolerate (accept such a file)
nmissing_accept = 20 # number of missing day to accept (if no other choice)
def fall_back_to_best(missing, saved_dfs, saved_urls, climate_ids):
    val, idx = min((val,idx) for (idx, val) in enumerate(missing))
    if (val <= nmissing_accept):
        df = saved_dfs[idx]
        cid = climate_ids[idx]
        df.columns = weather_cols
        print(idx, saved_urls[idx])
        gotit = True
    else:
        df = {}
        cid = -1
        gotit = False
    return df, cid, gotit

class DataMissingException(Exception):
    pass

#=== setting dates for downloads and download directories
def prep_for_download(date_start, date_end, no_create_outdir=False):
    # Set up dates for downloading
    nowdate, year_start, year_end, month_start, month_end, year_end_file, month_end_file = \
            prep_dates_for_downloading(date_start, date_end)
    # Prepare outfile directory
    outdir = base_raw_outdir \
        + f"{year_start:d}-{month_start:02d}_{year_end_file:d}-{month_end_file:02d}"
    if no_create_outdir:
        outdir = outdir + '/'
    else:
        # Check to see if it exists and create new (possibly unique) directory if not
        outdir = create_outdir(outdir, nowdate)
    return nowdate, year_start, year_end, month_start, month_end, outdir

def prep_dates_for_downloading(date_start, date_end):
    startdate = dt.datetime.strptime(date_start, "%Y-%m-%d")
    enddate = dt.datetime.strptime(date_end, "%Y-%m-%d")
    # let the directory name be matched to the requested date range
    year_end_file = enddate.year
    month_end_file = enddate.month
    nowdate = dt.datetime.now()
    if (nowdate < enddate):
        enddate = nowdate
    year_start = startdate.year
    year_end = enddate.year
    month_start = startdate.month
    month_end = enddate.month
    return nowdate, year_start, year_end, month_start, month_end, year_end_file, month_end_file

#=== Directory for storing downloaded raw data
base_raw_outdir = "all_health_regions_raw_temperature_files/"
prompt_user_to_overwrite_directory_data = False
noprompt_overwrite_directory_data = True  # otherwise create unique name
# output column names
raw_data_columns = np.array(['date', 'temp_mean', 'temp_min', 'temp_max', 'climate_id'])

def make_new_unique_outdir(outdir, nowdate):
    nowtime_str = nowdate.strftime("%Y-%m-%d_%H-%M")
    outdir = outdir + '_' + nowtime_str + '/'
    os.mkdir(outdir)
    return outdir

def create_outdir(outdir, nowdate):
    # check if directory exists
    if os.path.isdir(outdir):
        if prompt_user_to_overwrite_directory_data:
            while True:
                response = input("The directory:\n\t" + outdir
                                 + "\nalready exists.  Do you want to overwrite these files? (y/n)\n")
                if (response.capitalize() == 'Y'):
                    outdir = outdir + '/'
                    break
                elif (response.capitalize() == 'N'):
                    # if user doesn't want to overwrite, make a new unique outdir
                    outdir = make_new_unique_outdir(outdir, nowdate)                    
                    break
                else:
                    print("You must input y/n.")
        else:
            if noprompt_overwrite_directory_data:
                outdir = outdir + '/'
            else:
                outdir = make_new_unique_outdir(outdir, nowdate)
    else:
        # if directory does not exist, make the outfile directory
        outdir = outdir + '/'
        os.mkdir(outdir)
    return outdir

def get_endofmonth(year, month):
    if month in [9, 4, 6, 11]:
        endofmonth = 30
    elif month in [1, 3, 5, 7, 8, 10, 12]:
        endofmonth = 31
    else:
        if ( (year % 4) == 0 ):
            endofmonth = 29
        else:
            endofmonth = 28
    return endofmonth

#=== main download function for one health region over many dates
def download_monthly_data_and_write_to_file(year_start, year_end,
                                            month_start, month_end,
                                            prov_id, climate_ids, stations,
                                            region, hr_uid, outdir,
                                            write_to_file=True):
    # Print out all stations for this health region
    for i in range(3):
        if (not pd.isnull(climate_ids[i])):
            print("\t", i, stations[i] + " (" + str(climate_ids[i]) + ")")
    # Create an empty list-of-dataframes to pd.concat(...)
    dfs = []
    startindex = 0
    for y in range(year_start, year_end + 1):
        for m in range(1,13):
            if (
                    ( (year_start == year_end)
                      & (m >= month_start) & (m <= month_end) )
                    | ( (year_start != year_end) &
                        ( ( (y == year_start) & (m >= month_start) )
                          | ( (y == year_end) & (m <= month_end) )
                          | (y not in [year_start, year_end]) ) )
            ):
                gotit = False
                # Try up to three weather stations to get data for YYYY-mm
                missing = [40,40,40]
                saved_dfs = []
                saved_urls = []
                for i in range(3):
                    try:
                        print(i, end=' ')
                        cid = climate_ids[i]
                        station = stations[i]
                        if (str(cid) == "6105978"):
                            # for Outaouis, QC allow Ottawa weather station
                            url = get_weather_file_url('ON', cid, y, m)
                        elif (str(cid) == "7056616"):
                            # for Edmundston, NB, allow this QC weather station
                            url = get_weather_file_url('QC', cid, y, m)
                        else:
                            url = get_weather_file_url(prov_id, cid, y, m)                        
                        # Read in file
                        df = pd.read_csv(url, encoding='Latin-1')
                        saved_dfs.append(df)
                        saved_urls.append(url)
                        df.columns = weather_cols
                        nmissing = len(df) - df['temp_mean'].count()
                        missing[i] = nmissing
                        if (nmissing > nmissing_tol):
                            raise DataMissingException()
                        gotit=True                        
                        print(url)
                        break
                    except(urllib.error.HTTPError):
                        # append an empty dataframe and blank url
                        saved_dfs.append(pd.DataFrame({'A' : []}))
                        saved_urls.append("")
                        print("\tFile not found for" , station,
                              "(" + str(cid) + ")", f"in {y:d}-{m:02d}")
                        # last chance: if there is a file with some data... use it
                        if (i == 2):
                            [df, cid, gotit] = fall_back_to_best(missing, saved_dfs,
                                                                 saved_urls, climate_ids)
                    except(DataMissingException):
                        print(f"\tMissing {nmissing:d} entries for temp_mean at", station,
                              "(" + str(cid) + ")", f"in {y:d}-{m:02d}")
                        # last chance: if there is a file with some data... use it
                        if (i == 2):
                            [df, cid, gotit] = fall_back_to_best(missing, saved_dfs,
                                                                 saved_urls, climate_ids)
                if gotit:
                    # Rename columns and get a YYYY-mm-dd date string
                    df['monthstr'] = df['month'].astype(str).str.zfill(2)
                    df['daystr'] = df['day'].astype(str).str.zfill(2)                
                    df['datestr'] = \
                        df['year'].astype(str) + '-' + df['monthstr'] \
                        + '-' + df['daystr']
                    # make new column for climate_id
                    df['cid'] = cid
                    # Keep only [date, temp_mean, temp_min, temp_max, climate_id]
                    df = df[['datestr', 'temp_mean', 'temp_min', 'temp_max', 'cid']]
                    df.columns = raw_data_columns
                    # Append to list of dataframes
                    dfs.append(df)
                else:
                    # Only display error if data not found for that YYYY-mm
                    print("\n**** ERROR ****  Data not found for ",
                          prov_id, region, str(y) + '-' + str(m) + "\n")
    # Merge all dates for this health region and output
    if dfs:
        # if list not empty
        df = pd.concat(dfs, ignore_index=True)
        # Fill in any missing dates (e.g., at the end of the month)
        #    (I think you have to convert date to datetime object to do this)
        df['date'] = pd.to_datetime(df['date'])
        firstday = f"{year_start:d}-{month_start:02d}-01"
        lastday = df['date'].to_list()[-1]
        daterng = pd.date_range(firstday, lastday)
        df = df.set_index('date').reindex(daterng).reset_index()
        df.columns = raw_data_columns
        # convert date back to string
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        # write file
        if write_to_file:
            outfile = outdir + prov_id + '_' + str(hr_uid) + ".csv"
            df.to_csv(outfile, index=False)
        else:
            return df
        
#=== Downloading data for one health region in a date range
def download_raw_data_one_hr(my_hr_uid, df_hr, date_start, date_end):
    # Prep the dates and outdir for downloading
    nowdate, year_start, year_end, month_start, month_end, outdir = \
        prep_for_download(date_start, date_end)
    # Loop over all health regions, selecting only this health region
    for index, row in df_hr.iterrows():
        hr_uid = row.hr_uid        
        if (hr_uid == my_hr_uid):
            prov_id = row.prov_id
            climate_ids = [row.climate_id, row.climate_id_alt, row.climate_id_alt2]
            stations = [row.temp_region, row.temp_region_alt, row.temp_region_alt2]
            region = row.health_region
            print("====== " + prov_id + " --- " + region + " (" + str(hr_uid) +  ") ======")
            download_monthly_data_and_write_to_file(year_start, year_end,
                                                    month_start, month_end,
                                                    prov_id, climate_ids, stations,
                                                    region, hr_uid, outdir)

#=== Downloading data for one province in a date range
def download_raw_data_one_province(my_prov_id, df_hr, date_start, date_end):
    # Prep the dates and outdir for downloading
    nowdate, year_start, year_end, month_start, month_end, outdir = \
        prep_for_download(date_start, date_end)
    # Loop over all health regions, selecting only those in this province
    for index, row in df_hr.iterrows():
        prov_id = row.prov_id
        if (prov_id == my_prov_id):
            climate_ids = [row.climate_id, row.climate_id_alt, row.climate_id_alt2]
            stations = [row.temp_region, row.temp_region_alt, row.temp_region_alt2]
            region = row.health_region
            hr_uid = row.hr_uid
            print("====== " + prov_id + " --- " + region + " (" + str(hr_uid) +  ") ======")
            download_monthly_data_and_write_to_file(year_start, year_end,
                                                    month_start, month_end,
                                                    prov_id, climate_ids, stations,
                                                    region, hr_uid, outdir)

#=== Downloading data for all health regions in a date range
def download_all_raw_data(df_hr, date_start, date_end):
    # Prep the dates and outdir for downloading
    nowdate, year_start, year_end, month_start, month_end, outdir = \
        prep_for_download(date_start, date_end)
    print(year_start, month_start, year_end, month_end)
    # Loop over all health regions
    for index, row in df_hr.iterrows():
        prov_id = row.prov_id
        climate_ids = [row.climate_id, row.climate_id_alt, row.climate_id_alt2]
        stations = [row.temp_region, row.temp_region_alt, row.temp_region_alt2]
        region = row.health_region
        hr_uid = row.hr_uid
        print("====== " + prov_id + " --- " + region + " (" + str(hr_uid) +  ") ======")
        download_monthly_data_and_write_to_file(year_start, year_end,
                                                month_start, month_end,
                                                prov_id, climate_ids, stations,
                                                region, hr_uid, outdir)

#============================================================#
#        creating actual/avg temperature data files          #
#============================================================#

base_actual_avg_outdir = "all_health_regions_actual_avg_temperature_files/"

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

def check_raw_data_for_create_actual_avg(date_start, date_end):
    # Check availability of raw data in time-frame
    #
    # grab the outfilename (rawdir) and dates for the raw data
    [nowdate, raw_year_start, raw_year_end, 
     raw_month_start, raw_month_end, rawdir] = \
         prep_for_download(download_raw_date_start, download_raw_date_end,
                           no_create_outdir=True)
    # datetime objects for rawdata start/end dates
    rawdata_start = dt.datetime.strptime(download_raw_date_start, "%Y-%m-%d")
    rawdata_end = dt.datetime.strptime(download_raw_date_end, "%Y-%m-%d")
    # datetime object for creation start/end dates
    create_start = dt.datetime.strptime(date_start, "%Y-%m-%d")
    create_end = dt.datetime.strptime(date_end, "%Y-%m-%d")
    # first data needed for averaging is 4 years before date_start
    first_date_needed_for_averaging = \
        dt.datetime.strptime(f"{create_start.year - 4:d}-{create_start.month:02d}-{create_start.day:02d}",
                             "%Y-%m-%d")
    # check that the specified raw data directories have the necessary data
    if create_no_averaging:
        if (rawdata_start > create_start):
            print("***Error: Must choose raw data directory that starts before create startdate.")
            exit(0)
    else:
        if (rawdata_start > first_date_needed_for_averaging):
            print("***Error: Must choose raw data directory that starts 4 years before create startdate.")
            exit(0)
    return rawdir

def load_raw_data_for_create_actual_avg(my_hr_uid, df_hr, rawdir):
    # load the data
    prov_id = df_hr[df_hr.hr_uid == my_hr_uid]['prov_id'].to_list()[0]
    hr = df_hr[df_hr.hr_uid == my_hr_uid]['health_region'].to_list()[0]    
    infile = rawdir + prov_id + '_' + str(my_hr_uid) + ".csv"
    #print("loading raw data from:\n\t" + infile)
    df = pd.read_csv(infile)
    return df, prov_id, hr

def centralmod(angle):
    a = np.mod(angle, 2.0*math.pi)
    if (a > math.pi):
        a = a - 2.0*math.pi
    return a

def create_actual_avg_temperature_file_one_hr(my_hr_uid, df_hr,
                                              date_start, date_end):
    # Check that raw data is available
    rawdir = check_raw_data_for_create_actual_avg(date_start, date_end)
    # Get the raw data file
    #
    # [date, temp_mean, temp_min, temp_max]
    df, prov_id, region = load_raw_data_for_create_actual_avg(my_hr_uid, df_hr,
                                                                 rawdir)
    # Prepare outfile directory
    nowdate = dt.datetime.now()
    startdate = dt.datetime.strptime(date_start, "%Y-%m-%d")
    enddate = dt.datetime.strptime(date_end, "%Y-%m-%d")    
    outdir = base_actual_avg_outdir \
        + f"{startdate.year:d}-{startdate.month:02d}-{startdate.day:02d}" \
        + '_' + f"{enddate.year:d}-{enddate.month:02d}-{enddate.day:02d}"
    # Check to see if it exists and create new (possibly unique) directory if not
    outdir = create_outdir(outdir, nowdate)
    # Interpolate each column (the temp columns x123x)
    temp_cols = [1,2,3]
    df[raw_data_columns[temp_cols]] = \
        df[raw_data_columns[temp_cols]].interpolate(method='polynomial', order=3)
    # Extend dates to date_end
    firstdayraw = df['date'].to_list()[0]
    lastdayraw = df['date'].to_list()[-1]
    lastdaydata = dt.datetime.strptime(lastdayraw, "%Y-%m-%d")
    df['date'] = pd.to_datetime(df['date'])
    daterng = pd.date_range(firstdayraw, date_end)
    df = df.set_index('date').reindex(daterng).reset_index()
    df.columns = raw_data_columns
    # Calculate solar angle
    zeroday = dt.datetime.strptime(angle_zeroday, "%Y-%m-%d")  # 2017-01-01
    df['theta'] = ( (df['date'] - zeroday).dt.days * angle_delta ).mod(2.0*math.pi)
    # Get four-year average of each temperature column
    for c in raw_data_columns[temp_cols]:
        cc = c + "_avg"
        df[cc] = 9999.0
    fouryears = dt.timedelta(days = 365.25*4)
    oneday = dt.timedelta(days = 1)
    for index, row in df.iterrows():
        date = row.date
        theta = row.theta
        if (date >= startdate):
            #print("===", date.strftime("%Y-%m-%d"), f" theta={theta:.6f}", "===")
            dfavg = \
                df[ ( df.date.between(date - fouryears, date - oneday ) )
                    & ( df.theta.between(theta - angle_averaging_halfrange,
                                         theta + angle_averaging_halfrange) 
                        | ( (df.theta + 2.0*math.pi).between(theta
                                                             - angle_averaging_halfrange,
                                                             theta
                                                             + angle_averaging_halfrange) )
                        | ( (df.theta - 2.0*math.pi).between(theta
                                                             - angle_averaging_halfrange,
                                                             theta
                                                             + angle_averaging_halfrange) )
                       )]
            seventhetas = dfavg['theta'].to_list()
            meantemps = []
            for c in raw_data_columns[temp_cols]:
                temps = [0,0,0,0]
                seventemps = dfavg[c].to_list()
                # one temperature from 4 years ago
                temps[0] = seventemps[0]
                for i in (1 + np.arange(3)):
                    # interpolate between the two temperatures for the other three years
                    a1 = seventhetas[2*i-1]
                    a2 = seventhetas[2*i]
                    # when near the 0/2pi boundary, return the modulus in [-pi:pi]
                    # since it should be that:
                    #                 a1 < theta < a2
                    if ( (theta < a1) | (a2 < theta) | (a2 < a1) ):
                        theta = centralmod(theta)
                        a1 = centralmod(a1)
                        a2 = centralmod(a2)                    
                    T1 = seventemps[2*i-1]
                    T2 = seventemps[2*i]                    
                    temps[i] = T1 + (T2-T1)/(a2-a1) * (theta - a1)
                tempmean = np.mean(temps)
                meantemps.append(tempmean)
                df.at[index, c+'_avg'] = tempmean
            #print(dfavg)
            #print(meantemps)
            # Fill in the "actual" data with averages when empty
            if (date > lastdaydata):
                for c in raw_data_columns[temp_cols]:
                    df.at[index,c] = df.at[index,c+'_avg']
    # output
    df = df[df.date.between(date_start, date_end)]
    outfile = outdir + prov_id + '_' + str(my_hr_uid) + '.csv'
    df.to_csv(outfile, index=False)

def prevmonth(month):
    if month == 1:
        return 12
    else:
        return month-1

#============================================================#
#        updating raw data files with most recent data       #
#============================================================#
def update_raw_data_for_last_two_months(df_hr, download_date_start,
                                        download_date_end):
    #
    # get today's date (for month/year)
    nowdate = dt.datetime.now()
    # find beginning of previous month and the end of this month
    year_start = nowdate.year
    year_end = nowdate.year
    month_end = nowdate.month
    month_start = prevmonth(month_end)
    startdate = f"{year_start:d}-{month_start:02d}-01"
    enddate = f"{year_start:d}-{month_end:02d}-" \
        + f"{get_endofmonth(year_start,month_end):02d}"
    # grab the outdir for "download_raw_all"
    nonedate, ys, ye, ms, me, outdir = \
        prep_for_download(download_date_start, download_date_end)
    # loop over all health regions
    for index, row in df_hr.iterrows():
        prov_id = row.prov_id
        climate_ids = [row.climate_id, row.climate_id_alt, row.climate_id_alt2]
        stations = [row.temp_region, row.temp_region_alt, row.temp_region_alt2]
        region = row.health_region
        hr_uid = row.hr_uid
        # load the saved data
        filename = prov_id + "_" + str(hr_uid) + ".csv"
        df = pd.read_csv(outdir + filename)
        # delete this month and the previous one
        df = df[~df['date'].between(startdate, enddate)]
        # Get new data only for this and last month
        print("====== " + prov_id + " --- " + region + " (" + str(hr_uid) +  ") ======")
        newdf = download_monthly_data_and_write_to_file(year_start, year_end,
                                                        month_start, month_end,
                                                        prov_id, climate_ids, stations,
                                                        region, hr_uid, outdir,
                                                        write_to_file = False)
        # append new data to old
        df = df.append(newdf)
        # write back to the file
        df.to_csv(outdir + filename, index=False)

############# Main Code ##############
if (runmode == "download_raw_all"):
    #=== Download all raw data
    download_all_raw_data(df_hr_static, download_raw_date_start,
                          download_raw_date_end)
elif (runmode == "download_raw_one_province"):
    #=== Download raw data for one province
    download_raw_data_one_province(selected_province_abb, df_hr_static,
                                   download_raw_date_start, download_raw_date_end)
elif (runmode == "download_raw_one_hr"):
    #=== Download raw data for health region    
    download_raw_data_one_hr(selected_hruid, df_hr_static,
                             download_raw_date_start, download_raw_date_end)
elif (runmode == "create_actual_avg_all"):
    #=== Create the actual_avg temperature files for all health regions
    for index, row in df_hr_static.iterrows():
        hr_uid = row.hr_uid
        prov_id = row.prov_id
        region = row.health_region
        print("============= " + region + " (" + prov_id + "_" + str(hr_uid)+  ")"
              + " =============")
        create_actual_avg_temperature_file_one_hr(hr_uid, df_hr_static,
                                                  create_date_start, create_date_end)
elif (runmode == "create_actual_avg_one_hr"):
    #=== Create the actual_avg temperature files for one health regions
    create_actual_avg_temperature_file_one_hr(selected_hruid, df_hr_static,
                                              create_date_start, create_date_end)
elif (runmode == "update_raw_data_two_months"):
    #=== Download all raw data for this month and last month
    update_raw_data_for_last_two_months(df_hr_static, download_raw_date_start,
                                        download_raw_date_end)
else:
    print("***Error: runmode not recognized.")
