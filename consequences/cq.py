'''
This module is used to
1.
Start the process by emailing a form link to all the participants

2.
Finish by emailing a "consequence" to each participant
'''

import config
import os
import pprint
from datetime import datetime
import xml.etree.ElementTree as ET
import collections
from yattag import Doc, indent

TRACK_PREFIXES = ["BEACH", "CAMPING", "KURA", "LODGE", "QB", "TELE"]
STILL_ALIVE_SYMBOL = "Flag, Blue"
NAMESPACE = "http://www.topografix.com/GPX/1/1"

cf = config.ConfigFile()
raw_waypoints_files_path = (cf.configfile[cf.computername]['raw_waypoints_files_path'])

def waypoints_sort_key(filename):
    # example Waypoints_03-SEP-17.gpx
    # return the date time equivalent of the 03-SEP-17
    waypoint_day = filename[10:12] # %d
    waypoint_month = filename[13:16] # close to %b = Sep
    waypoint_month_to_use = waypoint_month[0] + waypoint_month[1:3].lower()
    waypoint_year = filename[17:19] # %y

    waypoint_date = waypoint_year + waypoint_month_to_use + waypoint_day
    waypoint_as_datetime = datetime.strptime(waypoint_date, "%y%b%d")

    return waypoint_as_datetime

# https://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
# https://docs.python.org/2/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
def tag_only(tag_and_URI):
    # Strips off the Namespace that is attached to the tag at the beginning
    # for example will replace {http://www.topografix.com/GPX/1/1}wpt with wpt
    tag_only = tag_and_URI.replace("{" + NAMESPACE + "}", "")
    return tag_only

def add_uri_to_tag(tag):
    return "{" + NAMESPACE + "}" + tag


def create_marble_files():

    # Get a list of all the files and folders in the raw_waypoints directory
    date_folders = [d for d in os.listdir(raw_waypoints_files_path) if \
        os.path.isdir(os.path.join(raw_waypoints_files_path, d))]

    # get the folder to use (the most recent) - format expected to be yyyy-mm-dd
    date_folders.sort(key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    folder_to_use = date_folders[-1]
    folder_to_use_filepath = os.path.join(raw_waypoints_files_path, folder_to_use)
    print(folder_to_use_filepath)

    # within this folder we are assuming there to be 1 or more text files of the form
    # Waypoints_03-SEP-17.gpx
    # we need to go through them most recent first
    # order them from the most recent to the oldest
    # thus in the unlikely event that we have repeated names only the most
    # up to date version of the name will be used. (Haven't thought this through thoroughly)
    waypoints_filenames = os.listdir(folder_to_use_filepath)
    waypoints_filenames.sort(key = waypoints_sort_key, reverse=True)
    print(waypoints_filenames)

    # open each filename in turn and extract waypoints that are still alive
    # they will be in a dictionary with key "name"
    # note that if a name appears more than once only the first (ie most recent)
    # version will be used
    all_waypoints = {}
    all_still_alive_waypoints = {}
    Waypoint = collections.namedtuple('Waypoint', 'lat lon ele sym')
    for wp_filename in waypoints_filenames:
        tree = ET.parse(os.path.join(folder_to_use_filepath, wp_filename))
        root = tree.getroot()
        for wpt in root.findall(add_uri_to_tag("wpt")):
            print()
            # get the name of this waypoint
            wpt_name = wpt.find(add_uri_to_tag("name")).text

            # if this name is not already in the all_waypoint dictionary add a record
            if not wpt_name in all_waypoints:
                wpt_lat = wpt.attrib["lat"]
                wpt_lon = wpt.attrib["lon"]
                wpt_ele = wpt.find(add_uri_to_tag("ele")).text
                wpt_sym = wpt.find(add_uri_to_tag("sym")).text
                all_waypoints[wpt_name] = Waypoint(wpt_lat, wpt_lon, wpt_ele, wpt_sym)

    all_still_alive_waypoints = {key: all_waypoints[key] for key in all_waypoints \
        if all_waypoints[key].sym == STILL_ALIVE_SYMBOL}

    pprint.pprint(all_still_alive_waypoints)

    # create the .gpx files for each track
    # here is an example of a wpt entry
    '''
    <wpt lat="-37.037798" lon="174.511325">
        <ele>4.663168</ele>
        <name>TESTQB01~(A24)</name>
    </wpt>
    '''
    waypoints_for_track = {}

    filename_start = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

    for track_prefix in TRACK_PREFIXES:
        # for yattag
        doc, tag, text = Doc().tagtext()
        waypoints_for_track = {key: all_still_alive_waypoints[key] \
            for key in all_still_alive_waypoints if key.startswith(track_prefix)}
        for k, v in sorted(waypoints_for_track.items()): # sorts by key
            print(k, v)

        with tag('gpx', xmlns="http://www.topografix.com/GPX/1/1"):
            for k, v in sorted(waypoints_for_track.items()):
                with tag('wpt', lat=v.lat, lon=v.lon):
                    with tag('name'):
                        text(k)
                    with tag('ele'):
                        text(int(float(v.ele))) # round elevation to nearest metre

        result = indent(
            doc.getvalue(),
            indentation = ' '*4,
            newline = '\r\n'
        )

        # write gpx file
        marble_waypoints_files_path = (cf.configfile[cf.computername]['marble_waypoints_files_path'])
        marble_filename = filename_start + "_" + track_prefix + os.extsep + "gpx"
        subfolder_name = filename_start
        marble_filepath = os.path.join(marble_waypoints_files_path, subfolder_name, marble_filename)

        os.makedirs(os.path.dirname(marble_filepath), exist_ok=True)
        with open(marble_filepath, "w") as myfile:
            myfile.write(result)

    return True



if __name__ == '__main__':

    import sys
    import argparse
    import ast

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # create the parser for the create_internal_release function
    create_marble_files_parser = subparsers.add_parser('create_marble_files')
    create_marble_files_parser.set_defaults(function = create_marble_files)

    # parse the arguments
    arguments = parser.parse_args()
    arguments = vars(arguments) #convert from Namespace to dict

    #attempt to extract and then remove the function entry
    try:
        function_to_call = arguments['function']
    except KeyError:
        print ("You need a function name. Please type -h to get help")
        sys.exit()
    else:
        #remove the function entry as we are only passing arguments
        del arguments['function']

    if arguments:
        #remove any entries that have a value of 'None'
        #We are *assuming* that these are optional
        #We are doing this because we want the function definition to define
        #the defaults (NOT the function call)
        arguments = { k : v for k,v in arguments.items() if v is not None }

        #alter any string 'True' or 'False' to bools
        arguments = { k : ast.literal_eval(v) if v in ['True','False'] else v
                                              for k,v in arguments.items() }

    result = function_to_call(**arguments) #note **arguments works fine for empty dict {}

    print (result)
