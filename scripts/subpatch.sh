#!/bin/bash -e
# This script is taken from https://gist.github.com/tomykaira/40abc2ba411be28bee67

separator="----8<----8<----8<----8<----"

function make_chunk {
    cd $1
    if ! git diff-index --quiet HEAD -- . ':(exclude)*.ipynb'; then
        echo "${PWD#$root}/"
        git diff-index --patch --no-color HEAD -- . ':(exclude)*.ipynb'
        echo "$separator"
    fi
}

case "$1" in
    "make" )
        root=$PWD
        make_chunk $PWD
        for module in $(git submodule  foreach --recursive 'echo $toplevel/$path' | grep -v Entering); do
            make_chunk $module
        done
    ;;
    "apply")
        root=$PWD
        IFS=''
        while read pwd; do
            patch=""
            while read -r line; do
                if [ "$line" = "$separator" ]; then
                    break
                fi
                patch="$patch$line"$'\n'
            done
            echo Patching $root$pwd
            cd $root$pwd

            echo "$patch" | git apply --index || true
        done
        unset IFS
    ;;
    *)
        echo "Unknown command"
        exit 1
        ;;
esac
