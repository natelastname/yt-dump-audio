#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2024-04-28T08:46:25-04:00

@author: nate
"""
import os
import argparse
import sys
import subprocess
import re
import json

import datetime

basedir = os.path.dirname(__file__)

parser = argparse.ArgumentParser(description="Dowload a channel as audio")
parser.add_argument('link', type=str, help='Link to the channel')

parser.add_argument('--no-delete',
                    action=argparse.BooleanOptionalAction,
                    help="Do not delete any metadata files")

parser.add_argument('--debug',
                    action=argparse.BooleanOptionalAction,
                    help='Assume metadata and videos have already been downloaded')



args = parser.parse_args()

# Preffered format: m4a, 128kps


def subproc(cmd):
    result = subprocess.call(cmd.strip(), shell=True)
    return result

#res = re.search('youtube\.com/@(.*)[$/]$', args.link)

res = re.search('youtube\.com/@([^/]+)/*$', args.link)

if not res:
    print("Couldn't extract channel name")
    sys.exit(1)

channel = res.groups()[0]

outpath = os.path.join(basedir, "output", channel)
os.makedirs(outpath, exist_ok=True)

fmt_str = '%(id)s.%(ext)s'

cmd = f"""
yt-dlp -P '{outpath}'\
    -o '{fmt_str}'\
    --write-info-json --skip-download\
    --extract-audio --audio-format m4a --audio-quality 128kps\
    '{args.link}'
"""

if not args.debug:
    subproc(cmd)


cmd = f"""
yt-dlp -P '{outpath}'\
    -o '{fmt_str}'\
    --extract-audio --audio-format m4a --audio-quality 128kps\
    '{args.link}'
"""

if not args.debug:
    subproc(cmd)

def set_metadata_tag(vid_path, metadata):

    outpath = os.path.dirname(vid_path)
    vid_name = os.path.basename(vid_path)
    tempfile = os.path.join(outpath, f"tmp.{vid_name}")
    for key, val in metadata.items():
        cmd = f"""
ffmpeg -i '{vid_path}' -c copy -metadata {key}='{val}' '{tempfile}'
        """
        subproc(cmd)
        cmd = f"""
mv '{tempfile}' '{vid_path}'
        """
        subproc(cmd)

    pass

def process_callback(vid_info, vid_path):
    '''
    Now we have the audio file and the .info.json,
    assign any fancy name or metadata here
    '''
    uri = "https://www.youtube.com/watch?v="+vid_info['id']

    date = datetime.datetime.fromtimestamp(vid_info['epoch'])


    metadata = {
        'artist': vid_info['channel'],
        'title': vid_info['title'],
        'album': vid_info['playlist'],
        'track': vid_info['playlist_index'],
        'description': uri
    }

    return metadata



meta = {}
for item in os.scandir(path=outpath):
    if not item.is_file():
        print("Not file, skipping...")
        continue

    item_id = re.search('(.*)\.info\.json$', item.name)

    if not item_id:
        print("Not info.json, skipping...")
        continue

    item_id = item_id.groups()[0]

    fp = open(item.path, 'r')
    item_data = json.load(fp)

    vid_file = f"{item_id}.m4a"
    vid_path = os.path.join(outpath, vid_file)
    if not os.path.isfile(vid_path):
        print("Not video metadata, skipping...")
        # It could be the channel metadata or something
        continue

    vid_path = os.path.join(outpath, vid_path)

    meta[vid_path] = process_callback(item_data, vid_path)


for vid_path, metadata in meta.items():

    if any(map(lambda item: len(item[1]) == 0, metadata.items())):
        breakpoint()
        pass

    breakpoint()
    #ffmpeg -i input.mp3 -c copy -metadata artist="Someone" output.mp3
    set_metadata_tag(vid_path, metadata)


if args.no_delete or args.debug:
    sys.exit(0)

# Clean up
for item in os.scandir(path=outpath):
    if not item.is_file():
        print("Not file, skipping...")
        continue

    if item.name.endswith("m4a"):
        continue

    cmd = f"""
rm '{item.path}'
    """
    subproc(cmd)



sys.exit(0)


