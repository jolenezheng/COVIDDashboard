# Use this conda environment
#      ~/local/lib/mycode/conda/GHSwork.yml
import sys
import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt
import matplotlib.transforms
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.mask

class Pars:
    home="/Users/holderb"
    # GHS info
    ghspop_filepath=home+"/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0.tif"
    GHS_resolution_in_m = 250
    GHS_pixperkm = 1000//GHS_resolution_in_m
    GHS_Acell_in_kmsqd = 1.0/(GHS_pixperkm)**2
    GHS_nodataval = -200
    eps_mollweide = 'esri:54009'
    
    # Counties polygons
    countiespath = '../external-data/counties/UScensus/'
    UScounties_filepath = countiespath + 'tiger_line-shapefiles/tl_2019_us_county/tl_2019_us_county.shp'
    UScounties = None
    
    # FIPS database
    fips_filepath = countiespath + '2017FIPS/all-geocodes-v2017.csv'
    fipscodes = None
    # guam, virgin islands, manu'a, etc don't have state-fips
    fips_excluded_states = [78, 66, 69, 60]
    
    # database for output
    pwpd_counties = None
    csv_out_filename = 'pwpd_counties.csv'

    # plotting and fitting pwpd vs scalelength
    do_pwpd_vs_scalelength = True
    plot_pwpd = True
    fit_with_delta = False
    delta_fixedval = 0.1
    plot_domain = [0.09, 300.0]
    startrow = 0
    stoprow = 100000

def load_all_databases():
    # read in counties DataFrame
    Pars.UScounties = gpd.read_file(Pars.UScounties_filepath)
    # read in FIPS DataFrame
    Pars.fipscodes = pd.read_csv(Pars.fips_filepath, encoding='mac_roman')

def create_new_database():
    # copy some columns to a new DataFrame
    Pars.pwpd_counties = Pars.UScounties.loc[:,['STATEFP', 'COUNTYFP',
                                           'NAME', 'NAMELSAD', 'ALAND']]
    # add column for state names
    Pars.pwpd_counties['STATENAME'] = Pars.pwpd_counties['NAME']
    # use the fips file to get the state names from FIPS code
    droprows = []
    for index, row in Pars.pwpd_counties.iterrows():
        f = int(row['STATEFP'])
        # guam, virgin islands, manu'a, etc don't have state-fips
        if (f not in Pars.fips_excluded_states):  
            Pars.pwpd_counties.loc[index, 'STATENAME'] = \
                Pars.fipscodes[(Pars.fipscodes['State Code (FIPS)'] == f)
                          & (Pars.fipscodes['County Code (FIPS)'] == 0)]['Area Name (including legal/statistical area description)'].tolist()[0]
        else:
            # find indices of those places without statefips
            droprows.append(index)
    # drop the rows with places without statefips
    Pars.pwpd_counties = Pars.pwpd_counties.drop(droprows)
    # also drop same rows from UScounties polygons
    Pars.UScounties = Pars.UScounties.drop(droprows)
    # add columns for population and pwpd, make them numeric
    Pars.pwpd_counties['POP'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_A'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_A_ERR'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_ALPHA1'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_ALPHA1_ERR'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_ALPHA2'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_ALPHA2_ERR'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_XBREAK'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_XBREAK_ERR'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_DELTA'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])
    Pars.pwpd_counties['PWPD_DELTA_ERR'] = \
        pd.to_numeric(Pars.pwpd_counties['STATEFP'])

def get_GHS_windowed_subimage(windowDataFrame):
    # get polygon shape(s) from the geopandas dataframe
    windowshapes = windowDataFrame["geometry"]
    # mask GHS-POP image with entire set of shapes
    with rasterio.open(Pars.ghspop_filepath) as src:
        img, img_transform = \
            rasterio.mask.mask(src, windowshapes, crop=True)
        img_profile = src.profile
        img_meta = src.meta
    img_meta.update( { "driver": "GTiff",
                       "height": img.shape[1],
                       "width": img.shape[2],
                       "transform": img_transform} )
    # return only the first band (rasterio returns 3D array)
    return img[0], img_transform

def get_pwpd(arr, lengthscale_km):
    #pwpd = np.sum(np.multiply(arr,arr)) \
    #     / Pars.GHS_Acell_in_kmsqd / totalpop
    totalpop = np.sum(arr)
    return np.sum(np.multiply(arr,arr) / lengthscale_km**2 / totalpop)

def coursegrain_fac2(arr):
    (rows,cols) = arr.shape
    n = np.log(rows)/np.log(2)
    if ( (rows != cols) | ( (n%1) != 0 )  | (rows < 2) ):
        print("***Error: coursegrain_fac2 only works on 2^n (n>0) square arrays")
        sys.exit(0)
    newlen = int(2**(n-1))
    newarr = np.zeros((newlen, newlen))
    # replaces 4 squares with one
    for r in range(rows//2):
        for c in range(cols//2):
            newarr[r,c] = arr[2*r,2*c] + arr[2*r,2*c+1] \
                + arr[2*r+1, 2*c] + arr[2*r + 1, 2*c + 1]
    return newarr

def powerlaw(x, A, alpha):
    return A*np.power(x,alpha)

def broken_powerlaw(x, A, x0, alpha1, alpha2, delta):
    """
    Using the equation given here:
      docs.astropy.org/en/stable/api/
         astropy.modeling.powerlaws.SmoothlyBrokenPowerLaw1D.html
    """
    return A*np.power(x/x0, -alpha1)\
        *np.power(1/2.0*(1 + np.power(x/x0,1.0/delta)),
                  (alpha1-alpha2)*delta)

def broken_powerlaw_nodelta(x, A, x0, alpha1, alpha2):
    """
    Using the equation given here:
      docs.astropy.org/en/stable/api/
         astropy.modeling.powerlaws.SmoothlyBrokenPowerLaw1D.html
    """
    delta = Pars.delta_fixedval  # fixed
    return A*np.power(x/x0, -alpha1)\
        *np.power(1/2.0*(1 + np.power(x/x0,1.0/delta)),
                  (alpha1-alpha2)*delta)

def get_fit_of_pwpd_vs_scalelength(ax, arr, popdensity):
    (rows, cols) = arr.shape
    # set initial scale length
    scalelength_km = Pars.GHS_resolution_in_m / 1000
    # get minimal 2^n box around image
    n = int(np.ceil(np.log(max(rows,cols))/np.log(2.0)))
    bigarr = np.zeros((2**n, 2**n))
    bigarr[0:rows, 0:cols] = arr
    newarr = bigarr
    # make lower and lower resolution images and calculate pwpd
    pwpd_r = []
    print("ind  scale(km)  imgsize  pwpd")
    for i in range(n):
        curscalelength = scalelength_km*2**i
        curpwpd = get_pwpd(newarr, curscalelength)
        pwpd_r.append(curpwpd)
        if ( (i == 0) | (i == (n-1)) ):
            print(f"{i:d}  {curscalelength:.2f}  {2**(n-i):.0f}  {curpwpd:.0f}")
        # coursegrain the image
        newarr = coursegrain_fac2(newarr)
    lengths = scalelength_km*np.power(2, np.arange(n))
    # Plot pwpd vs scalelength
    if (Pars.plot_pwpd):
        ax.scatter(lengths, pwpd_r, s=15)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_ylabel(r'$\mathrm{PWPD} \;\;\left(\mathrm{people}/\mathrm{km}^2\right)$')
        ax.set_xlabel('resolution (km)')
        ax.set_xlim(Pars.plot_domain)
        ax.tick_params(direction='in', which='both', top=True)
    # Fit to a broken power law (or fall back to single power law, if that fails)
    A = 500
    alph = 0.5
    firsttry = True
    while(True):
        try:
            # Fit a broken power law
            if Pars.fit_with_delta:
                initpars = [A, 1.0, alph, 1.0, 1e-1]
                parbounds = ((0, 0, 0, 0, 1e-3),
                             (np.inf, np.inf, np.inf, np.inf, np.inf))
                popt, pcov = \
                    scipy.optimize.curve_fit(broken_powerlaw, lengths, pwpd_r,
                                             p0=initpars,
                                             bounds=parbounds,
                                             maxfev=5000) #maxfev=200*(5+1))
            else: 
                initpars = [A, 1.0, alph, 1.0]
                parbounds = ((0, 0, 0, 0),
                             (np.inf, np.inf, np.inf, np.inf))
                popt, pcov = \
                    scipy.optimize.curve_fit(broken_powerlaw_nodelta, lengths, pwpd_r,
                                             p0=initpars,
                                             bounds=parbounds,
                                             maxfev=5000) #maxfev=200*(5+1))
            A = popt[0]
            A_err = np.sqrt(pcov[0,0])
            xb = popt[1]
            xb_err = np.sqrt(pcov[1,1])
            alph1 = popt[2]
            alph1_err = np.sqrt(pcov[2,2])
            alph2 = popt[3]
            alph2_err = np.sqrt(pcov[3,3])
            if Pars.fit_with_delta:            
                delt = popt[4]
                delt_err = np.sqrt(pcov[4,4])
                print(f"A={A:.2e}; xb={xb:.2e}; alph1={alph1:.2e}; alph2={alph2:.2e}; delta={delt:.2e}")
                print(f"A_err={A_err:.1e}; xb_err={xb_err:.1e}; alph1_err={alph1_err:.1e}; alph2_err={alph2_err:.1e}; delta_err={delt_err:.1e}")
                if (Pars.plot_pwpd):
                    ax.plot(lengths, broken_powerlaw(lengths,
                                                     A, xb, alph1, alph2, delt), 'k--')
                    ax.plot(Pars.plot_domain, [popdensity,popdensity],':k')
            else:
                print(f"A={A:.2e}; xb={xb:.2e}; alph1={alph1:.2e}; alph2={alph2:.2e}")
                print(f"A_err={A_err:.1e}; xb_err={xb_err:.1e}; alph1_err={alph1_err:.1e}; alph2_err={alph2_err:.1e}")
                if (Pars.plot_pwpd):
                    ax.plot(lengths, broken_powerlaw_nodelta(lengths,
                                                             A, xb, alph1, alph2), 'k--')
                    ax.plot(Pars.plot_domain, [popdensity,popdensity],':k')
                    popdens = f'Population Density = {popdensity:.1f} '\
                        + r'$\mathrm{km}^{-2}$'
                    ts1_trans = matplotlib.transforms.blended_transform_factory(
                        ax.transAxes, ax.transData)
                    ax.text(0.45, 0.98*popdensity, popdens, horizontalalignment = 'left',
                            verticalalignment='top',transform=ts1_trans, fontsize=8)
            # Print the power 
            textstring1 = r'$A = $' + f"{A:.2e}" + r'$\pm$' \
                + f"{A_err:.1e}"
            textstring2 = r'$x_b = $' + f"{xb:.2e}" + r'$\pm$' \
                + f"{xb_err:.1e}"
            textstring3 = r'$\alpha_1 = $'+ f"{alph1:.2f}" \
                + r'$\pm$' + f"{alph1_err:.2f}"
            textstring4 = r'$\alpha_2 = $'+ f"{alph2:.2f}" \
                + r'$\pm$' + f"{alph2_err:.2f}"
            ax.text(0.1, 0.3, textstring1, horizontalalignment = 'left',
                    verticalalignment='center',transform=ax.transAxes)
            ax.text(0.1, 0.25, textstring2, horizontalalignment = 'left',
                    verticalalignment='center',transform=ax.transAxes)
            ax.text(0.1, 0.2, textstring3, horizontalalignment = 'left',
                    verticalalignment='center',transform=ax.transAxes)
            ax.text(0.1, 0.15, textstring4, horizontalalignment = 'left',
                    verticalalignment='center',transform=ax.transAxes)
            if Pars.fit_with_delta:
                textstring5 = r'$\Delta = $'+ f"{delt:.2e}" \
                    + r'$\pm$' + f"{delt_err:.1e}"
                ax.text(0.1, 0.1, textstring5, horizontalalignment = 'left',
                        verticalalignment='center',transform=ax.transAxes)
            # Return the parameters and their variances
            if Pars.fit_with_delta:
                return A, A_err, xb, xb_err, alph1, alph1_err, alph2, alph2_err, delt, delt_err
            else:
                return A, A_err, xb, xb_err, alph1, alph1_err, alph2, alph2_err, \
                    Pars.delta_fixedval, 0.0
        except RuntimeError:
            try:
                # Fit a single power law
                popt, pcov = \
                    scipy.optimize.curve_fit(powerlaw, lengths, pwpd_r, p0=[A,alph])
                A = popt[0]
                A_err = np.sqrt(pcov[0][0])
                alph = -1.0*popt[1]
                alph_err = np.sqrt(pcov[1][1])
                if firsttry:
                    firsttry=False
                else:
                    print(f"***single power fit: A={A:.2e}; alph={alph:.2e}")
                    if (Pars.plot_pwpd):
                        ax.plot(lengths, powerlaw(lengths, A, -1.0*alph), 'k--')
                        ax.plot(Pars.plot_domain, [popdensity,popdensity],':k')
                        popdens = f'Population Density = {popdensity:.0f} '\
                            + r'$\mathrm{km}^{-2}$'
                        ts1_trans = matplotlib.transforms.blended_transform_factory(
                            ax.transAxes, ax.transData)
                        ax.text(0.45, 0.98*popdensity, popdens, horizontalalignment = 'left',
                                verticalalignment='top',transform=ts1_trans, fontsize=8)
                        # Print the power 
                        textstring1 = r'$\alpha = $'+ f"{alph:.2f}" \
                            + r'$\pm$' + f"{alph_err:.2f}"
                        textstring2 = r'$A = $'+ f"{A:.2f}" \
                            + r'$\pm$' + f"{A_err:.2f}"
                        ax.text(0.1, 0.2, textstring1, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                        ax.text(0.1, 0.1, textstring1, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                    # Return the parameters found
                    return A, A_err, 0.0, 0.0, alph, alph_err, 0.0, 0.0, 0.0, 0.0
            except RuntimeError:
                print("***Error: could not even fit a power law!")
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

# load the counties polygons and statefips databases
load_all_databases()
# make pwpd database w/ state names too
create_new_database()
# loop over counties, mask GHS, calculate pwpd
if (Pars.plot_pwpd):
    plotdir = 'plots'
for index, row in Pars.pwpd_counties.iterrows():
    if ( (index >= Pars.startrow) & (index < Pars.stoprow) ):
        if (Pars.plot_pwpd):
            fig,ax = plt.subplots(figsize=(8,8))
        # get corresponding county polygon
        county = Pars.UScounties.loc[[index]]
        # print name of county for user
        statefips=  int(row['STATEFP'])
        countyfips = int(row['COUNTYFP'])
        statecountyfips = f"{statefips:02}{countyfips:03}"
        countyname = row['NAME'] + ", " + row['STATENAME']
        print("==== " + str(index) + " "
              + statecountyfips + " " + countyname
              + " =====")
        # transform to Mollweide
        county_m = county.to_crs(crs=Pars.eps_mollweide)
        # mask GHS-POP image on county, get raster subimage
        img, img_transform = get_GHS_windowed_subimage(county_m)
        imarr = np.array(img)
        imarr[(imarr == Pars.GHS_nodataval)] = 0.0
        # calculate population and PWPD
        pop = np.sum(imarr)
        Pars.pwpd_counties.loc[index, 'POP'] = pop
        pwpd = np.sum(np.multiply(imarr, imarr)) \
            / Pars.GHS_Acell_in_kmsqd / pop
        Pars.pwpd_counties.loc[index, 'PWPD'] = pwpd
        print(f"PWPD (250km) = {pwpd:.0f}   POP = {pop:.0f}")
        # get regular population density
        area = float(row['ALAND'])/1e6
        popdensity = pop/area
        # get parameters for pwpd vs scalelength
        if Pars.do_pwpd_vs_scalelength:
            A, A_err, xb, xb_err, al1, al1_err, al2, al2_err, delt, delt_err = \
                get_fit_of_pwpd_vs_scalelength(ax, imarr, popdensity)
            # put parameters into csv file
            Pars.pwpd_counties.loc[index, 'PWPD_A'] = A
            Pars.pwpd_counties.loc[index, 'PWPD_A_ERR'] = A_err
            Pars.pwpd_counties.loc[index, 'PWPD_XBREAK'] = xb
            Pars.pwpd_counties.loc[index, 'PWPD_XBREAK_ERR'] = xb_err
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA1'] = al1
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA1_ERR'] = al1_err
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA2'] = al2
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA2_ERR'] = al2_err
            Pars.pwpd_counties.loc[index, 'PWPD_DELTA'] = delt
            Pars.pwpd_counties.loc[index, 'PWPD_DELTA_ERR'] = delt_err
        if ((index % 100) == 0):
            # write pwpd dataframe to csv
            Pars.pwpd_counties.to_csv(Pars.csv_out_filename)
        if (Pars.plot_pwpd):
            ax.set_title(countyname)
            filename = plotdir + '/' + statecountyfips + '.pdf'
            fig.savefig(filename)
            plt.close(plt.gcf())

# write pwpd dataframe to csv
Pars.pwpd_counties.to_csv(Pars.csv_out_filename)
if (Pars.plot_pwpd):
    plt.close(fig)
