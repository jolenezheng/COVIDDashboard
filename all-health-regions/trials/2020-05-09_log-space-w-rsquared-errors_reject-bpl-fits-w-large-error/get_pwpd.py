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
    fips_filepath = countiespath + 'state-fips.csv' #'2017FIPS/all-geocodes-v2017.csv'
    fipscodes = None
    # guam, virgin islands, manu'a, etc don't have state-fips
    #fips_excluded_states = [78, 66, 69, 60]
    #ignorerows = [2391]  # shelby county KY seems bad?
    # database for output
    pwpd_counties = None
    csv_out_filename = 'pwpd_counties.csv'

    # plotting and fitting pwpd vs scalelength
    do_pwpd_vs_scalelength = True
    plot_pwpd = True
    fit_with_delta = False
    delta_fixedval = 0.1
    plot_domain = [0.09, 300.0]
    startrow = 0   # 608 is albany
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
    for index, row in Pars.pwpd_counties.iterrows():
        f = int(row['STATEFP'])
        Pars.pwpd_counties.loc[index, 'STATENAME'] = \
            Pars.fipscodes[(Pars.fipscodes['FIPS'] == f)]['State Name'].tolist()[0]
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
    pwpd = np.sum(np.multiply(arr,arr) / lengthscale_km**2 / totalpop)
    # see just before fit, using errors proposed by niayesh
    #pwpd_err = 2.0/(np.sqrt(totalpop) * lengthscale_km**2)
    return pwpd

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

def log_powerlaw(x, A, alpha):
    return np.log(A*np.power(x,alpha))

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

def log_broken_powerlaw_nodelta(x, A, x0, alpha1, alpha2):
    """
    Using the equation given here:
      docs.astropy.org/en/stable/api/
         astropy.modeling.powerlaws.SmoothlyBrokenPowerLaw1D.html
    """
    delta = Pars.delta_fixedval  # fixed
    return np.log(
        A*np.power(x/x0, -alpha1)
        *np.power(1/2.0*(1 + np.power(x/x0,1.0/delta)),
                  (alpha1-alpha2)*delta)
        )

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
            goodpts = (pwpd_r > 0)
            popt, pcov = \
                scipy.optimize.curve_fit(log_broken_powerlaw_nodelta,
                                         lengths[goodpts],
                                         np.log(pwpd_r[goodpts]),
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
            # The parameter we will output is:
            #
            #     Aprime = A*(1/xb)^(-alpha1) * (1/2)^(delta*(alpha1-alpha2))
            #
            # where, for x<<xb, we have
            #
            #     f(x) = Aprime x^(-alpha1)
            #
            # so "Aprime" for the broken power law and "A" of the power
            # law are the same.
            delta = Pars.delta_fixedval  # fixed
            Aprime = A*(1/xb)**(-1.0*alph1) * (1/2)**(delta*(alph1-alph2))
            # and now propagating the error to get Aprime_err
            sig_onehalf_tothe_dotdotdot = np.sqrt(
                (1.0/2)**(2.0*delta*(alph1-alph2))
                * (delta*np.log(1.0/2)*(alph1_err**2 + alph2_err**2))**2
                )
            #print(sig_onehalf_tothe_dotdotdot)
            sig_one_over_xb = xb_err/(xb**2)
            #print(sig_one_over_xb)
            sig_one_over_xb_to_minus_alpha1 = np.sqrt(
                (1.0/xb)**(-2.0*alph1)
                * ( ((-1.0*alph1/(1.0/xb))*sig_one_over_xb)**2
                    + (np.log(1.0/xb) * alph1_err)**2 )
                )
            # f this: + 2.0*(-1.0*alph1)*np.log(1.0/xb)/(1.0/xb)*sig_AB
            #print(sig_one_over_xb_to_minux_alpha1)
            Aprime_err = np.sqrt(
                Aprime**2
                * ( ( A_err / A )**2
                    + ( sig_one_over_xb_to_minus_alpha1 / ((1.0/xb)**(-1.0*alph1)) )**2
                    + ( sig_onehalf_tothe_dotdotdot / ((1.0/2)**(delta*(alph1-alph2))) )**2
                    )
                )
            print(f"A={A:.2e}; Ap={Aprime:.2e}; xb={xb:.2e}; alph1={alph1:.2e}; alph2={alph2:.2e}")
            print(f"Aerr={A_err:.2e}  Ap_err={Aprime_err:.1e}; xb_err={xb_err:.1e}; alph1_err={alph1_err:.1e}; alph2_err={alph2_err:.1e}")
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
            textstring1 = r'$A^{\prime} = $' + f"{Aprime:.2e}" + r'$\pm$' \
                + f"{Aprime_err:.1e}"
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
            # Return the parameters and their variances
            return Aprime, Aprime_err, xb, xb_err, alph1, alph1_err, alph2, alph2_err, \
                Pars.delta_fixedval, 0.0
        except RuntimeError:
            try:
                # Fit a single power law
                popt, pcov = \
                    scipy.optimize.curve_fit(log_powerlaw,
                                             lengths[goodpts],
                                             np.log(pwpd_r[goodpts]),
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
                        textstring1 = r'$\alpha = $'+ f"{alph:.2f}" \
                            + r'$\pm$' + f"{alph_err:.2f}"
                        textstring2 = r'$A = $'+ f"{A:.2f}" \
                            + r'$\pm$' + f"{A_err:.2f}"
                        ax.text(0.1, 0.2, textstring1, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                        ax.text(0.1, 0.1, textstring2, horizontalalignment = 'left',
                                verticalalignment='center',transform=ax.transAxes)
                    # Return the parameters found
                    return A, A_err, 0.0, 0.0, alph, alph_err, 0.0, 0.0, 0.0, 0.0
            except RuntimeError:
                print("***Error: could not even fit a power law!")
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

# load the counties polygons and statefips databases
load_all_databases()
# make pwpd database w/ state names too
if (Pars.startrow == 0):
    create_new_database()
else:
    # Read in most recent version of the csv file
    Pars.pwpd_counties = pd.read_csv(Pars.csv_out_filename, index_col=0)
# loop over counties, mask GHS, calculate pwpd
if (Pars.plot_pwpd):
    plotdir = 'plots'
for index, row in Pars.pwpd_counties.iterrows():
    if ( (index >= Pars.startrow) & (index <= Pars.stoprow) ):
        if (Pars.plot_pwpd):
            fig,ax = plt.subplots(figsize=(8,8))
        # get corresponding county polygon
        county = Pars.UScounties.loc[[index]]
        # print name of county for user
        statefips=  int(row['STATEFP'])
        countyfips = int(row['COUNTYFP'])
        statecountyfips = f"{statefips:02}{countyfips:03}"
        countyname = row['NAME'] + ", " + row['STATENAME']
        print("================ " + str(index) + " "
              + statecountyfips + " " + countyname
              + " ================")
        # transform to Mollweide
        county_m = county.to_crs(crs=Pars.eps_mollweide)
        # mask GHS-POP image on county, get raster subimage
        img, img_transform = get_GHS_windowed_subimage(county_m)
        imarr = np.array(img)
        imarr[(imarr == Pars.GHS_nodataval)] = 0.0
        # calculate population and PWPD
        pop = np.sum(imarr)
        Pars.pwpd_counties.loc[index, 'POP'] = pop
        if (pop > 0):
            pwpd = np.sum(np.multiply(imarr, imarr)) \
                / Pars.GHS_Acell_in_kmsqd / pop
            Pars.pwpd_counties.loc[index, 'PWPD'] = pwpd
        else:
            Pars.pwpd_counties.loc[index, 'PWPD'] = 0.0            
        # get regular population density
        area = float(row['ALAND'])/1e6
        popdensity = pop/area
        print(f"PWPD (250km) = {pwpd:.0f}   POP = {pop:.0f}   AREA = {area:.0f} km^2  POPDENS = {popdensity:.1f} / km^2")
        if ((pop > 0) & (statecountyfips != '02016')):  # can't do aleutians
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
                if ((index % 10) == 0):
                    # write pwpd dataframe to csv
                    Pars.pwpd_counties.to_csv(Pars.csv_out_filename)
                if (Pars.plot_pwpd):
                    ax.set_title(countyname + " --- " + statecountyfips)
                    filename = plotdir + '/' + statecountyfips + '.pdf'
                    fig.savefig(filename)
                    plt.close(plt.gcf())
                    sys.stdout.flush()
                    sys.stderr.flush()
        else:
            # put zeros for all parameters into csv file
            Pars.pwpd_counties.loc[index, 'PWPD_A'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_A_ERR'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_XBREAK'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_XBREAK_ERR'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA1'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA1_ERR'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA2'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_ALPHA2_ERR'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_DELTA'] = 0.0
            Pars.pwpd_counties.loc[index, 'PWPD_DELTA_ERR'] = 0.0

# write pwpd dataframe to csv
Pars.pwpd_counties.to_csv(Pars.csv_out_filename)
if (Pars.plot_pwpd):
    plt.close(fig)
