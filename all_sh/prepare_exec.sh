#!/bin/bash

printf "\033[1;32mThis is $0 launched with args '$*'\033[0m\n"

if [[ $TMPDIR == /tmp/* ]] ; then
    printf "\033[1;31mTMPDIR='${TMPDIR}' starts with '/tmp/' which will not be visible from the submitted job.\033[0m\n"
    printf "We cannot control where the gitlab runner puts scripts for\n"
    printf "run_exec.sh to run except through the environment variable 'TMPDIR'\n"
    printf "Please restart the gitlab runner with TMPDIR pointing to a\n"
    printf "directory on a shared filesystem.  For example something like\n\n"

    printf "    TMPDIR=$HOME/gitlab-runner-tmpdir gitlab-runner run\n\n"

    exit 1
fi

if [[ $TMPDIR != /* ]] ; then
    printf "\033[1;31mTMPDIR='${TMPDIR}' needs to be an absolute path\033[0m\n"
fi
echo "$0: $* (TMPDIR = '$TMPDIR')"
