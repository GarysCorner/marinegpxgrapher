#! /usr/bin/env python3
#File:		marinegpxgrapher.py
#Author:	Gary Bezet
#Date:		2018-07-29
#Desc:		This program is designed to graph GPX tracking data for marine application.  I wrote it to get a more useful understanding of tracking data from regattas.  The basic problem is that tracking data doesn't tell a very good story without speed and/or time data.  While programs like OpenCPN are very useful I didn't find the display of tracking data was adequite.  To solve this I wrote this program which I intend to be used with a chart plotter like OpenCPN to provide additional data and allow you to form a good narrative about your last race.  If you look back at git revision history you may notice that I originally was writing this code to tear down the GPX data into a better format, but the project kept evolving and became what it is now.  Hope you find it useful.

#    marinegpxgrapher A GPX file graphing program for sailors
#    Copyright (C) 2018  Gary Andrew Bezet

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


#configuration data (probably command line)
config = {  "hours":False,
            "minutes":False,
            "filename":None,
            "timecmap":"plasma",
            "speedcmap":"gist_ncar",
            "figsize":(6,6),
            "showall":True,
            "showspeed":False,
            "showtime":False,
            "showhist":False
        }


#catch error if matplotlib or numpy arent installed

import math
from datetime import datetime
import xml.dom.minidom as xml
import os
import argparse
from xml.parsers.expat import error as xmlerror
try:
    from matplotlib.ticker import FuncFormatter
    import matplotlib.pyplot as plt
    from matplotlib import cm as colormaps
    
except ImportError:
    print("")
    print("")
    print("You don't have matplotlib installed, you need to install it.  Go to the address below.  Error 6")
    print("https://matplotlib.org/users/installing.html")
    exit(6)

try:
    import numpy as np
except ImportError:
    print("")
    print("")
    print("You don't have numpy installed, you need to install it.  Go to the address below Error 7")
    print("https://docs.scipy.org/doc/numpy/user/install.html")
    exit(7)


#earths radius in nautical miles we will use this later
earthrad = 3436.801


"""
    Calculate speed in nautical miles
"""
def calcspeed(data):

    #The insert statement gives us a starting speed of zero and make sure the speed array has the same dimensions as the other arrays
    data['data']['speed'] = np.insert(calcdist(data) / calctimedelta(data), 0, [0.0])


"""
    Why did I put my comments here?
    Calculate thr olling averge of speed
"""
def calcspeed_rollavg(data, pts):
    data['data']['speedavg'] = np.zeros(data['data']['speed'].shape[0], dtype=np.float)
    data['data']['speedavg'][:pts] = np.mean(data['data']['speed'][:pts-1]) # set the first points to their average for simplicity
    for idx in range(pts,data['data']['speed'].shape[0]):
        data['data']['speedavg'][idx] = np.mean(data['data']['speed'][idx-pts:idx])
        

    
"""
    Calculate and return timedelta in hours as float of two points.  Enter points in the order in which they were recorded
"""
def calctimedelta(data):

    return (data['data']['time'][1:] - data['data']['time'][:-1]) / 3600



"""
    Calculate distance between two points in nautical miles
"""
def calcdist(data):
        
    return np.sqrt(np.square(data['data']['latnm'][:-1] -data['data']['latnm'][1:]) + np.square(data['data']['lonnm'][:-1]-data['data']['lonnm'][1:]))
    


"""
convert lat and long to offset from orgin using Haversine
"""
def havconvlatlon(data,frame='data'):
    
    
    latrad = np.radians(data[frame]['lat'])
    lonrad = np.radians(data[frame]['lon'])
    data[frame]['latnm'] = latrad * earthrad
    data[frame]['latnm'] = data[frame]['latnm'] - data[frame]['latnm'][0]
    
    data[frame]['lonnm'] = ((lonrad-lonrad[0]) * np.cos(latrad)) * earthrad
    
    
    #data['data']['lonnm'] = data['data']['lonnm'] - data['data']['lonnm'][0]

    
"""
Load waypoints
"""
def loadmarkfiles(data):
    waypoints = set()
    totaldropped = 0
    
    for filename in data['markfiles']:
        print("Loading mark data from \"%s\"" % os.path.basename(filename))

        droppedinfile = 0

        try:
            root = xml.parse(filename)

        except xmlerror:
            print("")
            print("")
            print("***Fatal Error:  mark GPX file is not properly formated XML, sorry I cant help you with this***")
            print("File: %s" % filename)
            exit(8)

        except IOError:
            print("")
            print("")
            print("***Fatal Error:  Could not open mark file ***")
            print("File: %s" % filename)
            exit(9)

        wpt = root.getElementsByTagName("wpt")
        if len(wpt) == 0:
            print("***Warning, no waypoints in %s***" % filename)
        
        wptcountfile = 0
        for w in wpt:
            nameelm = w.getElementsByTagName('name')
            if not (w.hasAttribute('lat') and w.hasAttribute('lon') and len(nameelm) == 1):
                print("***Warning, some waypoints missing data [%s] dropping***" % filename)
                droppedinfile += 1
                
            else:
                
                datapoint = (float(w.getAttribute('lat')), float(w.getAttribute('lon')),nameelm[0].firstChild.data)
                if (not config['filterwaypoints']) or (datapoint[0] > np.min(data['data']['lat']) and datapoint[0] < np.max(data['data']['lat']) and datapoint[1] > np.min(data['data']['lon']) and datapoint[1] < np.max(data['data']['lon'])):
                    waypoints.add(datapoint)
                else:
                    droppedinfile += 1
                
            
                
            wptcountfile += 1
        
        totaldropped += droppedinfile
        
        print("Loaded %d/%d waypoints from %s" % (wptcountfile,droppedinfile + wptcountfile,filename))

    data['waypoints'] = {}
    data['waypoints']['names'] = []
    data['waypoints']['lat'] = np.zeros(len(waypoints)+1,dtype=np.float)
    data['waypoints']['lon'] = np.zeros(len(waypoints)+1,dtype=np.float)
    
    #this is for passing it into our previous functions
    data['waypoints']['lat'][0] = data['data']['lat'][0]
    data['waypoints']['lon'][0] = data['data']['lon'][0]
        
    for idx,w in zip(range(1,len(waypoints)+1),waypoints):
        data['waypoints']['names'].append(w[2])
        data['waypoints']['lat'][idx] = w[0]
        data['waypoints']['lon'][idx] = w[1]
    
    
    havconvlatlon(data, frame='waypoints')
    
    data['waypoints']['lat'] = data['waypoints']['lat'][1:]
    data['waypoints']['lon'] = data['waypoints']['lon'][1:]
    data['waypoints']['latnm'] = data['waypoints']['latnm'][1:]
    data['waypoints']['lonnm'] = data['waypoints']['lonnm'][1:]
    
    print("Loaded %d/%d total waypoints!" % (len(waypoints),len(waypoints) + totaldropped))
      
    
              
        
"""
    Load garmin data, provide filename 
    returns object with metadata and datapoints
"""
def loaddata(path):

    startloadtime = datetime.now()

    print("Loading data from \"%s\"" % os.path.basename(path))

    data = {'filename':os.path.basename(path), 'markfiles':config['markfiles']}
    
    try:
        root = xml.parse(path)

    except xmlerror:
        print("")
        print("")
        print("***Fatal Error:  GPX file is not properly formated XML, sorry I cant help you with this***")
        print("File: %s" % path)
        exit(2)

    except IOError:
        print("")
        print("")
        print("***Fatal Error:  Could not open file ***")
        print("File: %s" % path)
        exit(5)

    #parse metadata
    #add some error checking here to since I dont know if this metadata is availble in all tracking file

    trk = root.getElementsByTagName("trk")
    if len(trk) > 0 and len(trk[0].getElementsByTagName("name")) == 1:
        data['name'] = trk[0].getElementsByTagName("name")[0].firstChild.data
        print("Track title: ", data['name'])

    else:
        print("Track has no name")
        data['name'] = None


    if len(root.getElementsByTagName("metadata")) == 1:

        metadata = root.getElementsByTagName("metadata")[0]
       
        if len(metadata.getElementsByTagName("time")) == 1:
            data['time'] = metadata.getElementsByTagName("time")[0].firstChild.data 
            print("Track recorded at %s with" % ( data['time'] ))


            if len(metadata.getElementsByTagName("bounds")) == 1:

                bounds = metadata.getElementsByTagName("bounds")[0]
                data['maxlat'] = float(bounds.getAttribute('maxlat'))
                data['maxlon'] = float(bounds.getAttribute('maxlon'))
                data['minlat'] = float(bounds.getAttribute('minlat'))
                data['minlon'] = float(bounds.getAttribute('minlon'))
        
                print("\tMaximum/Minimum Latitude:\t%s\t/\t%s" % ( data['maxlat'], data['minlat'] ))
                print("\tMaximum/Minimum Longitude:\t%s\t/\t%s" % ( data['maxlon'], data['minlon'] )) 

    else:
        print("Metadata not found continuing")
    
    print("Track has %i segments" % len(root.getElementsByTagName("trkseg")))


    gpxpts = root.getElementsByTagName("trkpt")

    #I am concerned about how len(gpxpts) is handled and weather it could cause performance issues
    print("Found %i points of tracking data" % (len(gpxpts)))
    if len(gpxpts) == 0:
        print("")
        print("")
        print("File (%s) contains no tracking points, program can not continue!")
        exit(100)

    data['ptcount'] = len(gpxpts)
    data['data'] = { 'lat': np.zeros(data['ptcount']), 'lon':np.zeros(data['ptcount']), 'time':np.zeros(data['ptcount']) }

    #setup time converter
    checkdtformat(gpxpts[0].getElementsByTagName("time")[0].firstChild.data)
    
    starttime = datetime.strptime(gpxpts[0].getElementsByTagName("time")[0].firstChild.data, config['datetimeformat']) 

    #go through and process all tracking points
    for i in range(data['ptcount']):
        
        data['data']['lat'][i] = float(gpxpts[i].getAttribute("lat"))
        data['data']['lon'][i] = float(gpxpts[i].getAttribute("lon"))
        data['data']['time'][i] = convdatetime(gpxpts[i].getElementsByTagName("time")[0].firstChild.data, starttime)

    
    totaltime = data['data']['time'][len(data['data']['time'])-1]

    if totaltime > 9000:
        print("Track elapsed time is: %f hours" % (totaltime / 3600.))

    else:
        print("Track elapsed time is: %f minutes" % (totaltime / 60.))


    #convert latlong to nautical mile offset
    #convlatlon(data)
    havconvlatlon(data)

    #calc speeds
    calcspeed(data)
    
    #calc speed rolling avg
    calcspeed_rollavg(data,config['rollavg_points'])
    
    #load marks from markfiles
    if data['markfiles']:
        loadmarkfiles(data)

    loadtime = datetime.now() - startloadtime

    print("Track \"%s\" loaded (load time %i ms)!" % (os.path.basename(path), loadtime.seconds * 1000. + loadtime.microseconds/1000))

    return data


"""
    Convert Garmin UTC format to datetime object
"""
def convdatetime(dtstr, starttime):
    pttime = datetime.strptime(dtstr,config['datetimeformat']) - starttime
    return float(pttime.seconds + pttime.days*24*3600)

"""
    Check time format potential time formats and set convdatetime
"""
def checkdtformat(dtstr):

    format_strings = ["%Y-%m-%dT%H:%M:%S.%f%z","%Y-%m-%dT%H:%M:%S.%fZ","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%dT%H:%M:%SZ"]
    config['datetimeformat'] = None
    
    for idx, fstr in enumerate( format_strings ):
        try:
            datetime.strptime(dtstr,fstr)
            config['datetimeformat'] =   fstr
            break
            
        except ValueError:
            if idx == (len(format_strings) - 1):

                print("No valid time format found for \"%s\" fatal error!" % (dtstr))
                print("Please report this error at https://github.com/GarysCorner/marinegpxgrapher/issues")

                exit(1)

    print("Time format string found \"%s\"" % (config['datetimeformat']))


"""
    Graph all the data this is what you came here for
"""
def plotdata(data):
    # ['lat','lon','time', 'latrad', 'lonrad', 'speed']  
    
    if data['name'] == None:
        trkname = data['filename']

    else:
        trkname = data['name']

    

    if data['data']['time'][len(data['data']['time'])-1] > 9000:

        timeunit = "hours"
        timedatahours = data['data']['time'] / 3600.

    else:
        timeunit = "minutes"
        timedatahours = data['data']['time'] / 60.


    #this is very ugly fix it
    if config['hours']:

        timeunit = "hours"
        timedatahours = data['data']['time'] / 3600.

    elif config['minutes']:
        timeunit = "minutes"
        timedatahours = data['data']['time'] / 60.



    if config['showhist']:
   
        print("Plotting speed over time (%s)..." % (timeunit))

        #plot speed/time    
        fig, ax = plt.subplots(figsize=config['figsize'])
        fig.canvas.set_window_title(trkname)
        plt.suptitle("Speed / time (knots/%s)" % (timeunit))
        plt.title("(%d point rolling average)" % config['rollavg_points'], fontsize='small')
        plt.xlabel(timeunit)
        plt.ylabel("Speed (knots)")
        plt.plot( timedatahours[config['rollavg_points']:],data['data']['speedavg'][config['rollavg_points']:])
        #plt.show()

    if config['showtime']:

        print("Plotting tracking data with time in %s" % (timeunit))
        
        #plot time data
        fig, ax = plt.subplots(figsize=config['figsize'])
        fig.canvas.set_window_title(trkname)
        ax.set_aspect('equal')
        plt.title("Tracking with Time as color")
        plt.ylabel("NM North-South from start")
        plt.xlabel("NM West-East from start")
        plt.scatter(data['data']['lonnm'],data['data']['latnm'], c=timedatahours, cmap=config['timecmap'])
        plt.colorbar(label="Time (%s)" % (timeunit))
        plt.grid()
        
        #add marks
        if data['markfiles'] and len(data['waypoints']) > 0:
            plt.scatter(data['waypoints']['lonnm'], data['waypoints']['latnm'], marker='x')
            for idx in range(len(data['waypoints']['names'])):
                plt.annotate(data['waypoints']['names'][idx],(data['waypoints']['lonnm'][idx],data['waypoints']['latnm'][idx]))
        
        #plt.show()
    
    if config['showspeed']:
    
        print("Plotting tracking data with speed it nautical miles per hour")

        fig, ax = plt.subplots(figsize=config['figsize'])
        fig.canvas.set_window_title(trkname)
        ax.set_aspect('equal')
        plt.title("Tracking with speed as color")
        plt.ylabel("NM North-South from start")
        plt.xlabel("NM West-East from start")
        plt.scatter(data['data']['lonnm'],data['data']['latnm'], c=data['data']['speed'], cmap=config['speedcmap'])
        plt.colorbar(label="Speed (knots)")
        plt.grid()
        
        #add marks
        if data['markfiles'] and len(data['waypoints']) > 0:
            plt.scatter(data['waypoints']['lonnm'], data['waypoints']['latnm'], marker='x')
            for idx in range(len(data['waypoints']['names'])):
                plt.annotate(data['waypoints']['names'][idx],(data['waypoints']['lonnm'][idx],data['waypoints']['latnm'][idx]))

        print("The graphs may be displayed one in front of the other!")
    
    plt.show()

"""
    Displays list of valid colormaps
"""
def showcolormaps():
    allcolormaps = dir(colormaps)
    for i in allcolormaps:
        if i[0] != '_':
            print(i + "\t", end=' ')

"""
    Parses the command line arguments
"""
def parsecmdline():
    
    parser = argparse.ArgumentParser(prog="Marine GPX Grapher",
                                     description="This program is designed to provide useful graphs of GPX tracking data from Garmin Quatix watches, though it should work with other files.  The program will display two graphs both of which show all of the tracking points as offsets for a zero position which is the first data point.  One graph will show the speed at each data point as color, and the other will show the time at each datapoint as color.  There is also a third graph showing speed with respect to time, however this is just for comparison.  Since this program is intended for marine data it does not take altitude into account.")

    parser.add_argument("-f", "--file", help = "Open file", metavar = "file", type = str)
    parser.add_argument("-mf", "--markfile", help = "Add waypoints from GPX file to graphs (can be called multiple times)", action="append", type=str, metavar = "file")
    parser.add_argument("-nf", "--nofilter",  help = "Loads all marks even if they are outside the track area", action="store_true")
    
    parser.add_argument("-H", "--hours",  help = "Force graphs to use hours instead of minutes", action="store_true")
    parser.add_argument("-M", "--minutes" , help = "Force graphs to use minutes intead of hours", action="store_true")
    
    parser.add_argument("-gs", "--graphspeed" , help = "Show speed graph", action="store_true")
    parser.add_argument("-gt", "--graphtime" , help = "Show time graph", action="store_true")
    parser.add_argument("-gh", "--graphhist" , help = "Show speed history graph (rolling average)", action="store_true")
    parser.add_argument("-ra", "--rollavgpts" , help = "The number of points to use for rolling average (default 20)" , metavar="points", type=int)
    
    parser.add_argument("-cs", "--speedcmap", help = "Colormap for speed graph", metavar = "colormap", type = str)
    parser.add_argument("-ct", "--timecmap", help = "Colormap for time graph", metavar = " colormap", type = str)
    parser.add_argument("-sc","--showcolormaps", help = "Displays a list of colormaps", action="store_true")
    parser.add_argument("-s","--size", help="Sets the figure size (X & Y) in inches", metavar="inches", type=int)
    parser.add_argument("-sx", "--xsize", help="Sets the size in inches for the X axis", metavar="inches", type=int)
    parser.add_argument("-sy", "--ysize", help="Sets the size in inches for the Y axis", metavar="inches", type=int)
    
    

    args = parser.parse_args()

    if args.showcolormaps:
        showcolormaps()
        exit(0)

    if args.rollavgpts:
        config['rollavg_points'] = args.rollavgpts
    
    else:
        config['rollavg_points'] = 20
        
    if args.speedcmap:
        config['speedcmap'] = args.speedcmap

    if args.timecmap:
        config['timecmap'] = args.timecmap
    
    if args.hours:
        config['hours'] = True

    if args.minutes:
        config['minutes'] = True

    if args.file:
        config['filename'] = args.file
    
    if args.size:
        config['figsize'] = (args.size, args.size)
        
    if args.xsize:
        listfigsize = list(config['figsize'])
        listfigsize[0] = args.xsize
        config['figsize'] = tuple(listfigsize)
        
    if args.ysize:
        listfigsize = list(config['figsize'])
        listfigsize[1] = args.ysize
        config['figsize'] = tuple(listfigsize)
        
    if args.graphspeed:
        config['showall'] = False
        config['showspeed'] = True
    
    if args.graphtime:
        config['showall'] = False
        config['showtime'] = True
        
    if args.graphhist:
        config['showall'] = False
        config['showhist'] = True
    
    if args.markfile:
        config['markfiles'] = set(args.markfile)
    else:
        config['markfiles'] = None
    
    if args.nofilter:
        config['filterwaypoints'] = False
    else:
        config['filterwaypoints'] = True
    
    if config['showall']:
        config['showtime'] = True
        config['showspeed'] = True
        config['showhist'] = True
        
    
        


    #Check to make sure a valid colormap is set
    allcolormaps = dir(colormaps)
    if not (config['speedcmap'] in allcolormaps and config['timecmap'] in allcolormaps):
        print("")
        print("")

        showcolormaps()

        print("")
        print("")
        
        print("Bad colormap selected.  You need to selected a valid colormap from above (Error 10)")
        print("Better yet go to https://matplotlib.org/examples/color/colormaps_reference.html")
        
        
        exit(10)


if __name__ == "__main__":
    
    parsecmdline()

    #get filename

    if not config['filename']:
        try:
            from tkinter import Tk
            import tkinter.filedialog
        except ImportError:
            print("")
            print("")
            print("You don't have Tkinter installed, this can be installed with python 2.x.  Try reinstalling python 2.x.  Error 8")
            print("If you run the program with the -f [--file] option and specify a filename this error will be bypassed!!!")
            exit(8)
        
        root = Tk()
        config['filename'] = tkinter.filedialog.askopenfilename()
        root.destroy()

        if config['filename'] == ():
            print("Canceled")
            exit(25)

    #for now just load the file we are working with
    data = loaddata(config['filename'])

   

    plotdata(data)
