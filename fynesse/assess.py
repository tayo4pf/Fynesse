from .config import *

from . import access, address
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd

"""Place commands in this file to assess the data you have downloaded. How are missing values encoded, how are outliers encoded? What do columns represent, makes rure they are correctly labeled. How is the data indexed. Crete visualisation routines to assess the data (e.g. in bokeh). Ensure that date formats are correct and correctly timezoned."""

def query(query, columns):
    """
    Request user input for some aspect of the data.
    :param query: The database query to be performed to select the data
    :param columns: The columns to be selected in the query
    :return: Dataframe containing the data selected from the database
    """
    data = access.get_rows_from_query(query)
    data = np.vstack(data)
    if len(data) == 0:
        raise ValueError("No data matches the query")
    if len(columns) != len(data[0]):
        raise ValueError(f"Number of columns in the dataframe({len(columns)}) must match number of columns selected in the query({len(data[0])})")
    df = pd.DataFrame({
        column: data[:,i] for i, column in enumerate(columns)
        })
    return df

def view(df, x_col, y_cols):
    """
    Provide a view of the data that allows the user to verify some aspect of its quality.
    :param df: The dataframe containing the columns to be visualized
    :param x_col: The name of the column to be visualized as the x-axis
    :param y_col: List of column names to be visualized as the y_axis
    """
    if x_col not in df:
        raise ValueError(f"Column {x_col} is not in the dataframe provided")
    for y_col in y_cols:
        if y_col not in df:
            raise ValueError(f"Column {y_col} is not in the dataframe provided")
    df = df.sort_values(by=x_col)
    for y_col in y_cols:
        plt.plot(df[x_col], df[y_col], label=y_col)
    plt.xlabel(x_col)
    plt.legend()
    plt.show()

def labelled(data, columns):
    """
    Provide a labelled set of data ready for supervised learning.
    Provide a dataframe from a set of rows of data
    :param data: tuple tuple of datapoints
    :param columns: list of column names for the dataframe
    :return: Dataframe containining the labelled data
    """
    if len(data) == 0:
        raise ValueError("No data matches the query")
    if len(columns) != len(data[0]):
        raise ValueError(f"Number of columns in the dataframe({len(columns)}) must match number of columns selected in the query({len(data[0])})")
    data = np.vstack(data)
    df = pd.DataFrame({
        column: data[:, i] for i, column in enumerate(columns)
    })
    return df

def df_from_year(year):
    """
    Provide a dataframe of price-coordinates data from a specified year
    :param year: The year of data to be selected
    :return: Dataframe containing the labelled data
    """
    cols = ("Postcode", "Price", "Date", "Property Type", "New Build Flag", "Tenure Type", 
        "Locality", "Town/City", "District", "County", "Positional Quality Indicator",
        "Country", "Latitude", "Longitude")
    pcdf1, pcdf2 = pd.read_csv(f"pcd/pc-{year}-part1.csv", names = cols), pd.read_csv(f"pcd/pc-{year}-part2.csv", names = cols)
    pcdf = pd.concat((pcdf1, pcdf2))
    return pcdf

def plot_gdf_col_heatmap(gdf, col):
    world_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world_gdf.crs = "EPSG:4326"
    uk_gdf = world_gdf[np.in1d(world_gdf['name'],['England', 'Wales', 'Scotland', 'Northern Ireland', 'Channel Islands', 'Isle of Man'])]
    base = uk_gdf.plot(color='white', edgecolor='black', alpha=0, figsize=(11,11))
    gdf.plot(ax=base, column=col, legend=True)
    
def plot_price_predictions(df, x=None, args=None, prices=False):
    """
    Plots the price predictions for a dataframe of property sales
    :param df: The dataframe containing the property sale data ("Longitude", "Latitude", "Date", "Property Type")
    :param x: The column of the dataframe to be used as the x-axis for the plot
    :param args: The parameters to be used for price predictions (optional)
    :param prices: The true sale prices for the properties (optional)
    """
    if not ("Latitude" in df and "Longitude" in df and "Date" in df and "Property Type" in df):
        raise ValueError(f"df must contain columns 'Latitude', 'Longitude', 'Date', and 'Property Type', {df.columns} is not sufficient")
    if prices and "Price" not in df:
        raise ValueError(f"df must contain column 'Price' if prices is True, {df.columns} is not sufficient")
    if x is None:
        col = "Date"
    else:
        col = x
    df = df.sort_values(by=col)
    price_preds = []
    for latitude, longitude, date, pt in zip(df["Latitude"], df["Longitude"], df["Date"], df["Property Type"]):
        if args is not None:
            p, _ = address.predict_price_parameterized(args, latitude, longitude, date, pt)
        else:
            p, _ = address.predict_price(latitude, longitude, date, pt)
        price_preds.append(p)
    fig = plt.figure(figsize=(10,5))
    ax = fig.add_subplot(111)
    
    ax.plot(df[col], price_preds, color='red', linestyle='--', zorder=1)
    if prices is not None:
        ax.plot(df[col], df["Price"], zorder=2)
    ax.set_xlabel(col)
    plt.tight_layout()

def price_predictions(df, args=None):
    """
    Returns list of price predictions for a dataframe of property sales
    :param df: The dataframe containing the property sale data ("Longitude", "Latitude", "Date", "Property Type")
    :param args: The parameters to be used for price predictions (optional)
    :return: List of price predictions
    """
    if not ("Latitude" in df and "Longitude" in df and "Date" in df and "Property Type" in df):
        raise ValueError(f"df must contain columns 'Latitude', 'Longitude', 'Date', and 'Property Type', {df.columns} is not sufficient")
    price_preds = []
    for latitude, longitude, date, pt in zip(df["Latitude"], df["Longitude"], df["Date"], df["Property Type"]):
        if args is not None:
            p, _ = address.predict_price_parameterized(args, latitude, longitude, date, pt)
        else:
            p, _ = address.predict_price(latitude, longitude, date, pt)
        price_preds.append(p)
    return price_preds