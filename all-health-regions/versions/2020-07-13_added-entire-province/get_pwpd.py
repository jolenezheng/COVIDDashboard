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
    
    # Canadian Health Regions Polygons
    # (These are 2018 from arcgis, also used by ishaberry's covid19canada)
    regionspath = '../external-data/health-regions/ArcGis/health-regional-archive-public-view-shape_2018/'
    regions_filepath = regionspath + 'RegionalHealthBoundaries.shp'
    HRegions = None
    provinces = None
    regionnames = None
    pwpd_regions = None
    csv_out_filename = 'pwpd_canada_health-regions.csv'

    # plotting and fitting pwpd vs scalelength
    do_pwpd_vs_scalelength = False
    plot_pwpd = True
    fit_with_delta = False
    delta_fixedval = 0.1
    plot_domain = [0.09, 300.0]
    startrow = 0   
    stoprow = 10000

def load_all_databases():
    # read in counties DataFrame
    Pars.HRegions = gpd.read_file(Pars.regions_filepath)
    # canadian province abbreviations
    Pars.provinces = pd.read_csv('canada-provinces.csv')
    # canadian health region names and codes
    Pars.regionnames = pd.read_csv('canada-hr-names.csv')

def create_new_database():
    # copy some columns to a new DataFrame
    Pars.pwpd_regions = \
        Pars.HRegions.loc[:,['HR_UID', 'Province','ENGNAME']]
    # get rows for entire province and append to dataframes
    provinces = Pars.HRegions.dissolve(by='Province')
    # for some reason the province column disappears on dissolve
    # and the index is the province
    provincerows = provinces.loc[:,['HR_UID','ENGNAME']]
    provincerows['Province'] = provincerows['ENGNAME']
    for index, row in provincerows.iterrows():
        code = row['HR_UID'][0:2]
        provincerows.loc[index,'ENGNAME'] = 'Entire Province'
        provincerows.loc[index,'HR_UID'] = code
        provincerows.loc[index,'Province'] = index
    Pars.HRegions = Pars.HRegions.append(provinces)
    Pars.HRegions = Pars.HRegions.sort_values(by=['HR_UID'])
    Pars.pwpd_regions = Pars.pwpd_regions.append(provincerows)
    Pars.pwpd_regions = Pars.pwpd_regions.sort_values(by=['HR_UID'])
    Pars.HRegions = Pars.HRegions.reset_index(drop=True)
    Pars.pwpd_regions = Pars.pwpd_regions.reset_index(drop=True)
    # add column for "long" province name (used by covid19 datafile)
    Pars.pwpd_regions['ProvinceName'] = Pars.pwpd_regions['Province']
    # add column for "short" health region name (used by covid19)
    Pars.pwpd_regions['shortname'] = Pars.pwpd_regions['Province']
    # use the province and regionnames files to get the province name
    # from abbreviation and the shortname from the code
    for index, row in Pars.pwpd_regions.iterrows():
        pabb = row['Province']
        code = int(row['HR_UID'])
        Pars.pwpd_regions.loc[index, 'ProvinceName'] = \
            Pars.provinces[(Pars.provinces['abb'] == pabb)]['name'].tolist()[0]
        if (row['ENGNAME'] == 'Entire Province'):
            Pars.pwpd_regions.loc[index, 'shortname'] = 'Entire Province'
        else:
            Pars.pwpd_regions.loc[index, 'shortname'] = \
                Pars.regionnames[(Pars.regionnames['HR_UID'] == code)]['shortname'].tolist()[0]
    # add columns for area, population and pwpd, make them numeric
    Pars.pwpd_regions['landarea'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['POP'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_A'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_A_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_ALPHA1'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_ALPHA1_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_ALPHA2'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_ALPHA2_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_XBREAK'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_XBREAK_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_DELTA'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWPD_DELTA_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_A'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_A_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_ALPHA1'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_ALPHA1_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_ALPHA2'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_ALPHA2_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_XBREAK'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_XBREAK_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_DELTA'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])
    Pars.pwpd_regions['PWLOGPD_DELTA_ERR'] = \
        pd.to_numeric(Pars.pwpd_regions['HR_UID'])

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
    pwpd = np.sum(np.multiply(arr,arr) / lengthscale_km**2 / totalpop)
    # see just before fit, using errors proposed by niayesh
    #pwpd_err = 2.0/(np.sqrt(totalpop) * lengthscale_km**2)
    return pwpd

def get_pwlogpd(arr, lengthscale_km):
    #pwpd = np.sum(np.multiply(arr,arr)) \
    #     / _Pars._GHS_Acell_in_kmsqd / totalpop
    totalpop = np.sum(arr)
    # mask array on nonzero values
    nonzero = (arr > 0)
    return np.sum( np.multiply( np.log(arr[nonzero]/lengthscale_km**2),
                                arr[nonzero] ) \
                   / totalpop)

def coarsegrain_fac2(arr):
    (rows,cols) = arr.shape
    n = np.log(rows)/np.log(2)
    if ( (rows != cols) | ( (n%1) != 0 )  | (rows < 2) ):
        print("***Error: coarsegrain_fac2 only works on 2^n (n>0) square arrays")
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

def log_powerlaw(x, A, alpha):
    return np.log(A*np.power(x,alpha))

def broken_powerlaw(x, Aprime, xb, alpha1, alpha2):   #, delta):
    """
    Using the equation given here:
      docs.astropy.org/en/stable/api/
         astropy.modeling.powerlaws.SmoothlyBrokenPowerLaw1D.html
    """
    delta = Pars.delta_fixedval  # fixed
    A = Aprime / ((1.0/xb)**(-1.0*alpha1)) / \
        ((1.0/2)**(delta*(alpha1-alpha2)))
    return A*np.power(x/xb, -alpha1)\
        *np.power(1/2.0*(1 + np.power(x/xb,1.0/delta)),
                  (alpha1-alpha2)*delta)

def log_broken_powerlaw(x, Aprime, xb, alpha1, alpha2):   #, delta):
    """
    Using the equation given here:
      docs.astropy.org/en/stable/api/
         astropy.modeling.powerlaws.SmoothlyBrokenPowerLaw1D.html
    """
    delta = Pars.delta_fixedval  # fixed
    A = Aprime / ((1.0/xb)**(-1.0*alpha1)) / \
        ((1.0/2)**(delta*(alpha1-alpha2)))
    return np.log(
        A*np.power(x/xb, -alpha1)\
        *np.power(1/2.0*(1 + np.power(x/xb,1.0/delta)),
                  (alpha1-alpha2)*delta)
        )

def get_fit_of_pwpd_vs_scalelength(ax, arr, popdensity, type='STD'):
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
        if (type=='LOG'):
            curpwpd = get_pwlogpd(newarr, curscalelength)
        else:
            curpwpd = get_pwpd(newarr, curscalelength)
        pwpd_r.append(curpwpd)
        if ( (i == 0) | (i == (n-1)) ):
            print(f"{i:d}  {curscalelength:.2f}  {2**(n-i):.0f}  {curpwpd:.0f}")
        # coarsegrain the image
        newarr = coarsegrain_fac2(newarr)
    lengths = scalelength_km*np.power(2, np.arange(n))
    pwpd_r = np.array(pwpd_r)
    # see niayesh email 2020-05-09 for explanation of errors
    #
    #     weight_i = 1/err_i = (rmax/ri)^2
    #
    # or maybe it's
    #
    #     weight_i = 1/err_i = rmax/ri
    #
    # the latter seems to work much better, and we'll use that
    errs = np.divide(lengths, lengths[-1])
    # Plot pwpd vs scalelength
    if (Pars.plot_pwpd):
        #ax.scatter(lengths, pwpd_r, s=15)
        if (type == 'LOG'):
            ax.errorbar(lengths, np.exp(pwpd_r), yerr=errs, fmt='o', markersize=3)
        else:
            ax.errorbar(lengths, pwpd_r, yerr=errs, fmt='o', markersize=3)
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
            initpars = [A, 1.0, alph, 1.0]
            parbounds = ((0, 0, 0, 0),
                         (np.inf, np.inf, np.inf, np.inf))
            if (type == 'LOG'):
                popt, pcov = \
                    scipy.optimize.curve_fit(log_broken_powerlaw,
                                             lengths,
                                             pwpd_r,  # it's already logged values
                                             p0=initpars,
                                             bounds=parbounds,
                                             sigma=errs,
                                             maxfev=5000) # sigma=pwpd_r_err, maxfev=200*(5+1))
            else:
                popt, pcov = \
                    scipy.optimize.curve_fit(log_broken_powerlaw,
                                             lengths,
                                             np.log(pwpd_r),
                                             p0=initpars,
                                             bounds=parbounds,
                                             sigma=errs,
                                             maxfev=5000) # sigma=pwpd_r_err, maxfev=200*(5+1))
            A = popt[0]
            A_err = np.sqrt(pcov[0,0])
            # Tricky: Raise amy own RuntimeError if fit is bad:
            if (A_err > A):
                raise RuntimeError('Just real bad errors')
            xb = popt[1]
            xb_err = np.sqrt(pcov[1,1])
            alph1 = popt[2]
            alph1_err = np.sqrt(pcov[2,2])
            alph2 = popt[3]
            alph2_err = np.sqrt(pcov[3,3])
            print(f"Ap{A:.2e}; xb={xb:.2e}; alph1={alph1:.2e}; alph2={alph2:.2e}")
            print(f"Ap_err={A_err:.2e}; xb_err={xb_err:.1e}; alph1_err={alph1_err:.1e}; alph2_err={alph2_err:.1e}")
            if (Pars.plot_pwpd):
                ax.plot(lengths, broken_powerlaw(lengths,
                                                         A, xb, alph1, alph2), 'k--')
                ax.plot(Pars.plot_domain, [popdensity,popdensity],':k')
                popdens = f'Population Density = {popdensity:.1f} '\
                    + r'$\mathrm{km}^{-2}$'
                ts1_trans = matplotlib.transforms.blended_transform_factory(
                    ax.transAxes, ax.transData)
                ax.text(0.45, 0.98*popdensity, popdens, horizontalalignment = 'left',
                        verticalalignment='top',transform=ts1_trans, fontsize=8)
                # Print the power 
                textstring1 = r'$A^{\prime} = $' + f"{A:.2e}" + r'$\pm$' \
                    + f"{A_err:.1e}"
                textstring2 = r'$x_b = $' + f"{xb:.2e}" + r'$\pm$' \
                    + f"{xb_err:.1e}"
                textstring3 = r'$\alpha_1 = $'+ f"{alph1:.3f}" \
                    + r'$\pm$' + f"{alph1_err:.3f}"
                textstring4 = r'$\alpha_2 = $'+ f"{alph2:.3f}" \
                    + r'$\pm$' + f"{alph2_err:.3f}"
                ax.text(0.1, 0.25, textstring1, horizontalalignment = 'left',
                        verticalalignment='center',transform=ax.transAxes)
                ax.text(0.1, 0.2, textstring2, horizontalalignment = 'left',
                        verticalalignment='center',transform=ax.transAxes)
                ax.text(0.1, 0.15, textstring3, horizontalalignment = 'left',
                        verticalalignment='center',transform=ax.transAxes)
                ax.text(0.1, 0.1, textstring4, horizontalalignment = 'left',
                        verticalalignment='center',transform=ax.transAxes)
            # Return the parameters and their variances
            return A, A_err, xb, xb_err, alph1, alph1_err, alph2, alph2_err, \
                Pars.delta_fixedval, 0.0
        except RuntimeError:
            try:
                # Fit a single power law
                if (type == 'LOG'):
                    popt, pcov = \
                        scipy.optimize.curve_fit(log_powerlaw,
                                                 lengths,
                                                 pwpd_r,  # it's already logged values
                                                 sigma = errs,
                                                 p0=[A,alph]) # sigma=pwpd_r_err,
                else:
                    popt, pcov = \
                        scipy.optimize.curve_fit(log_powerlaw,
                                                 lengths,
                                                 np.log(pwpd_r),
                                                 sigma = errs,
                                                 p0=[A,alph]) # sigma=pwpd_r_err,
                A = popt[0]
                A_err = np.sqrt(pcov[0][0])
                alph = -1.0*popt[1]
                alph_err = np.sqrt(pcov[1][1])
                if firsttry:
                    firsttry=False
                else:
                    print("***single power fit:")
                    print(f"A={A:.2e}; alph={alph:.2e}")
                    print(f"A_err={A_err:.1e}; alph_err={alph_err:.1e}")
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
                        textstring1 = r'$A = $'+ f"{A:.2f}" \
                            + r'$\pm$' + f"{A_err:.2f}"
                        textstring2 = r'$\alpha = $'+ f"{alph:.3f}" \
                            + r'$\pm$' + f"{alph_err:.3f}"
                        ax.text(0.1, 0.15, textstring1, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                        ax.text(0.1, 0.1, textstring2, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                    # Return the parameters found
                    return A, A_err, 0.0, 0.0, alph, alph_err, 0.0, 0.0, 0.0, 0.0
            except RuntimeError:
                print("***Error: could not even fit a power law!")
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

# load the databases (health regions, names, ...)
load_all_databases()
# make pwpd database w/ province names and "shortnames" of H Regions
if (Pars.startrow == 0):
    create_new_database()
else:
    # Read in most recent version of the csv file
    Pars.pwpd_regions = pd.read_csv(Pars.csv_out_filename, index_col=0)
# loop over counties, mask GHS, calculate pwpd
if (Pars.plot_pwpd):
    plotdir = 'plots'
for index, row in Pars.pwpd_regions.iterrows():
    if ( (index >= Pars.startrow) & (index <= Pars.stoprow) ):
        if (Pars.plot_pwpd):
            fig,ax = plt.subplots(figsize=(8,8))
        # get corresponding health region polygon
        region = Pars.HRegions.loc[[index]]
        # print name of health region for user
        code = int(row['HR_UID'])
        province = row['ProvinceName']
        regionname = row['shortname']
        print("================ " + str(index) + " "
              + str(code) + " " + regionname + ", " + province
              + " ================")
        # transform to Mollweide
        region_m = region.to_crs(crs=Pars.eps_mollweide)
        # mask GHS-POP image on health region, get raster subimage
        img, img_transform = get_GHS_windowed_subimage(region_m)
        imarr = np.array(img)
        area = np.sum(imarr == Pars.GHS_nodataval)*0.25**2
        imarr[(imarr == Pars.GHS_nodataval)] = 0.0
        # calculate population and PWPD
        pop = np.sum(imarr)
        Pars.pwpd_regions.loc[index, 'POP'] = pop
        if (pop > 0):
            pwpd = np.sum(np.multiply(imarr, imarr)) \
                / Pars.GHS_Acell_in_kmsqd / pop
            nonzero = (imarr > 0)
            pwlogpd = np.sum(np.multiply(np.log(imarr[nonzero]/Pars.GHS_Acell_in_kmsqd),
                                         imarr[nonzero]))/pop
            Pars.pwpd_regions.loc[index, 'PWPD'] = pwpd
            Pars.pwpd_regions.loc[index, 'PWLOGPD'] = pwlogpd
        else:
            Pars.pwpd_regions.loc[index, 'PWPD'] = 0.0            
        # get regular population density
        #      found area using:
        #          https://gis.stackexchange.com/questions/218450
        #      but this doesn't give the right values.. about a factor of 2 large
        #
        #region_copy = region.copy()
        #region_copy = region_copy.to_crs({'init': 'epsg:3857'})
        #area = region_copy['geometry'].area.tolist()[0]/10**6
        Pars.pwpd_regions.loc[index, 'landarea'] = area
        popdensity = pop/area
        print(f"PWPD (250km) = {pwpd:.0f}   POP = {pop:.0f}   AREA = {area:.0f} km^2  POPDENS = {popdensity:.1f} / km^2")
        if ((pop > 0)):   #& (statecountyfips != '02016')):  # can't do aleutians
            # get parameters for pwpd vs scalelength
            if Pars.do_pwpd_vs_scalelength:
                for logstr in ['', 'LOG']:
                    if (logstr == 'LOG'):
                        Pars.plot_pwpd = True  # for now, only plot the new ones
                        A, A_err, xb, xb_err, al1, al1_err, al2, al2_err, delt, delt_err = \
                            get_fit_of_pwpd_vs_scalelength(ax, imarr, popdensity, type='LOG')
                    else:
                        Pars.plot_pwpd = False
                        A, A_err, xb, xb_err, al1, al1_err, al2, al2_err, delt, delt_err = \
                            get_fit_of_pwpd_vs_scalelength(ax, imarr, popdensity, type='STD')
                    # put parameters into csv file
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_A'] = A
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_A_ERR'] = A_err
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_XBREAK'] = xb
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_XBREAK_ERR'] = xb_err
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_ALPHA1'] = al1
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_ALPHA1_ERR'] = al1_err
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_ALPHA2'] = al2
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_ALPHA2_ERR'] = al2_err
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_DELTA'] = delt
                    Pars.pwpd_regions.loc[index, 'PW' + logstr + 'PD_DELTA_ERR'] = delt_err
                if ((index % 10) == 0):
                    # write pwpd dataframe to csv
                    Pars.pwpd_regions.to_csv(Pars.csv_out_filename)
                if (Pars.plot_pwpd):
                    ax.set_title(countyname + " --- " + statecountyfips)
                    filename = plotdir + '/' + statecountyfips + '.pdf'
                    fig.savefig(filename)
                    plt.close(plt.gcf())
                    sys.stdout.flush()
                    sys.stderr.flush()
        else:
            # put zeros for all parameters into csv file
            Pars.pwpd_regions.loc[index, 'PWPD_A'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_A_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_XBREAK'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_XBREAK_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_ALPHA1'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_ALPHA1_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_ALPHA2'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_ALPHA2_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_DELTA'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWPD_DELTA_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_A'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_A_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_XBREAK'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_XBREAK_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_ALPHA1'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_ALPHA1_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_ALPHA2'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_ALPHA2_ERR'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_DELTA'] = 0.0
            Pars.pwpd_regions.loc[index, 'PWLOGPD_DELTA_ERR'] = 0.0

# write pwpd dataframe to csv
Pars.pwpd_regions.to_csv(Pars.csv_out_filename)
if (Pars.plot_pwpd):
    plt.close(fig)