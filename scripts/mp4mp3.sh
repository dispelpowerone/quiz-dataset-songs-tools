set -eo pipefail


SRC_PATH="$1"
DEST_PATH="$2"
DEST_TEMP_PATH="$DEST_PATH.tmp"

rm -f "$DEST_TEMP_PATH"
ffmpeg -i "$SRC_PATH" -c:a libmp3lame -f mp3 "$DEST_TEMP_PATH"
mv "$DEST_TEMP_PATH" "$DEST_PATH"
