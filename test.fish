#!/usr/bin/fish

. env/bin/activate.fish

if test (which randomname)
    set PREV_BRANCH_NAME (git symbolic-ref --short HEAD)
    set -x RUN_NAME (randomname get)
    mkdir -p runs/$RUN_NAME
    # create a new commit with the current state of the working directory on a new branch
    git checkout -b run/$RUN_NAME
    git commit -a -m "Commit of src at run $RUN_NAME"
    git checkout --detach HEAD
    git reset --soft $PREV_BRANCH_NAME
    git checkout $PREV_BRANCH_NAME

    python train.py
else
    echo "randomname not installed. run pip install"
end
