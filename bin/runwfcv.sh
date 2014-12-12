#!/bin/bash

# find the directory that holds the script
# - see http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in/246128#246128
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
BIN="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

#echo $BIN

# assumption: this bash script is in the $BIN directory
DATA=$BIN/../data
CODE=$BIN/../code

PDATE=$1
MONTHS=$2

# run the python script to execute walk forward cross validation
# assumption: the python script is in the $CODE directory
# assumption: the data files are in the $DATA directory
python $CODE/runwfcv.py $DATA/business.json $DATA/review.json $DATA/tip.json $DATA/sentiment.csv "$@"

