#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This code is intened to help Greenlandings.org with flights data
@author: jialiliang
"""

import matplotlib.pyplot as plt
import xlsxwriter
import glob
import numpy as np
import datetime
import matplotlib.dates as mdates

##############################################################
# Define global variable here
global content 
content = ["Date","Total Count","Total Cancelled", "BWI","IAD","DCA", "LGA", 
                        "JFK", "TEB", "EWR","LAX","BUR","ASE","XNA"]
###############################################################

# Given an airline or airport name, count how many times it appears
def search_air(data,airline):
    match = []
    for i in range(len(data)):
        if airline in str(data[i]) :
            match.append(i)
    return match

# Given the list of airlines, count how many times it appears
def air_count(data,list):
    air_count = []
    for i in list: 
        air_count.append(search_air(data,i))
    return air_count

# given two search words to find out the matching data
# Not2 is to search the flight status without the keyword 
def search_air_2(data1,airline1,data2,airline2,NOT2=False):
   # Find all the index which has keyword1
    match1 = search_air(data1,airline1)
    match2 = []
    
    # From the match of first one, search for the index which matchs second keyword
    for i in match1:
        if NOT2 == False:
            if airline2 in str(data2[i]) :
                match2.append(i)
        if NOT2 == True:
            if airline2 not in str(data2[i]) :
                match2.append(i)
    
    return match2

# Given a variable name and return the variable name in string
def variablename(var):
     return [tpl[0] for tpl in filter(lambda x: var is x[1], globals().items())]


# Extract data of interest and return the count
def interest_data(dtf_file):
    global Fltid; global DEP; global ARR; global Flt_stat
    Fltid, DEP, ARR, Flt_stat = np.loadtxt(dtf_file,usecols=(0,1,2,7),skiprows=2,unpack=True,dtype='U10')
    #list_airline = ["AAL","UAL","DAL","SWA","EJA"]
    #AAL,UAL,DAL,SWA,EJA = air_count(Fltid,list_airline)

    Date = dtf_file.split(".")[0]
    Total_count = len(Fltid)
    # Find out how many flights status are cancelled
    Cancelled = search_air(Flt_stat, "CANCELLED")
    
    # Build the return list 
    global content_list
    content_list = [Date, Total_count,Cancelled]

    # Search the airport of interest ( ARR + DEP )
    # Start from BWI
    for airport in content[3:]:
        content_list.append(search_air_2(ARR,airport,Flt_stat, "CANCELLED",NOT2 = True)\
                            + search_air_2(DEP,airport,Flt_stat, "CANCELLED",NOT2 = True))
            
    #Output count
    count = [Date,Total_count]
    
    # Skip the first(Date) and Second(total_count) 
    for i in range(2, len(content_list)):
        count.append(len(content_list[i]))
    return count


# This function writes the data to an excel file
def write2xls(data):
    # Create an excel file
    workbook = xlsxwriter.Workbook('Cancelled Flight.xlsx') 
    worksheet = workbook.add_worksheet()

    # Write the title to excel 
    for inx in range(len(content)):
        worksheet.write(0, inx, content[inx]) 
    
    
    # Write the content
    for item in range(len(data)):
        for index in range(len(data[0])):
            worksheet.write(item+1, index, data[item][index]) 
    workbook.close()


def read_data(dir=''):
    
    files = glob.glob(dir+"*.dft")
    files.sort()
    data_sum = np.zeros((len(files),14))
    print(files)
    for i in range(len(files)):
        print(files[i])
        data_sum[i] = (interest_data(files[i]))
    return data_sum 


# This function plots the data vs date needed upto 4 different dataset.
# For example, I can plot JFK,TEB,LGA,EWR vs Date
def plot_data(date,data0,label0=None, data1=[],label1=None,\
              data2=[],label2=None,data3=[],label3=None,plt_title='Flight trend in the US'):
    dates = []
    # This translate the number 200301 to 2020/3/1
    # It also translate the date into python plotting format
    for i in date:
        yr,mo,day = int(str(i)[0:2]),int(str(i)[2:4]),int(str(i)[4:6])
        dates.append( datetime.datetime(2000+yr, mo, day))
    
    # This is the ploting function itself
    fig, ax = plt.subplots(constrained_layout=True,figsize=(15, 10),dpi=100)
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.plot(dates, data0,label = label0)
    
    # Optional plotting of the rest three data
    if len(data1) != 0: ax.plot(dates, data1,label=label1)
    if len(data2) != 0: ax.plot(dates, data2,label=label2)  
    if len(data3) != 0: ax.plot(dates, data3,label=label3)
    
    ax.set_title(plt_title)
    ax.set_ylabel('# of Flights')
    ax.legend()
    #fig.savefig('total_flights.png')


# Main running here
if __name__ == '__main__':
    data_sum = read_data()
    plot_data(data_sum[:,0],data_sum[:,1],data1=data_sum[:,2],label0='Total Flight',label1='Cancelled flight')
    #plot_data(data_sum[:,0],data_sum[:,2],label0='Cancelled flight')
    write2xls(data_sum)














