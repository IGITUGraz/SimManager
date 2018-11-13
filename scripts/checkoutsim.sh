#!/usr/bin/env bash
# Syntax:
# 
#   checkoutsim.sh <simulation output directory>
# 
# This script must be run from the root directory. This function checks out a particular simulation. This means that it checks
# out the commit and applies the patch corresponding to the experiment in the
# specidied directory. The directory should be one that was create using the
# SimManager class. Since this script performs a checkout, you will need to
# reset the state of your repository to a clean state in order for this to
# work.

if [[ -z "$1" ]]; then
	echo "Syntax:"
	echo ""
	echo "  checkoutsim.sh <simulation output directory>"
	echo ""
	echo "This function checks out a particular simulation. This means that it checks"
	echo "out the commit and applies the patch corresponding to the experiment in the"
	echo "specidied directory. The directory should be one that was create using the"
	echo "SimManager class. Since this script performs a checkout, you will need to"
	echo "reset the state of your repository to a clean state in order for this to"
	echo "work."
fi
sim_result_dir=$1

commit_id=$(cat "$sim_result_dir/.commit_id") &&
    git checkout $commit_id && git submodule update --init --recursive &&
    (cat "$sim_result_dir/.patch" | subpatch.sh apply)
