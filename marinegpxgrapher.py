#! /usr/bin/env python

import math
from datetime import datetime
import xml.dom.minidom as xml
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from Tkinter import Tk
import tkFileDialog
import os

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
    
    latrad = np.radians(lat)

    lonrad = np.radians(lon * np.cos(latrad[0]))


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

    print "Loading data from \"%s\"" % path

    data = {'filename':os.path.basename(path)}
    
    root = xml.parse(path)

    #parse metadata
    #add some error checking here to since I dont know if this metadata is availble in all tracking file

    trk = root.getElementsByTagName("trk")
    if len(trk) > 0 and len(trk[0].getElementsByTagName("name")) == 1:
        data['name'] = trk[0].getElementsByTagName("name")[0].firstChild.data
        print "Track title: ", data['name']

    else:
        print "Track has no name"
        data['name'] = None


    if len(root.getElementsByTagName("metadata")) == 1:

        metadata = root.getElementsByTagName("metadata")[0]
       
        if len(metadata.getElementsByTagName("time")) == 1:
            data['time'] = metadata.getElementsByTagName("time")[0].firstChild.data 
            print "Track recorded at %s with" % ( data['time'] )


            if len(metadata.getElementsByTagName("bounds")) == 1:

                bounds = metadata.getElementsByTagName("bounds")[0]
                data['maxlat'] = bounds.getAttribute('maxlat')
                data['maxlon'] = bounds.getAttribute('maxlon')
                data['minlat'] = bounds.getAttribute('minlat')
                data['minlon'] = bounds.getAttribute('minlon')
        
                print "\tMaximum/Minimum Latitude:\t%s\t/\t%s" % ( data['maxlat'], data['minlat'] )
                print "\tMaximum/Minimum Longitude:\t%s\t/\t%s" % ( data['maxlon'], data['minlon'] ) 

    else:
        print "Metadata not found continuing"
    
    print "Track has %i segments" % len(root.getElementsByTagName("trkseg"))


    gpxpts = root.getElementsByTagName("trkpt")

    print "Found %i points of tracking data" % (len(gpxpts))

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
        
    convrad2nm(data)

    return data


"""
    Convert Garmin UTC format to datetime object
"""
def convdatetime(dtstr, starttime):
    pttime = datetime.strptime(dtstr,"%Y-%m-%dT%H:%M:%SZ") - starttime
    return float(pttime.seconds + pttime.days*24*3600)
    

"""
    Graph all the data this is what you came here for
"""
def plotdata(data):
    # ['lat','lon','time', 'latrad', 'lonrad', 'speed']  
    
    if data['name'] == None:
        trkname = data['filename']

    else:
        trkname = data['name']

    timedatahours = data['data']['time'] / 3600.
   
    print "Plotting speed over time..."

    #plot speed/time
    fig, ax = plt.subplots()
    fig.canvas.set_window_title(trkname)
    plt.title("Speed / time (knots/hours))")
    plt.xlabel("Hour")
    plt.ylabel("Speed (knots)")
    plt.plot( timedatahours,data['data']['speed'])
    #plt.show()

    print "Plotting tracking data with time in"

    #plot time data
    fig, ax = plt.subplots()
    fig.canvas.set_window_title(trkname)
    ax.set_aspect('equal')
    plt.title("Tracking with Time data (NM|hours)")
    plt.ylabel("NM North-South from start")
    plt.xlabel("NM East-Weat from start")
    plt.scatter(data['data']['lonnm'],data['data']['latnm'], c=timedatahours, cmap='plasma')
    plt.colorbar(label="Time (hours)")
    plt.grid()
    #plt.show()
    
    print "Plotting tracking data with speed it nautical miles per hour"

    fig, ax = plt.subplots()
    fig.canvas.set_window_title(trkname)
    ax.set_aspect('equal')
    plt.title("Tracking with speed data (NM|knots)")
    plt.ylabel("NM North-South from start")
    plt.xlabel("NM East-Weat from start")
    plt.scatter(data['data']['lonnm'],data['data']['latnm'], c=data['data']['speed'], cmap='hot')
    plt.colorbar(label="Speed (knots)")
    plt.grid()
    
    print "The graphs may be displayed one in front of the other!"
    
    plt.show()




if __name__ == "__main__":
    
    print "Starting..."

    #get filename
    root = Tk()
    filename = tkFileDialog.askopenfilename()
    root.destroy()
    
    #for now just load the file we are working with
    data = loaddata(filename)

   

    plotdata(data)
