#! /usr/bin/env python

import math
from datetime import datetime
import xml.dom.minidom as xml
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from Tkinter import Tk
import tkFileDialog


#earths radius in nautical miles we will use this later
earthrad = 3436.801


"""
    Calculate speed in nautical miles
"""
def calcspeed(pt1, pt2):
    return calcdist(pt1,pt2) / calctimedelta(pt1,pt2)


"""
    Calculate and return timedelta in hours as float of two points.  Enter points in the order in which they were recorded
"""
def calctimedelta(pt1, pt2):
    diff = pt2['time'] - pt1['time']
    
    return diff.seconds / (60.0 * 60.0) + diff.microseconds / 1000000.0



"""
    convert latitude and longitude to radians and return as tuple  these are really kind made up units so dont worry about the orientation
"""
def convlatlon(lat, lon):
    latrad = lat * math.pi / 180

    lonrad = lat * math.pi / 180 * math.cos(latrad)


    return latrad,lonrad


"""
    Calculate distance between two points in nautical miles
"""
def calcdist(pt1, pt2):
        
    return math.sqrt(math.pow((pt1['latrad']-pt2['latrad']),2) + math.pow((pt1['lonrad']-pt2['lonrad']),2)) * earthrad
    
        


"""
    Load garmin data, provide filename 
    returns object with metadata and datapoints
"""
def loaddata(path):
    data = {}
    
    data['data'] = []

    root = xml.parse(path)

    #parse metadata
    metadata = root.getElementsByTagName("metadata")[0]
    data['time'] = convdatetime(metadata.getElementsByTagName("time")[0].firstChild.data)

    bounds = metadata.getElementsByTagName("bounds")[0]
    data['maxlat'] = float(bounds.getAttribute('maxlat'))
    data['maxlon'] = float(bounds.getAttribute('maxlon'))
    data['minlat'] = float(bounds.getAttribute('minlat'))
    data['minlon'] = float(bounds.getAttribute('minlon'))


    #later we probably need to make sure the track isnt split between segments

    trkpts = []
    #go through and process all tracking points
    for pt in root.getElementsByTagName("trkpt"):
        fmtpt = {}
        fmtpt['lat'] = float(pt.getAttribute("lat"))
        fmtpt['lon'] = float(pt.getAttribute("lon"))
        fmtpt['time'] = convdatetime(pt.getElementsByTagName("time")[0].firstChild.data)

        fmtpt['temp'] = float(pt.getElementsByTagName("gpxx:Temperature")[0].firstChild.data)


        data['data'].append(fmtpt)

    #convert latlong to radians earth units (I made that up) and store
    for i in data['data']:
        i['latrad'],i['lonrad'] = convlatlon(i['lat'],i['lon'])


    #calculate speed at all tracking p-oints but first later this could be fixed when command line options are added to constrain time
    data['data'][0]['speed'] = 0.0

    for i in range(len(data['data'])-1):
        data['data'][i+1]['speed'] = calcspeed(data['data'][i],data['data'][i+1])
        
        #print data['data'][i]['time'],data['data'][i]['speed']  #sanity check interresting note for some reason OpenCPN is giving me speed in miles even though its set to NM....took a while to figure out that descrep

    return data


"""
    Convert Garmin UTC format to datetime object
"""
def convdatetime(dtstr):
    return datetime.strptime(dtstr,"%Y-%m-%dT%H:%M:%SZ")


"""
    Converts a column of tracking data to an arry of points for graphing and such, probably could have done all this way more effeciently but hey its on CPU cycles and ram right
    Pass data array and column name
"""
def column2arr(data, col):
    retarr = []
    for pt in data:
        retarr.append(pt[col])

    return retarr
    
"""
    Returns an array of the time offset in hours
"""
def gettimeoffsets(data):
    
    #start from first trkpt
    starttime = data[0]['time']

    output = []
    for i in data:
        t = i['time'] - starttime

        output.append(24.0 * t.days + t.seconds / 3600.)
    
    return output

"""
    Format lat/lon from floats to string with degrees decimel minutes
"""
def formatter(x,p):

    degrees = int(x)
    minutes = x - degrees

    #do this better
    return str(degrees) + "' " + str(minutes) + "\"" 
    


if __name__ == "__main__":
    
    print "Starting..."

    #get filename
    root = Tk()
    filename = tkFileDialog.askopenfilename()
    root.destroy()

    #for now just load the file we are working with
    data = loaddata(filename)

    x = np.array(column2arr(data['data'],"lon"))
    y = np.array(column2arr(data['data'],"lat"))
    s = np.array(column2arr(data['data'],"speed"))
    t = np.array(gettimeoffsets(data['data']))

    #calculate aspect ratio
    mod = (data['maxlon']-data['minlon']) / math.cos(data['data'][0]['latrad']) / 2

    #plot speed/time
    plt.title("Speed(knots)/time(hours)")
    plt.plot(t,s)
    plt.show()
    plt.cla()
    #plot time data
    plt.title("Tracking data with TIME in hours")

    fig, ax = plt.subplot()
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(formatter))

    plt.xlim((data['minlon']-mod,data['maxlon']+mod))
    plt.ylim((data['minlat'],data['maxlat']))
    plt.scatter(x,y,c=t, cmap='plasma')
    plt.colorbar()
    plt.show()

    #plot speed data
    #formatter for degres decim minutes
    

    plt.title("Tracking data with SPEED in knots")
    
    fig, ax = plt.subplots()
    ax.yaxis.set_major_formatter(FuncFormatter(formatter))
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))

    plt.xlim((data['minlon']-mod,data['maxlon']+mod))
    plt.ylim((data['minlat'],data['maxlat']))
    plt.scatter(x,y, c=s, cmap='hot')
    plt.colorbar()
    plt.grid()
    plt.show()

    
