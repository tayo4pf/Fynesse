# This file contains code for suporting addressing questions in the data

"""Address a particular question that arises from the data"""

import pandas as pd
import pygeohash as gh
import numpy as np
import datetime
import statsmodels.api as sm
from fynesse import access, assess
from itertools import product

def predict_price_parameterized(args, latitude, longitude, date, property_type):
    """
    Price prediction for UK housing with parameters
    This may be used for the prediction of the sale price of an atypical sale, for example a sale far into the future
    or the sale of a property that is far away from any other properties
    :param args: tuple of the length in km of the bounding box square, the amount of days around the date to bound
    the search by, and the precision of the geohash to be used
    :param latitude: The latitude of the property
    :param longitude: The longitude of the property
    :param date: The date of the property sale (datetime object)
    :param property_type: The property type enum of the property (F, S, D, T, O)
    :return: tuple of predicted price, r squared, and model results
    """

    d, t, h = args
    d = d * (0.02/2.2)
    pt = {"days": t}
    mt = {"days": -t}

    #Finding bounds for latitude and longitude
    box_width = d * (0.02/2.2)
    box_height = d * (0.02/2.2)
    north = latitude + (box_height/2)
    south = latitude - (box_height/2)
    west = longitude - (box_width/2)
    east = longitude + (box_width/2)

    #Finding bounds for date
    latest_date = date + datetime.timedelta(**pt)
    earliest_date = date + datetime.timedelta(**mt)

    #Getting data according to bounds
    rows = access.get_rows_in_bounds(north, south, west, east, latest_date, earliest_date)
    if len(rows) == 0:
        return np.nan, -float('inf'), f"Insufficient data to form model: {len(rows)} datapoints in bounding area"
    df = assess.labelled(rows, ("Postcode", "Price", "Date", "Property Type", "New Build Flag", "Tenure Type", 
        "Locality", "Town/City", "District", "County", "Positional Quality Indicator",
        "Country", "Latitude", "Longitude", "ID"))
    df["Geohash"] = df.apply(lambda x: gh.encode(x["Latitude"], x["Longitude"], precision=h), axis=1)

    property_type_oh = np.array([np.array([
        1 if p == "F" else 0,
        1 if p == "S" else 0,
        1 if p == "D" else 0,
        1 if p == "T" else 0,
        1 if p == "O" else 0
        ]) for p in df["Property Type"]])
    geohash_oh = np.array([np.array([
        1 if g == encoding else 0 for encoding in df["Geohash"].unique()
    ]) for g in df["Geohash"]])
    np_ord = np.vectorize(lambda x: x.toordinal())

    design = np.concatenate((np_ord(df["Date"]).reshape(-1, 1), property_type_oh, geohash_oh), axis=1)

    m = sm.OLS(np.array(df["Price"]).reshape(-1, 1), design)
    try:
        m_results = m.fit_regularized(alpha=0.1, L1_wt=0)
    except:
        return np.nan, np.nan, "SVD could not fit the model on given data" 
    property_oh_pred = np.array([np.array([
        1 if property_type == "F" else 0,
        1 if property_type == "S" else 0,
        1 if property_type == "D" else 0,
        1 if property_type == "T" else 0,
        1 if property_type == "O" else 0
    ])])
    geohash = gh.encode(latitude, longitude, precision=h)
    geohash_oh = np.array([np.array([
        1 if geohash == encoding else 0 for encoding in df["Geohash"].unique()
    ])])
    design_pred = np.concatenate(
        (np.array([date.toordinal()]).reshape(-1, 1), property_oh_pred, geohash_oh), axis=1
    )
    p_array = np.array(df["Price"])
    rss = np.sum(np.square(m_results.fittedvalues - p_array))
    tss = np.sum(np.square(p_array - np.mean(p_array)))
    return m_results.predict(design_pred)[0], (1-(rss/tss)), m_results

def predict_price(latitude, longitude, date, property_type, optimize=False):
    """
    Price prediction for UK housing.
    :param latitude: Latitude of the property
    :param longitude: Longitude of the property
    :param date: The date of the property sale (datetime object)
    :param property_type: The property type enum of the property (F, S, D, T, O)
    :param optimize: When true, find the combination of parameters that provide the model with the highest r squared (optional)
    :return: tuple of predicted price, r squared, and model results
    """
    
    if optimize:
        return max(
        (predict_price_parameterized(a, latitude, longitude, date, property_type) for a in product((10, 25, 50), (730, 365, 180), (3, 5, 7))), 
        key = lambda x: -float('inf') if isinstance(x[2], str) else x[1]
               )
    else:
        d, t, h = (50, 365, 5)
    d = d * (0.02/2.2)
    pt = {"days": t}
    mt = {"days": -t}

    #Finding bounds for latitude and longitude
    box_width = d * (0.02/2.2)
    box_height = d * (0.02/2.2)

    north = latitude + (box_height/2)
    south = latitude - (box_height/2)
    west = longitude - (box_width/2)
    east = longitude + (box_width/2)

    #Finding bounds for date
    latest_date = date + datetime.timedelta(**pt)
    earliest_date = date + datetime.timedelta(**mt)

    rows = access.get_rows_in_bounds(north, south, west, east, latest_date, earliest_date)
    if len(rows) == 0:
        return np.nan, -float('inf'), f"Insufficient data to form model: {len(rows)} datapoints in bounding area"
    df = assess.labelled(rows, ("Postcode", "Price", "Date", "Property Type", "New Build Flag", "Tenure Type", 
        "Locality", "Town/City", "District", "County", "Positional Quality Indicator",
        "Country", "Latitude", "Longitude", "ID"))
    df["Geohash"] = df.apply(lambda x: gh.encode(x["Latitude"], x["Longitude"], precision=h), axis=1)

    property_type_oh = np.array([np.array([
        1 if p == "F" else 0,
        1 if p == "S" else 0,
        1 if p == "D" else 0,
        1 if p == "T" else 0,
        1 if p == "O" else 0
        ]) for p in df["Property Type"]])
    geohash_oh = np.array([np.array([
        1 if g == encoding else 0 for encoding in df["Geohash"].unique()
    ]) for g in df["Geohash"]])
    np_ord = np.vectorize(lambda x: x.toordinal())

    design = np.concatenate((np_ord(df["Date"]).reshape(-1, 1), property_type_oh, geohash_oh), axis=1)

    m = sm.OLS(np.array(df["Price"]).reshape(-1, 1), design)
    m_results = m.fit_regularized(alpha=0.1, L1_wt=0)
    property_oh_pred = np.array([np.array([
        1 if property_type == "F" else 0,
        1 if property_type == "S" else 0,
        1 if property_type == "D" else 0,
        1 if property_type == "T" else 0,
        1 if property_type == "O" else 0
    ])])
    geohash = gh.encode(latitude, longitude, precision=h)
    geohash_oh = np.array([np.array([
        1 if geohash == encoding else 0 for encoding in df["Geohash"].unique()
    ])])
    design_pred = np.concatenate(
        (np.array([date.toordinal()]).reshape(-1, 1), property_oh_pred, geohash_oh), axis=1
    )
    p_array = np.array(df["Price"])
    rss = np.sum(np.square(m_results.fittedvalues - p_array))
    tss = np.sum(np.square(p_array - np.mean(p_array)))
    return m_results.predict(design_pred)[0], (1-(rss/tss)), m_results

def price_predictions(df, args=None, optimize=False):
    """
    Returns list of price predictions, and r squared values for a dataframe of property sales
    :param df: The dataframe containing the property sale data ("Longitude", "Latitude", "Date", "Property Type")
    :param args: The parameters to be used for price predictions (optional)
    :param optimize: When True, find the combination of parameters that provide the model with the highest r squared (optional)
    :return: List of price predictions
    """
    if not ("Latitude" in df and "Longitude" in df and "Date" in df and "Property Type" in df):
        raise ValueError(f"df must contain columns 'Latitude', 'Longitude', 'Date', and 'Property Type', {df.columns} is not sufficient")
    price_preds = []
    rs = []
    for latitude, longitude, date, pt in zip(df["Latitude"], df["Longitude"], df["Date"], df["Property Type"]):
        if args is not None:
            p, r, _ = predict_price_parameterized(args, latitude, longitude, date, pt)
        else:
            p, r, _ = predict_price(latitude, longitude, date, pt, optimize=optimize)
        price_preds.append(p)
        rs.append(r)
    return price_preds, rs