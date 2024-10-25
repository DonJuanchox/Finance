import logging
import typing
from pandas import Series

def get_rate(logger: logging.Logger,
             dictionary: typing.Dict,
             sub_string: str) -> float:
    """
    Function to find a rate based on the substring (currency) in fx_rate

    Parameters
    ----------
    logger : logging.Logger
        Logger object.
    dictionary : typing.Dict
        Dictionary containing {currency: fx_rate}
    sub_string : str
        String which contains currency value to lookup

    Returns
    -------
    float
        FX rate for a given currency

    """
    
    for key in dictionary.keys():
        if sub_string in key:
            return dictionary[key]  # Return the rate from the dictionary
    logger.warning('No key contains the specified substring.')
    return None  # Return None if no matching key is found

def generate_id(row: Series,
                id_values: typing.List) -> str:
    """
    Create unique id given certain column values

    Parameters
    ----------
    row : Series
        Series containing some kind of data.
    id_values : typing.List
        List containing column names to extract data from.

    Returns
    -------
    unique_id : str
        Id for the given row.

    """

    unique_id = ''
    for values in id_values: unique_id += str(row[values])
    return unique_id
