#!/usr/bin/env python

# Copyright 2012 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division

import sys
import json
import math
from argparse import ArgumentParser
from datetime import datetime



def main(argv):
    arg_parser = ArgumentParser()
    arg_parser.add_argument("input", help="Input File (JSON)")
    arg_parser.add_argument("-o", "--output", help="Output File (will be overwritten!)")
    arg_parser.add_argument("-f", "--format", choices=["kml", "json", "csv", "js", "gpx", "gpxtracks"], default="kml", help="Format of the output")
    arg_parser.add_argument("-v", "--variable", default="locationJsonData", help="Variable name to be used for js output")
    arg_parser.add_argument("-s", "--startdate", default=None, help="Start of output data yyyy/mm/dd format")
    arg_parser.add_argument("-e", "--enddate", default=None, help="End date of output data yyyy/mm/dd format")
    args = arg_parser.parse_args()
    if not args.output: #if the output file is not specified, set to input filename with a diffrent extension
        args.output = '.'.join(args.input.split('.')[:-1]) + '.'+args.format
    if args.input == args.output:
        arg_parser.error("Input and output have to be different files")
        return

    try:
        json_data = open(args.input).read()
    except:
        print("Error opening input file")
        return

    try:
        data = json.loads(json_data)
    except:
        print("Error decoding json")
        return

    if not args.startdate or not args.enddate:  # if date range not supplied, start and end set to min and max
        start_ms = 0
        end_ms = datetime.now()
    else:
        try:
            start_ms = int(datetime.strptime(args.startdate, "%Y/%m/%d") .strftime("%s"))*1000
        except:
            print("Invalid start date format")
            return
        try:
            end_ms = int(datetime.strptime(args.enddate, "%Y/%m/%d").strftime("%s"))*1000
        except:
            print("Invalid end date format")
            return

    if "locations" in data and len(data["locations"]) > 0:
        try:
            f_out = open(args.output, "w")
        except:
            print("Error creating output file for writing")
            return

        items = data["locations"]

        if args.format == "json" or args.format == "js":
            if args.format == "js":
                f_out.write("window.%s = " % args.variable)

            f_out.write("{\n")
            f_out.write("  \"data\": {\n")
            f_out.write("    \"items\": [\n")
            first = True

            for item in items:
                if int(item["timestampMs"]) < start_ms or int(item["timestampMs"]) > end_ms:
                    continue
                if first:
                    first = False
                else:
                    f_out.write(",\n")
                f_out.write("      {\n")
                f_out.write("         \"timestampMs\": %s,\n" % item["timestampMs"])
                f_out.write("         \"latitude\": %s,\n" % (item["latitudeE7"] / 10000000))
                f_out.write("         \"longitude\": %s\n" % (item["longitudeE7"] / 10000000))
                f_out.write("      }")
            f_out.write("\n    ]\n")
            f_out.write("  }\n}")
            if args.format == "js":
                f_out.write(";")

        if args.format == "csv":
            f_out.write("Time,Location\n")
            for item in items:
                if int(item["timestampMs"]) < start_ms or int(item["timestampMs"]) > end_ms:
                    continue
                f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
                f_out.write(",")
                f_out.write("%s %s\n" % (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000))

        if args.format == "kml":
            f_out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f_out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
            f_out.write("  <Document>\n")
            f_out.write("    <name>Location History</name>\n")
            for item in items:
                if int(item["timestampMs"]) < start_ms or int(item["timestampMs"]) > end_ms:
                    continue
                f_out.write("    <Placemark>\n")
                # Order of these tags is important to make valid KML: TimeStamp, ExtendedData, then Point
                f_out.write("      <TimeStamp><when>")
                f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ"))
                f_out.write("</when></TimeStamp>\n")
                if "accuracy" in item or "speed" in item or "altitude" in item:
                    f_out.write("      <ExtendedData>\n")
                    if "accuracy" in item:
                        f_out.write("        <Data name=\"accuracy\">\n")
                        f_out.write("          <value>%d</value>\n" % item["accuracy"])
                        f_out.write("        </Data>\n")
                    if "speed" in item:
                        f_out.write("        <Data name=\"speed\">\n")
                        f_out.write("          <value>%d</value>\n" % item["speed"])
                        f_out.write("        </Data>\n")
                    if "altitude" in item:
                        f_out.write("        <Data name=\"altitude\">\n")
                        f_out.write("          <value>%d</value>\n" % item["altitude"])
                        f_out.write("        </Data>\n")
                    f_out.write("      </ExtendedData>\n")
                f_out.write("      <Point><coordinates>%s,%s</coordinates></Point>\n" % (item["longitudeE7"] / 10000000, item["latitudeE7"] / 10000000))
                f_out.write("    </Placemark>\n")
            f_out.write("  </Document>\n</kml>\n")

        if args.format == "gpx" or args.format == "gpxtracks":
            f_out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f_out.write("<gpx xmlns=\"http://www.topografix.com/GPX/1/1\" version=\"1.1\" creator=\"Google Latitude JSON Converter\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
            f_out.write("  <metadata>\n")
            f_out.write("    <name>Location History</name>\n")
            f_out.write("  </metadata>\n")
            if args.format == "gpx":
                for item in items:
                    if int(item["timestampMs"]) < start_ms or int(item["timestampMs"]) > end_ms:
                    continue
                    f_out.write("  <wpt lat=\"%s\" lon=\"%s\">\n"  % (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000))
                    if "altitude" in item:
                        f_out.write("    <ele>%d</ele>\n" % item["altitude"])
                    f_out.write("    <time>%s</time>\n" % str(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")))
                    f_out.write("    <desc>%s" % datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
                    if "accuracy" in item or "speed" in item:
                        f_out.write(" (")
                        if "accuracy" in item:
                            f_out.write("Accuracy: %d" % item["accuracy"])
                        if "accuracy" in item and "speed" in item:
                            f_out.write(", ")
                        if "speed" in item:
                            f_out.write("Speed:%d" % item["speed"])
                        f_out.write(")")
                    f_out.write("</desc>\n")
                    f_out.write("  </wpt>\n")
            if args.format == "gpxtracks":
                f_out.write("  <trk>\n")
                f_out.write("    <trkseg>\n")
                lastloc = None
                # The deltas below assume input is in reverse chronological order.  If it's not, uncomment this:
                # items = sorted(data["data"]["items"], key=lambda x: x['timestampMs'], reverse=True)
                for item in items:
                    if int(item["timestampMs"]) < start_ms or int(item["timestampMs"]) > end_ms:
                    continue
                    if lastloc:
                        timedelta = -((int(item['timestampMs']) - int(lastloc['timestampMs'])) / 1000 / 60)
                        distancedelta = getDistanceFromLatLonInKm(item['latitudeE7'] / 10000000, item['longitudeE7'] / 10000000, lastloc['latitudeE7'] / 10000000, lastloc['longitudeE7'] / 10000000)
                        if timedelta > 10 or distancedelta > 40:
                            # No points for 10 minutes or 40km in under 10m? Start a new track.
                            f_out.write("    </trkseg>\n")
                            f_out.write("  </trk>\n")
                            f_out.write("  <trk>\n")
                    f_out.write("      <trkpt lat=\"%s\" lon=\"%s\">\n" % (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000))
                    if "altitude" in item:
                        f_out.write("        <ele>%d</ele>\n" % item["altitude"])
                    f_out.write("        <time>%s</time>\n" % str(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")))
                    if "accuracy" in item or "speed" in item:
                        f_out.write("        <desc>\n")
                        if "accuracy" in item:
                            f_out.write("          Accuracy: %d\n" % item["accuracy"])
                        if "speed" in item:
                            f_out.write("          Speed:%d\n" % item["speed"])
                        f_out.write("        </desc>\n")
                    f_out.write("      </trkpt>\n")
                    lastloc = item
                f_out.write("    </trkseg>\n")
                f_out.write("  </trk>\n")
            f_out.write("</gpx>\n")

        f_out.close()

    else:
        print("No data found in json")
        return


# Haversine formula
def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2):
    R = 6371 # Radius of the earth in km
    dlat = deg2rad(lat2-lat1)
    dlon = deg2rad(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
    math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * \
    math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c # Distance in km
    return d


def deg2rad(deg):
    return deg * (math.pi/180)

def getTimeMS(dt):
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000.0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
