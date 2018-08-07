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
def calcspeed(data, pt1,pt2):
    return calcdist(data, pt1, pt2) / (calctimedelta(data, pt1, pt2) / 3600.)


"""
    Calculate and return timedelta in hours as float of two points.  Enter points in the order in which they were recorded
"""
def calctimedelta(data,pt1, pt2):
    return data['time'][pt2] - data['time'][pt1]



"""
    convert latitude and longitude to radians and return as tuple  these are really kind made up units so dont worry about the orientation
"""
def convlatlon(lat, lon):
    
    latrad = lat * math.pi / 180

    lonrad = lat * math.pi / 180 * np.cos(latrad)


    return latrad,lonrad


"""
    Calculate distance between two points in nautical miles
"""
def calcdist(data,pt1, pt2):
        
    return math.sqrt(math.pow(data['latrad'][pt1]-data['latrad'][pt2],2) + math.pow(data['lonrad'][pt1]-data['lonrad'][pt2],2)) * earthrad
    

"""
    Converts radian data to nautical miles offset from starting point.
    Takes datastructure as input, modifies data structure
    returns nothing
"""
def convrad2nm(data):
    data['data']['latnm'] = (data['data']['latrad'] - data['data']['latrad'][0]) * earthrad
    data['data']['lonnm'] = (data['data']['lonrad'] - data['data']['lonrad'][0]) * earthrad


"""
    Load garmin data, provide filename 
    returns object with metadata and datapoints
"""
def loaddata(path):
    data = {}
    
    root = xml.parse(path)

    #parse metadata
    #add some error checking here to since I dont know if this metadata is availble in all tracking file
    metadata = root.getElementsByTagName("metadata")[0]
    data['time'] = datetime.strptime(metadata.getElementsByTagName("time")[0].firstChild.data,"%Y-%m-%dT%H:%M:%SZ") 
    bounds = metadata.getElementsByTagName("bounds")[0]
    data['maxlat'] = float(bounds.getAttribute('maxlat'))
    data['maxlon'] = float(bounds.getAttribute('maxlon'))
    data['minlat'] = float(bounds.getAttribute('minlat'))
    data['minlon'] = float(bounds.getAttribute('minlon'))


    #later we probably need to make sure the track isnt split between segments

    gpxpts = root.getElementsByTagName("trkpt")
    starttime = datetime.strptime(gpxpts[0].getElementsByTagName("time")[0].firstChild.data, "%Y-%m-%dT%H:%M:%SZ") 
    
    data['ptcount'] = len(gpxpts)
    data['data'] = { 'lat': np.zeros(data['ptcount']), 'lon':np.zeros(data['ptcount']), 'time':np.zeros(data['ptcount']) }

    #go through and process all tracking points
    for i in range(data['ptcount']):
        
        data['data']['lat'][i] = float(gpxpts[i].getAttribute("lat"))
        data['data']['lon'][i] = float(gpxpts[i].getAttribute("lon"))
        data['data']['time'][i] = convdatetime(gpxpts[i].getElementsByTagName("time")[0].firstChild.data, starttime)

        #There is no chance im going to use this since the wristwatch cant get accurate temp data anyway
        #fmtpt['temp'] = float(pt.getElementsByTagName("gpxx:Temperature")[0].firstChild.data)

    #convert latlong to radians earth units (I made that up) and store
    data['data']['latrad'], data['data']['lonrad'] = convlatlon(data['data']['lat'], data['data']['lon'])

    data['data']['speed'] = np.zeros(data['ptcount'])
    #calculate speed at all tracking p-oints but first later this could be fixed when command line options are added to constrain time
    data['data']['speed'][0] = 0.0

    for i in range(data['ptcount']-1):
        data['data']['speed'][i+1] = calcspeed(data['data'], i, i+1)
        
        #print data['data'][i]['time'],data['data'][i]['speed']  #sanity check interresting note for some reason OpenCPN is giving me speed in miles even though its set to NM....took a while to figure out that descrep

    return data


"""
    Convert Garmin UTC format to datetime object
"""
def convdatetime(dtstr, starttime):
    pttime = datetime.strptime(dtstr,"%Y-%m-%dT%H:%M:%SZ") - starttime
    return float(pttime.seconds + pttime.days*24*3600)
    

"""
    Format lat/lon from floats to string with degrees decimel minutes
"""
def formatter(x,p):

    degrees = int(x)
    minutes = x - degrees

    #do this better
    return str(degrees) + "' " + str(minutes) + "\"" 
    

"""
    Graph all the data this is what you came here for
"""
def plotdata(data):
    # ['lat','lon','time', 'latrad', 'lonrad', 'speed']  
    
    timedatahours = data['data']['time'] / 3600.
    
    #calculate aspect ratio
    mod = (data['data']['lon'].max()-data['data']['lon'].min()) / math.cos(data['data']['latrad'][0]) / 2

    #plot speed/time
    plt.figure("Speed(knots)/time(hours)")
    plt.plot( timedatahours,data['data']['speed'])
    #plt.show()

    #plot time data
    plt.figure("Tracking data with TIME in hours")

    plt.xlim((data['data']['lon'].min()-mod,data['data']['lon'].max()+mod))
    plt.ylim((data['data']['lat'].min(),data['data']['lat'].max()))
    plt.scatter(data['data']['lon'],data['data']['lat'], c=timedatahours, cmap='plasma')
    plt.colorbar()
    #plt.show()
    

    plt.figure("Tracking data with SPEED in knots")

    plt.xlim((data['data']['lon'].min()-mod,data['data']['lon'].max()+mod))
    plt.ylim((data['data']['lat'].min(),data['data']['lat'].max()))
    plt.scatter(data['data']['lon'],data['data']['lat'], c=data['data']['speed'], cmap='hot')
    plt.colorbar()
    plt.grid()
    plt.show()




if __name__ == "__main__":
    
    print "Starting..."

    #get filename
    root = Tk()
    filename = tkFileDialog.askopenfilename()
    root.destroy()

    #for now just load the file we are working with
    data = loaddata(filename)

    convrad2nm(data)

    plotdata(data)
