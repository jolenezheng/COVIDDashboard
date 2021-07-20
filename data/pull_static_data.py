import requests
import os

def replaceMultiple(string, replacePairs):
  newString = string
  for old, new in replacePairs:
    newString = newString.replace(old, new)
  return newString

def downloadAndCleanFile(url, newFilePath, replaceMappings):
  r = requests.get(url, allow_redirects=True)
  oldFile = r.text
  newFile = replaceMultiple(oldFile, replaceMappings)
  with open(newFilePath, "w") as writeFile:
    writeFile.write(newFile)

mortalityUrl = 'https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv'
mortalityFilePath = "/var/www/html/COVIDDashboard/data/mortality.csv"

casesUrl = 'https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv'
casesFilePath = "/var/www/html/COVIDDashboard/data/cases.csv"

replaceMappings = [
  ('è', 'e'),
  ('é', 'e'),
  ('ô', 'o'),
  ('Î', 'I')
]


downloadAndCleanFile(mortalityUrl, mortalityFilePath, replaceMappings)
downloadAndCleanFile(casesUrl, casesFilePath, replaceMappings)

os.system("systemctl restart mylocalcovid")
