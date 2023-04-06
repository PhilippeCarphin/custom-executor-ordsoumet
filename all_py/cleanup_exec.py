#!/usr/bin/env python3
import shutil
import os
import sys
import subprocess
import re

#
# The gitlab-runner launches the executables of the custom executor with
#     TMPDIR=$TMPDIR/custom-executorXXXXXXXXX
# it creates that directory, puts things in it and never deletes it so we do:
#
def get_intended_tmpdir():
    """
    The gitlab runner appends an entry TMPDIR=<intended-tmpdir> causing
    two strings of the form 'TMPDIR=...' to be in the environ array with
    the later one being the right one.

    The newer versions of the go standard library package os.exec calls
    a function 'dedupEnv' which removes duplicates by selecting only the
    latest value.  The v12.1.0 version was not compiled with a late enough
    version of the Go toolchain.

    Because of how Python constructs its os.environ dictionary, it retains
    the earlier TMPDIR which is not the intended one.

    Without knowing how it is implemented in BASH, I do know that the result
    is that it selects the later one.

    See https://github.com/PhilippeCarphin/env_var_duplicate for some
    experiments on how duplicates definitions in the array environ affect
    C, Bash, Python differently.
    """
    return subprocess.run(
            "echo $TMPDIR",
            shell=True,
            universal_newlines=True,
            stdout=subprocess.PIPE
    ).stdout.strip()

tmpdir = get_intended_tmpdir()

if not re.match(r'.*/custom-executor[0-9]+', tmpdir):
    print(f"Value of TMPDIR is fishy: '{tmpdir}'", file=sys.stderr)
    sys.exit(1)

print(f"\033[36mThis is cleanup_exec.py running TMPDIR='{tmpdir}'\033[0m", file=sys.stderr)
shutil.rmtree(tmpdir)

