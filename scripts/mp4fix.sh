set -xeo pipefail


TRACKS_DIR="output/popular_youtube/tracks"

for file in $(ls $TRACKS_DIR)
do
    track_file="$TRACKS_DIR/$file"
    track_temp_file="$track_file.tmp"

    format=$(ffprobe -show_format "$track_file" 2>/dev/null | grep "format_long_name")
    if [[ $format == *"MP2/3"* ]]
    then
        continue
    elif [[ $format == *"QuickTime"* ]]
    then
        ffmpeg -i "$track_file" -c:a libmp3lame -f mp3 "$track_temp_file"
        mv "$track_temp_file" "$track_file"
    fi
    echo $format
done
