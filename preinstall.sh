#!/bin/sh
ARGV1=$1 # First argument is temp folder during install
find /tmp/uploads/$ARGV1 -type f -print0 | xargs -0 dos2unix -q 
# Exit with Status 0
exit 0
