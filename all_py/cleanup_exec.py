#!/usr/bin/env python3
import shutil
import os

#
# The gitlab-runner launches the executables of the custom executor with
#     TMPDIR=$TMPDIR/custom-executorXXXXXXXXX
# it creates that directory, puts things in it and never deletes it so we do:
#
shutil.rmtree(os.environ['TMPDIR'])

