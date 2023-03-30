#!/bin/bash


#
# The gitlab-runner launches the executables of the custom executor with
#     TMPDIR=$TMPDIR/custom-executorXXXXXXXXX
# it creates that directory, puts things in it and never deletes it so we do
#

# STDOUT goes nowhere
echo "$0: TMPDIR = '$TMPDIR'"
# STDERR is shown in the output of the gitlab runner as a warning and nothing
# from this script goes to gitlab.
echo "$0: Cleaning up TMPDIR=${TMPDIR}" >&2
rm -rf $TMPDIR

