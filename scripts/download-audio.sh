#!/bin/bash
VIDEO_ID=$1

[ -z "$VIDEO_ID" ] && echo "ERROR: No video ID specified" && exit 1

yt-dlp "https://www.youtube.com/watch?v=$VIDEO_ID" --format m4a -o "./tmp/%(id)s.%(ext)s" 2>&1
yt-dlp -f bestvideo+bestaudio --merge-output-format mp4 "https://www.youtube.com/watch?v=$VIDEO_ID"  
