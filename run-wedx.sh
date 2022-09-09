#!/bin/bash

DIR=$(dirname $0)
if [ ! -d "${DIR}/.venv" ]; then
    echo 'venv not found. run `venv init`'
    CMD='python3 -m venv .venv'
    echo $CMD
    eval $CMD
fi

CMD='source .venv/bin/activate'
echo $CMD
eval $CMD

CMD='pip3 install --upgrade pip'
echo $CMD
eval $CMD

case "$(uname -s)" in
    Darwin*)
        CMD='pip3 install -r requirements/macos_x86_64.txt'
        echo $CMD
        eval $CMD
        ;;
    Linux*)
        CMD='pip3 install -r requirements/manylinux_x86_64.txt'
        echo $CMD
        eval $CMD
        ;;
esac

CMD='python3 src/main.py'
echo $CMD
eval $CMD
