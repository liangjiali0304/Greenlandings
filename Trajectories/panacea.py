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
from datetime import datetime as dt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import datetime
import re
from collections import Counter
import shutil
import os

##############################################################
# Define global variable here
global non_flt_content 
non_flt_content = ["Date","Total Count","Total Cancelled"]




global TRACONs
TRACONs = {"CA:SCT":['LAX','SAN','SNA','BUR','ONT','VNY'],\
           
           # index: 9 - 12 
           "NY:N90":['JFK','EWR', 'LGA','TEB'], \
           "CA:NCT":['SFO','SJC','OAK','SMF','RNO'],\
           
           # index: 18 - 21 
           "DC:PCT":['IAD','DCA','BWI','RIC'],\
           "TX:D10":['DFW','DAL'],\
           "IL:C90":['ORD','MDW','PWK'],\
           "GA:A80":['ATL','PDK'],\
           "FL:MIA":['MIA','FLL','OPF','FXE'],\
           "TX:I90":['IAH','HOU'], \
           "CO:D01":['DEN','APA'],
           "Other": ['ASE','XNA']}
           
global BizModels
BizModels = {
           # Different airline bussiness model
           "Hub Carriers":['AAL','UAL','DAL','Total Hub','Mean Hub'],\
           "Point to Point":['SWA','Total Pt2Pt','Mean Pt2Pt'],\
           "Fractional":['EJA','Total Fractional','Mean Fractional'],\
           "BizJet":['GAJ','XOJ','JTL','DPJ','EJM','FTH','Total BizJet','Mean BizJet'],
           "Regional":['SKW','EDV','ENY','RPA','JIA','ASH','QXE','PDT','Total Regional','Mean Regional'],
           "Other":['Other','Count_ALL']
           }

###############################################################

# Given an airline or airport name, count how many times it appears
def search_air(data,airline):
    match = []
    for i in range(len(data)):
        if airline in str(data[i]) :
            match.append(i)
    return match

# Given the list of airlines or airports, count how many times it appears
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

# Given two lists and find the difference in between. Used to solve LGA LGAV mixed up confusion
def Diff(li1, li2): 
    return (list(set(li1) - set(li2)))

# given the index of the Flghtid, check unique values of Flghtid
def check_unique(inx):
    return_arr = []
    for i in inx:
        return_arr.append(Fltid[i])
    
    return np.unique(return_arr)

def count_TRACON_airport():
    global TRACON_list 
    TRACON_list = []
    global Airline_list
    Airline_list = []
    for TRACON,airports in TRACONs.items():
        for airport in airports:
            TRACON_list.append(airport)
    
    # This step convert a dictionary to a list
    for Bizmod,Airlines in BizModels.items():
        for airline in Airlines:
            Airline_list.append(airline)

# function given an airport IATA code and return TRACON for that airport
def get_TRACON(val,Dictionary=TRACONs): 
    for TRACON, airports in Dictionary.items(): 
        #print(airports)
        for airport in airports:
            if val == airport: 
                return TRACON 
  
    return ""#"Airport doesn't exist in TRACON records"



# Extract data of interest and return the count
def interest_data(dtf_file):
    global Fltid; global DEP; global ARR; global Flt_stat
    Fltid, DEP, ARR, Flt_stat = np.loadtxt(dtf_file,usecols=(0,1,2,7),skiprows=2,unpack=True,dtype='U10')
    #list_airline = ["AAL","UAL","DAL","SWA","EJA"]
    #AAL,UAL,DAL,SWA,EJA = air_count(Fltid,list_airline)

    Date = dtf_file.split(".")[0]
    Total_count = len(Fltid)
    # Find out how many flights status are cancelled
    Cancelled = len(search_air(Flt_stat, "CANCELLED"))
    
    # Build the return list for page 1 about airport counts
    global content_list
    content_list = [Cancelled]
    
    # Build the return list for page 2 about airline counts in diff Bizmodels
    global content_list2
    content_list2 = []
    
    # Search the airport of interest ( ARR + DEP )
    # Start from BWI
    
    # Make amendment to LGA: LGA = search_LGA - LGAV
    LGAV = len(search_air_2(ARR,"LGAV",Flt_stat, "CANCELLED",NOT2 = True) +  search_air_2(DEP,'LGAV',Flt_stat, "CANCELLED",NOT2 = True))    
    
    for airport in TRACON_list:
        ARR_DEP = len(search_air_2(ARR,airport,Flt_stat, "CANCELLED",NOT2 = True)\
                            + search_air_2(DEP,airport,Flt_stat, "CANCELLED",NOT2 = True))
                            
        if airport == "LGA": ARR_DEP = ARR_DEP - LGAV          
        content_list.append(ARR_DEP)

    # the mark total count are used to intersect each total count points 
    # and count the airline number in that business category together
    global mark_total_count
    mark_total_count =[-2]
    
    # This is a variable counted for the totals
    five_business_total = 0
    for airline in Airline_list:
        Airline_count = len(search_air(Fltid,airline))
        
        # Counting the total in that category
        if 'Total' in airline:
            # Find the index of that total count
            total_inx = Airline_list.index(airline)
            #print(total_inx)
            mark_total_count.append(total_inx)
            # Smartly used the length of the list to determine the total counts from which index to which index
            length = len(mark_total_count)
            for index in range(mark_total_count[length-2]+2,mark_total_count[length-1]):
                #print(content_list2[index])
                Airline_count += content_list2[index]
            five_business_total += Airline_count 
        elif 'Mean' in airline:
            # Mean = Total / # of datapoint
            Airline_count = content_list2[-1] / (mark_total_count[length-1]-mark_total_count[length-2]-2)
        
        elif 'Other' in airline:
            Airline_count = len(Fltid) - five_business_total
            
        elif 'Count_ALL' in airline:
            Airline_count = len(Fltid)
        content_list2.append(Airline_count)
    
    #bar_chart(Fltid,Date)
    
    # Return the info(number) wanted to stored in the spreadsheet 
    content_list = [Date,Total_count] + content_list
    content_list2 = [Date] + content_list2
    
    '''
    #Output airport count on Page 1
    count = [Date,Total_count]
    
    #Output airline count on Page 2
    #count2 = [Date]
    
    # Skip the first(Date) and Second(total_count) 
    for i in range(0, len(content_list)):
        
        # Do we determine by Unique Flight id 
        if unique_FLid_Flag: count.append(check_unique(len(content_list[i])))   
        else: count.append(len(content_list[i])) 
    
    for i in range (0,len(content_list2)):
        count2.append(len(content_list2[i]))
    '''
    return content_list,content_list2 


def bar_chart(Fltid,date):
    date = str(date)
    name= []
    # Seperate the airline name
    for air in Fltid:
        name.append(re.findall(r'[A-Za-z]+|\d+', air)[0])
    #name = np.sort(name)

    # Get the key and count component from the frequency counter file
    Dic = Counter(name)
    key=sorted(list(Dic.keys()))
    count = []
    for i in key:
        count.append(Dic[i])
    count = np.array(count)
    # for plotting. Threshold is at least what number of flights you want to plot
    threshold = 30
    # index for the element that fits the threshold
    index = np.where(count>threshold)
    key_cond = []
    for inx in index[0]:
        key_cond.append(key[inx])
    
    fig, ax1 = plt.subplots(constrained_layout=True,figsize=(20, 10),dpi=30)
    x = np.arange(len(count[index]))
    ax1.bar(x, height=count[index])
    #ax1.set_yscale('log')
    ax1.set_xticks(x)
    ax1.set_xticklabels(key_cond)
    ax1.set_ylim(0, 4000)
    ax1.set_title("Number of flights in airlines on "+ date)
    
    #fig.savefig(str(os.getcwd())+'/Output/'+date+'.png')
    
    
    
# This function writes the data to an excel file
def write2xls(data,airline_data=[],title='_flights.xlsx'):
    # Create an excel file
    time = dt.now().strftime("%Y_%m_%d_%H%M")
    workbook = xlsxwriter.Workbook(time+title) 
    worksheet = workbook.add_worksheet()
    worksheet2 = workbook.add_worksheet()
    # Write the  to excel 

    # Write the TRACON and title to excel 
    content2write = non_flt_content + TRACON_list
    for inx in range(len(content2write)):
        # TRACON
        worksheet.write(0, inx, get_TRACON(content2write[inx]))
        
        # Title
        worksheet.write(1, inx, content2write[inx]) 
    
    content2write_2 = ["Date"] + Airline_list
    for inx in range(len(content2write_2)):
        # TRACON
        worksheet2.write(0, inx, get_TRACON(content2write_2[inx],BizModels))
        
        # Title
        worksheet2.write(1, inx, content2write_2[inx]) 
    
    
    # Write the airport content
    for item in range(len(data)):
        for index in range(len(data[0])):
            things2write = data[item][index]
            
            # In the condition of writing the date change 
            # the format from 2000301 to 2020/3/1
            if index == 0:
                things2write = Canon_date(things2write)
            
            # Check if there are any errors in the total count for example 05/13 and 05/23
            # If the total count is smaller than 4000, we took the average of the previous day and the day after
            if index == 1:
                if check_error_total_count_Flag & (int(things2write) < 4000): 
                    things2write = (data[item-1][index]+data[item+1][index]) / 2
                
                
            worksheet.write(item+2, index, things2write) 
            
        # Write the airline content on page 2
    for item in range(len(airline_data)):
        for index in range(len(airline_data[0])):
            things2write = airline_data[item][index] 
            
            # In the condition of writing the date change 
            # the format from 2000301 to 2020/3/1
            if index == 0:
                things2write = Canon_date(things2write)
            
            worksheet2.write(item+2, index, things2write) 


    workbook.close()


def read_data(dir=''):
    
    files = glob.glob(dir+"*.dft")
    files.sort()
    # The +3 means We have to account for Date, Total count, Cancelled count
    data_sum = np.zeros((len(files),len(TRACON_list)+3))
    biz_model_sum = np.zeros((len(files),len(Airline_list)+1))
    print(files)
    for i in range(len(files)):
        print(files[i])
        data_sum[i] = interest_data(files[i])[0]
        biz_model_sum[i] = interest_data(files[i])[1]
    return data_sum,biz_model_sum


def Canon_date(i):
    yr,mo,day = int(str(i)[0:2]),int(str(i)[2:4]),int(str(i)[4:6])
    return "%s/%02d/%02d"%(2000+yr, mo, day)
    
# This function plots the data vs date needed upto 4 different dataset.
# For example, I can plot JFK,TEB,LGA,EWR vs Date
def plot_data(date,data0,label0=None, data1=[],label1=None,\
              data2=[],label2=None,data3=[],label3=None,data4=[],label4=None,\
                  plt_title='Flight trend in the US'):
    
    
    dates = []
    # This translate the number 200301 to 2020/3/1
    # It also translate the date into python plotting format
    for i in date:
        yr,mo,day = int(str(i)[0:2]),int(str(i)[2:4]),int(str(i)[4:6])
        dates.append( datetime.datetime(2000+yr, mo, day))
    
    # This is the ploting function itself
    fig, ax1 = plt.subplots(constrained_layout=True,figsize=(20, 10),dpi=300)
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    locator = mdates.WeekdayLocator(interval=1)
    formatter = DateFormatter("%d-%b")
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    ln0 = ax1.plot(dates, data0,label = label0,color='orchid',linewidth=5)
    ax1.tick_params(axis='y', labelcolor='teal')
    
    # Combinition of lines so I can plot the legend easily later
    lns = ln0
    # Optional plotting of the rest three data on the same scale
    if len(data1) != 0: ln1 = ax1.plot(dates, data1,label=label1,color='limegreen',linewidth=5); lns += ln1
    if len(data2) != 0: ln2 = ax1.plot(dates, data2,label=label2,color='darkorange',linewidth=5); lns += ln2  
    if len(data3) != 0: ln3 = ax1.plot(dates, data3,label=label3,color='darkgreen',linewidth=5); lns += ln3
    
    # Plotting data on different scale 
    if len(data4) != 0: ax2 = ax1.twinx(); ln4 =ax2.plot(dates, data4,label=label4,color='r',linewidth=5);ax2.tick_params(axis='y', labelcolor='r'); lns += ln4
    ax1.set_title(plt_title,fontweight="bold", fontsize=50)
    ax1.set_ylabel('# of Flights', fontsize=30)
    
    labs = [l.get_label() for l in lns]
    leg = ax1.legend(lns, labs, loc=0,prop={'size': 30})
    for line in leg.get_lines():
        line.set_linewidth(4.0)
    plt.xticks(rotation=45)
    ax1.tick_params(axis="x", labelsize=16)
    ax1.tick_params(axis="y", labelsize=25)
    #plt.show()
    #fig.savefig(plt_title)


# Main running here
if __name__ == '__main__':
    
    check_error_total_count_Flag = True # Check error total count (<4000 then use the average for the day before and after)
    unique_FLid_Flag = False   # Determine if the we use the metrics as unique flight(False) or unique flight id(True)
    print("Unique_Flght = %s\n\n" % str(not unique_FLid_Flag))
    airline_normalization = False # Flag that determine if we normalized the plotting 
    # For Bar_chart only
    # Check if there is a directory called Output, delete it if it exist.
    if os.path.exists('Output'):
        shutil.rmtree('Output')
    # Creat a directory and save data inside it
    os.makedirs('Output')
    
    
    count_TRACON_airport()
    data_sum,bizmodel_sum = read_data()
    
    
    # LGA = data[:,6], JFK = 7, TEB=8, EWR = 9
    
    
    
    plot_data(data_sum[:,0],data_sum[:,9],data1=data_sum[:,10],data2=data_sum[:,11],\
              data3=data_sum[:,12],label0='JFK',label1='EWR',label2='LGA',label3='TEB',plt_title='NYC Metropolitan')
    '''
    plot_data(data_sum[:,0],data_sum[:,18],data1=data_sum[:,19],data2=data_sum[:,20],label0='IAD',label1='DCA',label2='BWI',plt_title='Washington Metropolitan')
    '''
    
    for index in mark_total_count[1:]:
        # determine if we normalize the plot or not
        if airline_normalization: normalized = bizmodel_sum[:,index+2].max()
        else:  normalized = 1
        plot_data(data_sum[:,0],bizmodel_sum[:,index+2]/normalized,label0=Airline_list[index+1], plt_title=Airline_list[index+1])
    plot_data(data_sum[:,0],bizmodel_sum[:,-2]/normalized,label0="Other Airlines", plt_title="Other Airlines") 
    plot_data(data_sum[:,0],data_sum[:,1],label0='Total Flight')
    plot_data(data_sum[:,0],bizmodel_sum[:,1],data1=bizmodel_sum[:,2],data2=bizmodel_sum[:,3], \
              label0='American Airline', label1='United Airline',label2='Delta Airline',plt_title="Hub Carrier Airlines")
    write2xls(data_sum,bizmodel_sum)













