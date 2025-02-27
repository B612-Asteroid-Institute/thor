import numpy as np
import pandas as pd
from astropy.time import Time

from ..config import Config

__all__ = [
    "writeADESHeader",
    "writeToADES"
]

def writeADESHeader(
        observatory_code, 
        submitter, 
        telescope_design,
        telescope_aperture,
        telescope_detector,
        observers,
        measurers,
        observatory_name=None,
        submitter_institution=None,
        telescope_name=None,
        comment=None
    ):
    """
    Write the ADES PSV headers.

    Parameters
    ----------
    observatory_code : str
        MPC-assigned observatory code
    submitter : str
        Submitter's name. 
    telescope_design : str
        Telescope's design, eg. Reflector.
    telescope_aperture : str
        Telescope's primary aperture in meters. 
    telescope_detector : str
        Telescope's detector, eg. CCD.
    observers : list of str
        First initial and last name (J. Smith) of each of the observers. 
    measurers : list of str
        First initial and last name (J. Smith) of each of the measurers. 
    observatory_name : str, optional
        Observatory's name. 
    submitter_insitution : str, optional
        Name of submitter's institution.
    telescope_name : str, optional
        Telescope's name. 
    comment : str
        Additional comment to add to the ADES header.


    Returns
    -------
    list : str
        A list of each line in the ADES header. 
    """
    # Start header with version number
    header = [
        "# version=2017",
    ]
    
    # Add observatory [required]
    header += ["# observatory"]
    header += ["! mpcCode {}".format(observatory_code)]
    if observatory_name is not None:
        header += ["! name {}".format(observatory_name)]
    
    # Add submitter [required]
    header += ["# submitter"]
    header += ["! name {}".format(submitter)]

    if submitter_institution is not None:
        header += ["! institution {}".format(submitter_institution)]

    # Add telescope details [required]
    header += ["# telescope"]
    if telescope_name is not None:
        header += ["! name {}".format(telescope_name)]
    header += ["! aperture 8.4"]
    header += ["! design {}".format(telescope_design)]
    header += ["! detector {}".format("CCD")]

    # Add observer details
    header += ["# observers"]
    if type(observers) is not list:
        err = (
            "observers should be a list of strings."
        )
        raise ValueError(err)
    for name in observers:
        header += ["! name {}".format(name)]

    # Add measurer details
    header += ["# measurers"]
    if type(measurers) is not list:
        err = (
            "measurers should be a list of strings."
        )
        raise ValueError(err)
    for name in measurers:
        header += ["! name {}".format(name)]

    # Add comment
    if comment is not None:
        header += ["# comment"]
        header += ["! line {}".format(comment)]
        
    header = [i + "\n" for i in header]
    return header

def writeToADES(
        observations, 
        file_out,
        mjd_scale="utc",
        seconds_precision=9,
        observatory_code=Config.ADES_METADATA["observatory_code"],
        submitter=Config.ADES_METADATA["submitter"], 
        telescope_design=Config.ADES_METADATA["telescope_design"],
        telescope_aperture=Config.ADES_METADATA["telescope_aperture"],
        telescope_detector=Config.ADES_METADATA["telescope_detector"],
        observers=Config.ADES_METADATA["observers"],
        measurers=Config.ADES_METADATA["measurers"],
        comment=None
    ):
    """
    Save observations to a MPC-submittable ADES psv file. 

    Parameters
    ----------
    observations : `~pandas.DataFrame`
        Dataframe containing observations. 
    file_out : str
        Path and name to save out 
    mjd_scale : str, optional
        Time scale of MJD observation times 
    seconds_precision : int, optional
        Number of decimal places of precision on the measurement 
        of seconds for the observation times. The ADES format can handle higher
        than ms precision if the observations warrant such accuracy. 0.1 ms precision
        would be expressed as 4 while ms precision would be expressed as 3. 
    observatory_code : str, optional
        MPC-assigned observatory code
    submitter : str, optional
        Submitter's name. 
    telescope_design : str, optional
        Telescope's design, eg. Reflector.
    telescope_aperture : str, optional
        Telescope's primary aperture in meters. 
    telescope_detector : str, optional
        Telescope's detector, eg. CCD.
    observers : list of str, optional
        First initial and last name (J. Smith) of each of the observers. 
    measurers : list of str, optional
        First initial and last name (J. Smith) of each of the measurers. 
    comment : str, optional
        Additional comment to add to the ADES header.

    Returns
    -------
    list : str
        A list of each line in the ADES header. 
    """
    header = writeADESHeader(
        observatory_code, 
        submitter, 
        telescope_design,
        telescope_aperture,
        telescope_detector,
        observers,
        measurers,
        comment=comment
    )
    
    # Format columns from observations into PSV format
    ades = {}
    
    id_present = False
    if "permID" in observations.columns.values:
        ades["permID"] = observations["permID"].values
        id_present = True
    if "provID" in observations.columns.values:
        ades["provID"] = observations["provID"].values
        id_present = True
    if "trkSub" in observations.columns.values:
        ades["trkSub"] = observations["trkSub"].values
        id_present = True
    
    if not id_present:
        err = (
            "At least one of permID, provID, or trkSub should\n"
            "be present in observations."
        )
        raise ValueError(err)
    
    observation_times = Time(
        observations["mjd"].values,
        format="mjd",
        scale=mjd_scale,
        precision=seconds_precision
    )
    ades["obsTime"] = np.array([i + "Z" for i in observation_times.utc.isot])
    ades["ra"] = observations["ra"].values 
    ades["dec"] = observations["dec"].values

    if "rmsRA" in observations.columns.values:
        ades["rmsRA"] = observations["rmsRA"].values
    if "rmsDec" in observations.columns.values:
        ades["rmsDec"] = observations["rmsDec"].values
    
    ades["mag"] = observations["mag"].values
    if "rmsMag" in observations.columns.values:
        ades["rmsMag"] = observations["rmsMag"].values
    ades["band"] = observations["band"].values
    ades["stn"] = observations["stn"].values
    ades["mode"] = observations["mode"].values
    ades["astCat"] = observations["astCat"].values
    
    if "remarks" in observations.columns.values:
        ades["remarks"] = observations["remarks"].values

    # Create dataframe with formated data entries
    ades = pd.DataFrame(ades)
    col_header = "|".join(ades.columns) + "\n"
   
    with open(file_out, "w") as f:
        f.write("".join(header))
        f.write(col_header)
        
    ades = ades.replace(
        np.nan, 
        " ", 
        regex=True
    )
        
    ades.to_csv(
        file_out, 
        sep="|", 
        header=False, 
        index=False, 
        mode="a", 
        float_format='%.16f'
    )
    return 