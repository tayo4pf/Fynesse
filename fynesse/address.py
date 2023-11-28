# This file contains code for suporting addressing questions in the data

"""Address a particular question that arises from the data"""

import pandas as pd
import pygeohash as gh
import numpy as np
import datetime
import pymysql
import yaml
import statsmodels.api as sm
from fynesse import access, assess
from scipy import optimize

def predict_price_parameterized(args, latitudes, longitudes, dates, property_types):
    """
    Price prediction for UK housing with parameters
    Returns performance of model with parameters
    Access username, password, host, and database config must be specified
    """

    d, t, h = args
    d = d * (0.02/2.2)
    pt = {"days": t}
    mt = {"days": -t}

    #Finding bounds for latitude and longitude
    box_width = d * (0.02/2.2)
    box_height = d * (0.02/2.2)
    price_preds = []
    results = []
    for latitude, longitude, date, property_type in zip(latitudes, longitudes, dates, property_types):
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
            price_preds.append(np.nan)
            results.append(f"Insufficient data to form model: {len(rows)} datapoints in bounding area")
            continue
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
        m_results = m.fit()
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
        price_pred = m_results.predict(design_pred)
        price_preds.append(price_pred[0])
        results.append(m_results)
    price_preds = np.array(price_preds)
    return price_preds, results

def predict_price(latitude, longitude, date, property_type):
    """
    Price prediction for UK housing.
    """
    
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
    m_results = m.fit()
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
    return m_results.predict(design_pred)[0]