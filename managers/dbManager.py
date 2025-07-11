from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
import dotenv
import pythonScripts.Logger as Logger
import numpy as np

client = None

def _get_database(collection):

    global client

    if client is None:
        dotenv.load_dotenv()
        CONNECTION_STRING = os.getenv('DB_CONNECTION')

        # Create a new client and connect to the server
        try:
             client = MongoClient(CONNECTION_STRING, server_api=ServerApi('1'))
        except Exception as e:
             Logger.log(f"Problem connecting to the database {e}", "ERROR")

    return client[collection]

def insertData(item, collection, database):
    """
    Insert an observation post into the database 'observations'.

    This function inserts a new item into the database

    Parameters:
        data (object): The data object that will be inserted, it needs to be JSON format.
        Should look like following: 
        data = {
            "type" : INSERT TYPE OF CURRENCY,
            "price" : INSERT THE PRICE VALUE
        }
    """

    dbname = _get_database(database)
    collection_name = dbname[collection]

    collection_name.insert_one(item)

def getData(collection, database):
    """
    Gets data from the database

    Parameters:
        collection (str): The name of the collection.
        database (str): Which database to get data from

    Returns:
        list: A list with the results
    """
     
    dbname = _get_database(database)
    collection_name = dbname[collection]

    result = collection_name.find({}, {"_id": 0, "stock": 0}).sort("timestamp", 1)
    return_list = list(result)
    return(return_list)

def getTradeHistoryData(collection, database):
    """
    Gets trade history data from the database

    Parameters:
        collection (str): The name of the collection.
        database (str): Which database to get data from

    Returns:
        list: A list with the results
    """
     
    dbname = _get_database(database)
    collection_name = dbname[collection]

    pipeline = [
    {
        "$addFields": {
            "parsedTimestamp": {
                "$dateFromString": {
                    "dateString": "$timestamp",
                    "format": "%Y-%m-%d %H:%M"  # Adjust if necessary
                }
            },
            "numericPrice": {"$toDouble": "$price"}  # Convert price to number
        }
    },
    {
        "$group": {
            "_id": {
                "$toDate": {
                    "$subtract": [
                        {"$toLong": "$parsedTimestamp"},
                        {"$mod": [{"$toLong": "$parsedTimestamp"}, 60 * 60 * 1000 * 24]}
                    ]
                }
            },
            "avgPrice": {"$avg": "$numericPrice"},
        }
    },
    {
        "$project": {
            "_id": 0,  # Remove default _id
            "timestamp": {
                "$dateToString": {"format": "%Y-%m-%d", "date": "$_id"}  # Format as YYYY-MM-DD HH
            },
            "avgPrice": 1,
            "count": 1
        }
    },
    {
        "$sort": {"timestamp": 1}  # Sort by time
    }
][
    {
        "$addFields": {
            "parsedTimestamp": {
                "$dateFromString": {
                    "dateString": "$timestamp",
                    "format": "%Y-%m-%d %H:%M"  # Adjust if necessary
                }
            },
            "numericPrice": {"$toDouble": "$price"}  # Convert price to number
        }
    },
    {
        "$group": {
            "_id": {
                "$toDate": {
                    "$subtract": [
                        {"$toLong": "$parsedTimestamp"},
                        {"$mod": [{"$toLong": "$parsedTimestamp"}, 60 * 60 * 1000 * 24]}
                    ]
                }
            },
            "avgPrice": {"$avg": "$numericPrice"},
        }
    },
    {
        "$project": {
            "_id": 0,  # Remove default _id
            "timestamp": {
                "$dateToString": {"format": "%Y-%m-%d", "date": "$_id"}  # Format as YYYY-MM-DD HH
            },
            "avgPrice": 1,
            "count": 1
        }
    },
    {
        "$sort": {"timestamp": 1}  # Sort by time
    }
]

    result = collection_name.aggregate(pipeline)
    return_list = list(result)
    return(return_list)

def queryData(collection, database, interval):
    """
    This function extracts price data for different coins based on dynamic time intervals,
    filtered to include only the last 3 months of data.
    
    Parameters:
        collection (str): The name of the collection.
        database (str): The database name to query.
        interval (str): The interval for data retrieval (e.g., '24h', '4h', '8h', '30m').
        
    Returns:
        np.array: A NumPy array with the results as floats.
    """
    def dynamicQuery(interval):
        current_hour = datetime.now().hour
        hours = [(current_hour + i * int(interval[:-1])) % 24 for i in range(5)]  # Generate list of valid hours

        return {"$expr": {"$in": [{"$hour": "$timestamp"}, hours]}}  # Match timestamps where the hour is in the list

    try:
        # Determine regex pattern based on interval
        if interval == '30M':
            #regex_query = r":(00|30)$"  # Match only minutes ending with 00 or 30
            inner_query = {
                "$or": [
                    {"$expr": {"$eq": [{"$minute": "$timestamp"}, 0]}},  # Match if the minute is 00
                    {"$expr": {"$eq": [{"$minute": "$timestamp"}, 30]}}  # Match if the minute is 30
                ]
            }
        elif interval != '0H':
            inner_query = dynamicQuery(interval)
        else:
            raise ValueError("Unsupported interval. Please choose from '24h to 1h', '30m'.")
        
        # Connect to the MongoDB database
        dbname = _get_database(database)
        collection_name = dbname[collection]

        result = collection_name.aggregate([
            {"$match": inner_query},  # Filter only timestamps at 00 and 30 minutes
            {"$sort": {"timestamp": 1}},  # Sort in ascending order
            {"$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"},
                    "minute": {"$minute": "$timestamp"}
                },
                "average_price": {"$avg": {"$toDouble": "$price"}}  # Convert and compute avg per 30-min group
            }},
            {"$sort": {"_id": 1}}  # Ensure results are in order
        ])
        
        # Extract the prices as floats
        return_list = [float(doc['average_price']) for doc in result]

        if not return_list:
            raise ValueError("No results returned for the given query.")
        
        # Return as a numpy array
        return np.array(return_list)
    
    except Exception as e:
        print(f"An error occurred while querying the database: {e}")
        return np.array([])  # Return an empty array if an error occurs


def findOne(query, collection_name):
    """
    Find a single document in the collection that matches the query.

    Parameters:
        query (dict): The query to find the document.
        collection_name (str): The name of the collection.

    Returns:
        dict: The found document or None if not found.
    """
    try:
        db = _get_database(collection_name)  # Pass the collection_name to _get_database
        collection = db[collection_name]
        result = collection.find_one(query)
        if result:
            print(f"Found record with ObjectId: {result.get('_id')}")
        return result
    except Exception as e:
        print(f"Error querying collection '{collection_name}' with query {query}: {e}")
        return None

def remove_duplicates(collection_name):
    """
    Remove duplicate records from a collection, keeping only one per timestamp.

    Parameters:
        collection_name (str): The name of the collection.
    """
    db = _get_database("coins")
    collection = db[collection_name]

    # Find duplicate timestamps and stocks
    pipeline = [
        {"$group": {
            "_id": {"timestamp": "$timestamp", "stock": "$stock"},
            "count": {"$sum": 1},
            "docs": {"$push": "$_id"}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = collection.aggregate(pipeline)
    
    for duplicate in duplicates:
        ids_to_delete = duplicate["docs"][1:]  # Keep only the first document
        if ids_to_delete:
            collection.delete_many({"_id": {"$in": ids_to_delete}})
            Logger.log(f"Removed {len(ids_to_delete)} duplicates for timestamp {duplicate['_id']['timestamp']}.", "WARNING")
