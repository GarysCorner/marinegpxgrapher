#Marine GPX Grapher

##Status
While I expect this program to be very useful, and I may not put a ton of extra work into it unless their is some interrest.  This program is not as polished as I would like.  However I have learned that when it comes to writing free code is that if you tell yourself "I'll upload it when its perfect" then you won't ever upload it...  So here it is.

##Usage
Just run the program using python (this usually justs means double click it), but this depends on your system. The system will then process the files and show 3 graphs.  The 3 graphs may appear on top of each other so feel free to move them around.  the graphs appear in different windows since I expect the user to be comparing the data with a traditionall chart plotter like OpenCPN.

##Description
This program was originally intended to process tracking data from my Garmin Quatrix 3 marine watch.  You may see some references to "garmindata.py" in the git history this is because the originally intention was specifically for garmin export data, however when I learned more I realized the program should work with any standard GPX tracking data.

This program is designed to graph GPX tracking data for marine application.  I wrote it to get a more useful understanding of tracking data from regattas.  The basic problem is that tracking data doesn't tell a very good story without speed and/or time data.  While programs like OpenCPN are very useful I didn't find the display of tracking data was adequite.  To solve this I wrote this program which I intend to be used with a chart plotter like OpenCPN to provide additional data and allow you to form a good narrative about your last race.  If you look back at git revision history you may notice that I originally was writing this code to tear down the GPX data into a better format, but the project kept evolving and became what it is now.  Hope you find it useful.

##Sorries
Sorry about my spelling, also sorry I hacked this out soo quick as of the writing of this there are still parts of the datastructure like "latrad/lonrad" which no longer serve a function other than eating up ram, but Im working on it.  Also I plan on putting some direction for my Windows users who probably don't have python, and the libraries installed.  
