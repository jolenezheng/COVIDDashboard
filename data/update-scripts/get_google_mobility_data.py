import pandas as pd

global_mobility_file = "Global_Mobility_Report.csv"
output_mobility_file = "mobility.csv"

# load all data (550MB!)
df = pd.read_csv(global_mobility_file)
# restrict to canadian health region data
provinces_without_region_mobility = ["Yukon", "Northwest Territories"]
df = df[((df['country_region_code'] == "CA") & (df['sub_region_2'].notna()))
        | (df['sub_region_1'].isin(provinces_without_region_mobility)) ]

# remove accents
df['sub_region_2'] = \
    df['sub_region_2'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# delete the column "iso_3166_2_code"  (gives warning about mixed type, mostly blank)
df.drop(["iso_3166_2_code"], axis=1, inplace=True)

# output to file
df.to_csv(output_mobility_file, index=False)
