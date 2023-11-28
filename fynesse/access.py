from .config import *
import requests
import pymysql
import osmnx as ox

# This file accesses the data

"""Place commands in this file to access the data electronically. Don't remove any missing values, or deal with outliers. Make sure you have legalities correct, both intellectual property and personal data privacy rights. Beyond the legal side also think about the ethical issues around this data. """

def request_to_csv(folder, filename, url):
    r = requests.get(url, allow_redirects=True)
    open(f"{folder}/{filename}", "wb").write(r.content)

def make_conn():
    if "username" in config and "password" in config and "host" in config and "database" in config:
        if "port" not in config:
            port = 3306
        return create_connection(config["username"], config["password"], config["host"], config["database"], port)
    raise NotImplementedError

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
    :param conn: the Connection object
    :param table: The table to query
    :param n: Number of rows to query
    """
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table} LIMIT {n}')

    rows = cur.fetchall()
    return rows

def head(table, n=5, conn = None):
    if conn is None:
        conn = make_conn()
    rows = select_top(table, n, conn = conn)
    for r in rows:
        print(r)

def upload_file(filename, table, conn = None):
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    load_data = f"""LOAD DATA LOCAL INFILE '{filename}' INTO TABLE {table} FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES STARTING BY '' TERMINATED BY '\n';"""
    cur.execute(load_data)
    conn.commit()

def local_features(latitude, longitude, width_km, height_km):
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

def get_rows_in_bounds(north, south, west, east, latest_date, earliest_date, conn = None):
    """
    Get rows from the database according to the specified bounds
    Return dataframe
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
    """
    if conn is None:
        conn = make_conn()
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchmany(50000)