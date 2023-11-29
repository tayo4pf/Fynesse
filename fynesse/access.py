from .config import *
import requests
import pymysql
import osmnx as ox
from functools import cache

# This file accesses the data

"""Place commands in this file to access the data electronically. Don't remove any missing values, or deal with outliers. Make sure you have legalities correct, both intellectual property and personal data privacy rights. Beyond the legal side also think about the ethical issues around this data. """

def download_url(folder, filename, url):
    """
    Save data from specified url to the filepath specified by folder and filename
    : param folder: The folder to save the data to
    : param filename: The name of the file to be saved to
    : param url: The url the data should be downloaded from
    """
    r = requests.get(url, allow_redirects=True)
    open(f"{folder}/{filename}", "wb").write(r.content)

def make_conn():
    """
    Create a database connection using the access.config mapping
    : return: Connection object
    """
    if "username" in config and "password" in config and "host" in config and "database" in config:
        if "port" not in config:
            port = 3306
        return create_connection(config["username"], config["password"], config["host"], config["database"], port)
    raise NotImplementedError("Specify connection details in access.config mapping")

def create_connection(user, password, host, database, port = 3306):
    """ Create a database connection to the MariaDB database
        specified by the host url and database name.
    :param user: username
    :param password: password
    :param host: host url
    :param database: database
    :param port: port number
    :return: Connection object or None
    """
    conn = None
    try:
        conn = pymysql.connect(user=user,
                               passwd=password,
                               host=host,
                               port=port,
                               local_infile=1,
                               db=database
                               )
    except Exception as e:
        print(f"Error connecting to the MariaDB Server: {e}")
    return conn

def select_top(table, n, conn = None):
    """
    Query n first rows of the table
    :param table: The table to query
    :param n: Number of rows to query
    :param conn: the Connection object (optional)
    :return: tuple tuple of the first n rows of the table
    """
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table} LIMIT {n}')

    rows = cur.fetchall()
    return rows

def head(table, n=5, conn = None):
    """
    Prints n first rows of the table
    :param table: The table to query
    :param conn: the Connection object (optional)
    """
    if conn is None:
        conn = make_conn()
    rows = select_top(table, n, conn = conn)
    for r in rows:
        print(r)

def upload_file(filename, table, conn = None):
    """
    Uploads file in the specified path to the specified table and commit connection
    :param filename: The path to the file to be uploaded
    :param table: The table to be uploaded to
    :param conn: the Connection object (optional)
    """
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    load_data = f"""LOAD DATA LOCAL INFILE '{filename}' INTO TABLE {table} FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES STARTING BY '' TERMINATED BY '\n';"""
    cur.execute(load_data)
    conn.commit()

def local_features(latitude, longitude, width_km, height_km):
    """
    Finds the features within the specified bounding box, returns dataframe with the number of each amenity
    :param latitude: The latitude central to the bounding box
    :param longitude: The longitude central to the bounding box
    :param width_km: The width of the bounding box in km (approx)
    :param height_km: The height of the bounding box in km (approx)
    :return: Dataframe object with the number of each amenity in the bounding box
    """
    box_width = width_km * (0.02/2.2)
    box_height = height_km * (0.02/2.2)

    north = latitude + (box_height/2)
    south = latitude - (box_height/2)
    west = longitude - (box_width/2)
    east = longitude + (box_width/2)

    tags = {
        "amenity": True,
        "buildings": ["religous"],
        "leisure": True,
        "shop": True,
        "highway": ["roads"],
        "railway": ["stations and stops"],
        "sport": True
        }

    pois = ox.geometries_from_bbox(north, south, east, west, tags)

    return pois.groupby("amenity").apply(len).reset_index().set_index("amenity").rename(columns={0:"Count"})

def count_local_features(latitude, longitude, width_km, height_km):
    """
    Finds the number of features within the specified bounding box
    :param latitude: The latitude central to the bounding box
    :param longitude: The longitude central to the bounding box
    :param width_km: The width of the bounding box in km (approx)
    :param height_km: The height of the bounding box in km (approx)
    :return: Number of features within the bounding box
    """
    box_width = width_km * (0.02/2.2)
    box_height = height_km * (0.02/2.2)

    north = latitude + (box_height/2)
    south = latitude - (box_height/2)
    west = longitude - (box_width/2)
    east = longitude + (box_width/2)

    tags = {
        "amenity": True,
        "buildings": ["religous"],
        "leisure": True,
        "shop": True,
        "highway": ["roads"],
        "railway": ["stations and stops"],
        "sport": True
        }

    pois = ox.geometries_from_bbox(north, south, east, west, tags)

    return len(pois)

@cache
def get_rows_in_bounds(north, south, west, east, latest_date, earliest_date, conn = None):
    """
    Get rows from the database according to the specified bounds, limit cursor fetch to 50000
    :param north: Maximum latitude
    :param south: Minimum latitude
    :param west: Minimum longitude
    :param east: Maximum longitude
    :param latest_date: Maximum date
    :param earliest_date: Minimum date
    :param conn: The connection object (optional)
    :return: tuple tuple of the rows that satisfy the given bounds
    """
    # Would usually be parameterized to prevent injection
    # but because there are no user input strings here don't need to worry
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    cur.execute(f"""
                SELECT * FROM prices_coordinates_data 
                WHERE {south} < latitude AND latitude < {north}
                AND {east} < longitude AND longitude > {west}
                AND CAST('{earliest_date}' as date) < date_of_transfer AND date_of_transfer < CAST('{latest_date}' as date)
                LIMIT 50000
                """)
    return cur.fetchall()

def get_rows_from_query(query, conn = None):
    """
    Get rows from the database according to query, limit cursor fetch to 50000
    :param query: The sql query to be executed
    :param conn: The connection object (optional)
    :return: tuple tuple of the rows fetched from the query
    """
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchmany(50000)