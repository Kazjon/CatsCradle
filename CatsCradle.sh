#!/bin/bash

export PATH="/home/bill/anaconda2/bin:$PATH"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

export PATH=/home/bill/Desktop:/usr/local/cuda-9.0/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PYTHONPATH="/home/bill/anaconda2/local/lib/python2.7/dist-packages/:$PYTHONPATH"

python /home/bill/Desktop/CatsCradle-master/CatsCradle.py
