import pandas as pd
import numpy as np
import scipy.interpolate

#=== NOTE: In spot checking the result of this extrapolation to
#          2020, I find that all actual mortality values were
#          higher than these extrapolated ones, by a factor of
#          1.05 (PEI, 1367 vs 1297) to 1.17 (Toronto, 115k vs 98k).
#          Canada is off by 1.13 (300k vs 266k)
#
#          So we might want to apply a multiplier of 1.1.

#=== Extrapolation of the [2001, 2006, 2011] mortality
#    date to 2020 is done by scipy.interpolate.UnivariateSpline
#    which allows for the assumption of a polynomial for
#    interpolation... probably best to stick with linear (k=1)
extrap_order = 1

#=== Load the Statistics Canada datafile, found here:
#
#  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310074201
#
# containing mortality data from three three-year periods:
#
#  2000-2002, 2005-2007, and 2010-2012
#
filename = "mortality_statistics-canada_2010-2012.csv"
df = pd.read_csv(filename)

#=== Select out total mortality from all causes, whole population
df = df[ (df["Selected causes of death (ICD-10)"] == "Total, all causes of death [A00-Y89]")
         & (df["Characteristics"] == "Number")
         & (df["Sex"] == "Both sexes")
         & (df["Indicators"] == "Mortality") ]

#=== Mortality is a 3-yr value.  Get 1-yr average
df['VALUE'] = df['VALUE']/3.0

#=== Keep only the possibly relevant rows
df = df[["REF_DATE", "GEO", "DGUID", "VECTOR", "COORDINATE", "VALUE"]]

#== Make a column for hr_uid, which seems to be the last 4
#   characters of DGUID
df["hr_uid"] = df["DGUID"]
rows_to_delete = []
for index, row in df.iterrows():
    id_str = str(row.hr_uid)
    try:
        df.at[index, "hr_uid"] = int(id_str[-4:])
    except:
        df.at[index, "hr_uid"] = np.nan
    #=== Reset the provincial hr_uid values to
    #    something useful when sorted
    hr = df.at[index, "hr_uid"]
    if ( hr == 210 ):
        # NL
        df.at[index, "hr_uid"] = 1000
    elif ( hr == 211 ):
        # PEI
        df.at[index, "hr_uid"] = 1101
    elif ( hr == 212 ):
        # NS
        df.at[index, "hr_uid"] = 1200
    elif ( hr == 213 ):
        # NB
        df.at[index, "hr_uid"] = 1300
    elif ( hr == 224 ):
        # QC
        df.at[index, "hr_uid"] = 2400
    elif ( hr == 246 ):
        # MB
        df.at[index, "hr_uid"] = 4600
    elif ( hr == 247 ):
        # SK
        df.at[index, "hr_uid"] = 4700
    elif ( hr == 248 ):
        # AB
        df.at[index, "hr_uid"] = 4800
    elif ( hr == 259 ):
        # BC
        df.at[index, "hr_uid"] = 5900
    elif ( hr == 260 ):
        # YT
        df.at[index, "hr_uid"] = 6000
    elif ( hr == 261 ):
        # NWT
        df.at[index, "hr_uid"] = 6200
    elif ( hr == 262 ):
        # NU
        df.at[index, "hr_uid"] = 6100
    elif ( hr == 1124 ):
        # CANADA
        df.at[index, "hr_uid"] = 0
    elif "Ontario by Local" in row.GEO:
        # ON
        df.at[index, "hr_uid"] = 3500
    elif "Ontario by Health" in row.GEO:
        # ON
        df.at[index, "hr_uid"] = 3599
    elif "Mamawetan" in row.GEO:
        # SK 4711 + 4712 + 4713 = "4716"
        df.at[index, "hr_uid"] = 4716
    elif "Peer group" in row.GEO:
        #=== Flag the rows of "Peer Groups" for deletion
        rows_to_delete.append(index)
#=== Delete Peer group rows
df = df.drop(index=rows_to_delete)

# Define center-year of three-year average ranges
df['year'] = 0
for index, row in df.iterrows():
    y = row.REF_DATE
    if (y == "2000/2002"):
        df.at[index, "year"] = 2001
    elif (y == "2005/2007"):
        df.at[index, "year"] = 2006
    elif (y == "2010/2012"):
        df.at[index, "year"] = 2011
#=== Rename columns and re-arrange
df.columns = ["REF_DATE", "region", "DGUID", "VECTOR", "COORDINATE",
	      "mortality", "hr_uid", "year"]
df = df[["hr_uid", "year", "mortality", "region",
         "DGUID", "VECTOR", "COORDINATE", "REF_DATE"]]
#=== Create new rows for 2020
hregions = np.unique(df['hr_uid'].to_list())
newrows = []
for hr in hregions:
    df_hr = df[df.hr_uid == hr]
    year = df_hr.year.to_numpy()
    ann_death = df_hr.mortality.to_numpy()
    #=== Extrapolate the annual death to 2020
    extrapolator = \
        scipy.interpolate.UnivariateSpline(year, ann_death,
                                           k=extrap_order)
    row = {"hr_uid" : hr,
           "year": 2020,
           "mortality": extrapolator(2020.0),
           "region": "",
           "DGUID": "",
           "VECTOR": "",
           "COORDINATE": "",
           "REF_DATE": "2019/2021"}
    newrows.append(row)
#=== Merge the new rows into the existing dataframe
newrows_df = pd.DataFrame(newrows)
df = pd.concat([df, newrows_df], ignore_index=True)


#=== Give new rows the correct values in other columns
df = df.sort_values(by=["hr_uid", "year"])
for index, row in df.iterrows():
    if (row.year == 2011):
        region = row.region
        dguid = row.DGUID
        vector = row.VECTOR
        coord = row.COORDINATE
    if (row.year == 2020):
        df.at[index, 'region'] = region
        df.at[index, 'DGUID'] = dguid
        df.at[index, 'VECTOR'] = vector
        df.at[index, 'COORDINATE'] = coord

#=== Concatenate health regions to match the COVID regions
#
#   * In my script get_pwpd_all-canada-health-regions.py
#     I merged *current* health regions into the ones used
#     for COVID data. See the 2020-11-09_pwpd-module-github
#     analysis directory.
#
#   * But here, some of these health regions are old. So I
#     needed to make some adjustments:
#
#
#
newrows = []
#=== Ontario --- Merge 3531+3552 --> 3575 (Southwestern)
newhr = 3575
newname = "Southwestern"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 3531)
         | (df.hr_uid == 3552) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== Ontario --- Re-label Huron 3539 --> 93539
hr = 3539
newhr = 93539
for index, row in df.iterrows():
    if (row.hr_uid == hr):
        df.at[index, "hr_uid"] = newhr
#=== Ontario --- Merge 93539+3554 --> 3539
newhr = 3539
newname = "Huron Perth Health Unit"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 93539)
         | (df.hr_uid == 3554) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== BC --- Merge 5921+5922+5923 --> 591 (Fraser Health)
newhr = 591
newname = "Fraser Health"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 5921)
         | (df.hr_uid == 5922)
         | (df.hr_uid == 5923) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== BC --- Merge 5911+5912+5913+5914 --> 592 (Interior Health)
newhr = 592
newname = "Interior Health"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 5911)
         | (df.hr_uid == 5912)
         | (df.hr_uid == 5913)
         | (df.hr_uid == 5914) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== BC --- Merge 5941+5942+5943 --> 593 ([Vancouver] Island Health)
newhr = 593
newname = "Island Health"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 5941)
         | (df.hr_uid == 5942)
         | (df.hr_uid == 5943) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== BC --- Merge 5951+5952+5953 --> 594 (Northern Health)
newhr = 594
newname = "Northern Health"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 5951)
         | (df.hr_uid == 5952)
         | (df.hr_uid == 5953) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== BC --- Merge 5931+5932+5933 --> 595 (Vancouver Coastal Health)
newhr = 595
newname = "Vancouver Coastal Health"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 5931)
         | (df.hr_uid == 5932)
         | (df.hr_uid == 5933) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Merge 4708+4709+4710 --> 472 (North, approximate)
newhr = 472
newname = "North (approximate)"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 4708)
         | (df.hr_uid == 4709)
         | (df.hr_uid == 4710) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Merge 4705+4707 --> 473 (Central, approximate)
newhr = 473
newname = "Central (approximate)"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 4705)
         | (df.hr_uid == 4707) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Merge 4701+4702+4703 --> 476 (South, approximate)
newhr = 476
newname = "South (approximate)"
newmort = \
    df[(df.year == 2020) &
       ( (df.hr_uid == 4701)
         | (df.hr_uid == 4702)
         | (df.hr_uid == 4703) )]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Duplicate Far North w/ new hr_uid (4716->471)
#           (this file's 4716 = actual 4711+4712+4713)
newhr = 471
newname = "Far North (approximate)"
newmort = \
    df[(df.year == 2020) &
       (df.hr_uid == 4716)]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Duplicate Saskatoon w/ new hr_uid (4706->474)
newhr = 474
newname = "Saskatoon (approximate)"
newmort = \
    df[(df.year == 2020) &
       (df.hr_uid == 4706)]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)
#=== SK --- Duplicate Regina w/ new hr_uid (4704->475)
newhr = 475
newname = "Regina (approximate)"
newmort = \
    df[(df.year == 2020) &
       (df.hr_uid == 4704)]['mortality'].sum()
row = {"hr_uid" : newhr,
       "year": 2020,
       "mortality": newmort,
       "region": newname,
       "DGUID": "",
       "VECTOR": "",
       "COORDINATE": "",
       "REF_DATE": "2019/2021"}
newrows.append(row)

#=== Merge the new rows into the existing dataframe
newrows_df = pd.DataFrame(newrows)
df = pd.concat([df, newrows_df], ignore_index=True)


#=== Sort by HR, Date and export        
df = df.sort_values(by=["hr_uid", "year"])
df = df[df.year == 2020]
df.to_csv("junk.csv", index=False)
