from .config import *

from . import access
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

"""Place commands in this file to assess the data you have downloaded. How are missing values encoded, how are outliers encoded? What do columns represent, makes rure they are correctly labeled. How is the data indexed. Crete visualisation routines to assess the data (e.g. in bokeh). Ensure that date formats are correct and correctly timezoned."""

def random_sample(table, condition, size):
    query = f"SELECT * FROM {table} WHERE {condition}"
    rows = access.get_rows_from_query()
    return np.random.choice(rows, size)

def query(query, columns):
    """Request user input for some aspect of the data."""
    data = access.get_rows_from_query(query)
    assert len(columns) == len(data[0])

def view(data):
    """
    Provide a view of the data that allows the user to verify some aspect of its quality.
    Provide a datafram with two columns, first column will be the x-axis, and the second column will be the y-axis
    """
    assert len(data.columns) == 2
    x_ax = data.columns[0]
    y_ax = data.columns[1]
    plt.plot(data[x_ax], data[y_ax])
    plt.xlabel(x_ax)
    plt.ylabel(y_ax)
    plt.show()

def labelled(data, columns):
    """Provide a labelled set of data ready for supervised learning."""
    assert len(columns) == len(data[0])
    data = np.vstack(data)
    df = pd.DataFrame({
        col: data[:, i] for i, col in enumerate(columns)
    })
    return df
