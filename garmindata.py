import math
from datetime import datetime
import xml.dom.minidom as xml

#earths size in nautical miles we will use this later
earthsize = 21637.508


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
    latrad = math.radians(lat+180)

    lonrad = math.cos(latrad) * math.radians(lon)
    print "%f vs %f" % (math.radians(lon),lonrad)

    return latrad,lonrad


"""
    Calculate distance between two points in nautical miles
"""
def calcdist(pt1, pt2):
    latrad1, lonrad1 = convlatlon(pt1['lat'],pt1['lon'])
    latrad2, lonrad2 = convlatlon(pt2['lat'],pt2['lon'])
        
    return math.sqrt((latrad1-latrad2)**2 + (lonrad1-lonrad2)**2) * earthsize
        


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

    return data


"""
    Convert Garmin UTC format to datetime object
"""
def convdatetime(dtstr):
    return datetime.strptime(dtstr,"%Y-%m-%dT%H:%M:%SZ")



if __name__ == "__main__":
    
    print "Starting..."

    #for now just load the file we are working with
    data = loaddata("2018-07-29 03_36_41 Around the Lake Race Cookie Monster.gpx")

    for i in range(len(data['data'])-1):
        print calcspeed(data['data'][i], data['data'][i+1])


