#!/bin/bash -e
# This script is taken from https://gist.github.com/tomykaira/40abc2ba411be28bee67

separator="----8<----8<----8<----8<----"

function make_chunk {
    cd $1
    if ! git diff-index --quiet HEAD -- . ':(exclude)*.ipynb'; then
        echo "${PWD#$root}/"  # get current directory relative to directory top
        git diff-index --patch --no-color HEAD -- . ':(exclude)*.ipynb'
        echo "$separator"
    fi
}

case "$1" in
    "make" )
        root=$(git rev-parse --show-toplevel)

        # exit if not in a repository
        git_error_code="$?"
        if [[ $git_error_code -ne 0 ]]; then
            exit $git_error_code
        fi

        make_chunk $root
        for module in $(git submodule  foreach --recursive 'echo $toplevel/$path' | grep -v Entering); do
            make_chunk $module
        done
    ;;
    "apply")
        root=$(git rev-parse --show-toplevel)

        # exit if not in a repository
        git_error_code="$?"
        if [[ $git_error_code -ne 0 ]]; then
            exit $git_error_code
        fi

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
