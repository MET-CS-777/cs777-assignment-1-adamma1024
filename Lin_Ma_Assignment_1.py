from __future__ import print_function

import os
import sys
import requests
from operator import add

from pyspark import SparkConf,SparkContext
from pyspark.streaming import StreamingContext

from pyspark.sql import SparkSession
from pyspark.sql import SQLContext

from pyspark.sql.types import *
from pyspark.sql import functions as func
from pyspark.sql.functions import *


#Exception Handling and removing wrong datalines
def isfloat(value):
    try:
        float(value)
        return True
 
    except:
         return False

#Function - Cleaning
#For example, remove lines if they don’t have 16 values and 
# checking if the trip distance and fare amount is a float number
# checking if the trip duration is more than a minute, trip distance is more than 0.1 miles, 
# fare amount and total amount are more than 0.1 dollars
def correctRows(p):
    if(len(p)==17):
        if(isfloat(p[5]) and isfloat(p[11]) and isfloat(p[16])):
            if(float(p[4])> 60 and float(p[5])>0 and float(p[11])> 0 and float(p[16])> 0):
                return p

# Function - Clean up the Directory
# Remove existing output directory if it exists
def removeDir(sc, output_path):
    fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(sc._jsc.hadoopConfiguration())
    path = sc._jvm.org.apache.hadoop.fs.Path(output_path)
    if fs.exists(path):
        fs.delete(path, True)

#Main
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: main_task1 <file> <output> ", file=sys.stderr)
        exit(-1)
    
    sc = SparkContext(appName="Assignment-1")
    
    rdd = sc.textFile(sys.argv[1])

    #Task 1

    # Parse the CSV (Assumes a header is present)
    header = rdd.first()
    data_rdd = rdd.filter(lambda row: row != header).map(lambda row: row.split(",")).filter(correctRows) # Filter out incorrect rows

    # Define indices for relevant columns
    medallion_idx = 0
    hack_license_idx = 1
    trip_time_secs_idx = 4
    total_amount_idx = 16

    # Task 1: Top-10 Active Taxis
    # Create pairs of (medallion, hack_license)
    medallion_hack_pairs = data_rdd.map(lambda row: (row[medallion_idx], row[hack_license_idx]))

    # Group by medallion and calculate unique hack_license counts
    distinct_driver_counts = medallion_hack_pairs.groupByKey() \
        .mapValues(lambda licenses: len(set(licenses)))

    # Sort by distinct_driver_count in descending order and get the top 10
    top10_taxis = distinct_driver_counts.sortBy(lambda x: x[1], ascending=False).take(10)

    rdd_top10 = sc.parallelize(top10_taxis)

    removeDir(sc, sys.argv[2])
    rdd_top10.coalesce(1).saveAsTextFile(sys.argv[2])

    #Task 2

    # Create pairs of (hack_license, (total_amount, trip_time_in_secs))
    driver_earnings_rdd = data_rdd.map(lambda row: (
        row[hack_license_idx],
        (float(row[total_amount_idx]), float(row[trip_time_secs_idx]))
    ))

    # Aggregate by driver to sum total_amount and trip_time_in_secs
    aggregated_rdd = driver_earnings_rdd.reduceByKey(
        lambda acc, value: (acc[0] + value[0], acc[1] + value[1])
    )

    # print(f"\n{aggregated_rdd.take(10)}")

    # Calculate 'Average Earned Money in Min'
    average_earnings_rdd = aggregated_rdd.mapValues(
        lambda x: float(x[0]) / (float(x[1]) / 60)  # total_amount / (trip_time_in_secs / 60)
    )

    # Sort by 'Average Earned Money in Min' in descending order
    sorted_rdd = average_earnings_rdd.sortBy(lambda x: x[1], ascending=False)

    # Get the top 10 drivers
    top_10_drivers = sorted_rdd.take(10)
    
    rdd_top10_drivers = sc.parallelize(top_10_drivers) # Convert the list back to an RDD

    removeDir(sc, sys.argv[3])
    # savings output to argument
    rdd_top10_drivers.coalesce(1).saveAsTextFile(sys.argv[3])

    #Task 3 - Optional 
    #Your code goes here

    #Task 4 - Optional 
    #Your code goes here


    sc.stop()

# !!!Originally, I write all codes with pandas, but I found that it requires me to use spark, so I rewrite the code with spark.
# That's all my pandas code

# # -*- coding: utf-8 -*-
# """Untitled0.ipynb

# Automatically generated by Colab.

# Original file is located at
#     https://colab.research.google.com/drive/1OLwkSu8I3FU_4u9w-tZ9OBS6lTnXdgg1
# """

# # 1. Auth GCP account
# from google.colab import auth
# auth.authenticate_user()

# # Check if the authentication works
# !gcloud config list
# # Login
# !gcloud auth application-default login

# # 1. Connect to dataset
# import pandas as pd

# # URL of the file
# url = "gs://met-cs-777-data/taxi-data-sorted-small.csv.bz2"

# # Load the datasety
# df = pd.read_csv(url)

# # Display the first few rows
# print(df.head())

# # 2. Fine-tuning dataset
# # Set column names
# df.columns = ["medallion", "hack license", "pickup datetime", "dropoff datetime",
#               "trip time in secs", "trip distance", "pickup longitude", "pickup latitude",
#               "dropoff longitude", "dropoff latitude", "payment type", "fare amount",
#               "surcharge", "mta tax", "tip amount", "tolls amount", "total amount"]

# print(df.columns)

# # Attribute Description
# # 0 medallion an md5sum of the identifier of the taxi - vehicle bound (Taxi ID)
# # 1 hack license an md5sum of the identifier for the taxi license (Driver ID)
# # 2 pickup datetime time when the passenger(s) were picked up
# # 3 dropoff datetime time when the passenger(s) were dropped off
# # 4 trip time in secs duration of the trip
# # 5 trip distance trip distance in miles
# # 6 pickup longitude longitude coordinate of the pickup location
# # 7 pickup latitude latitude coordinate of the pickup location
# # 8 dropoff longitude longitude coordinate of the drop-off location
# # 9 dropoff latitude latitude coordinate of the drop-off location
# # 10 payment type the payment method -credit card or cash
# # 11 fare amount fare amount in dollars
# # 12 surcharge surcharge in dollars
# # 13 mta tax tax in dollars
# # 14 tip amount tip in dollars
# # 15 tolls amount bridge and tunnel tolls in dollars
# # 16 total amount total paid amount in dollars

# # Task 1: Top-10 Active Taxis
# # groupby first column
# # distinct by the second column with nunipque()
# # reset_index the column name.
# taxisAndDistinctDriverSet = df.groupby('medallion')['hack license'].nunique().reset_index(name='distinct_driver_count')

# top10Taxis = taxisAndDistinctDriverSet.sort_values(by='distinct_driver_count', ascending=False).head(10)

# # Center justify
# styledDf = top10Taxis.style.set_properties(**{'text-align': 'center'})
# styledDf

# # Task 2- Top 10 best drivers

# # Cause there are some records' trip time is 0, we should ignore them first.
# df_filter = df[df['trip time in secs'] != 0]

# groupByDrivers = df_filter.groupby('hack license')

# aggByTotalAmountAndTripTime = groupByDrivers.agg({'total amount': 'sum', 'trip time in secs': 'sum'})
# aggByTotalAmountAndTripTime["Average Earned Money in Min"] = (aggByTotalAmountAndTripTime['total amount'] / aggByTotalAmountAndTripTime['trip time in secs'] / 60).round(2)

# print("Top 10 Best Drivers")
# aggByTotalAmountAndTripTime.sort_values(by="Average Earned Money in Min", ascending=False).head(10)

# # Task 3 - The best time of the day to Work on Taxi

# # ratio = surcharge amount money / miles
# # time = pickup_time(filter in hour)

# bestTimeToWork = df.copy()

# # Convert the date to hours
# bestTimeToWork['hour'] = pd.to_datetime(bestTimeToWork['pickup datetime'], errors='coerce').dt.hour

# # Filter the zero distance data
# # Tip: .copy can avoid the warning: SettingWithCopyWarning, cause filtered data is a view, not an indepent copy.
# bestTimeToWork_filtered = bestTimeToWork[bestTimeToWork['trip distance'] != 0.0].copy()
# # Calculate the ratio
# bestTimeToWork_filtered['ratio'] = bestTimeToWork_filtered['surcharge'] / bestTimeToWork_filtered['trip distance']

# bestTimeToWork_filtered.sort_values(by='ratio', ascending=False)

# print("The Best time to Work")
# bestTimeToWork_filtered.head(1).hour

# # Task 4
# ## 1.

# paymentType = pd.DataFrame({"type": df['payment type'].unique()})

# # For loop to set the count of each type
# for i, type in enumerate(paymentType['type']):
#   paymentType.at[i, 'count'] = (df['payment type'] == type).sum()

# paymentType['count'] = paymentType['count'].astype(int)

# # sum up all rows
# sum = paymentType['count'].sum()
# # sum

# # calculate the percentage
# for i, type in enumerate(paymentType['type']):
#   paymentType.at[i, 'percentage'] = (paymentType.at[i, 'count'] / sum * 100).round(5)

# print(f"For task 1:\n {paymentType}")

# paymentInHour = pd.DataFrame({"Hour": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]})

# # Add zero cols
# for i, type in enumerate(paymentType['type']):
#   paymentInHour[type] = 0.0

# # paymentInHour
# # create a view that shows the count of each payment type in each hour
# df['hour'] = pd.to_datetime(df['dropoff datetime']).dt.hour
# countOfEachTypeInEachHour = df.groupby(['hour', 'payment type']).size().reset_index(name='count')
# #countOfEachTypeInEachHour

# # Sum by hour
# sumOfPerHour = countOfEachTypeInEachHour.groupby('hour')['count'].transform('sum')
# #sumOfPerHour

# # Calculate the percentage
# countOfEachTypeInEachHour['percentage'] = (countOfEachTypeInEachHour['count'] / sumOfPerHour * 100).round(5)

# # countOfEachTypeInEachHour

# for i, row in countOfEachTypeInEachHour.iterrows():
#   paymentInHour.at[row['hour'], row['payment type']] = row['percentage']

# print("\n\nPercentage of each payment type in each hour:\n")
# paymentInHour

# ## 2.

# # It's similar to the task 4.2, so I don't want to do it again.


# ## 3.



# ## 4.