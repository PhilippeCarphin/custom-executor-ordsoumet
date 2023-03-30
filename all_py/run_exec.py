#!/usr/bin/env python3
import subprocess
import sys
import os

# print(f"\033[1;33mThis is {os.path.basename(sys.argv[0])}, args = {sys.argv}\033[0m", file=sys.stderr)
# sys.stderr.flush()

def main():
    print(f"run_exec: args = '{sys.argv}'")
    SCRIPT_PATH=sys.argv[1]
    STEP_NAME=sys.argv[2]

    if STEP_NAME in ["build_script", "step_script"]:
        print(f"PWD = {os.getcwd()}")
        sys.stdout.flush()
        # run_printer_script(SCRIPT_PATH)
        returncode = run_with_ord_soumet(SCRIPT_PATH)
    else:
        returncode = run_normally(SCRIPT_PATH)

    # Note: To indicate that the user's job failed (as opposed to the executor
    # not being able to perform its task), we must return BUILD_FAILURE_EXIT_CODE
    # There is also SYSTEM_FAILURE_EXIT_CODE.
    if returncode != 0:
        print(f"\033[1;31mStep {STEP_NAME} script returned {returncode}\033[0m", file=sys.stderr)
        return int(os.environ['BUILD_FAILURE_EXIT_CODE'])
    else:
        return 0

def run_with_ord_soumet(script_path):
    this_dir=os.path.dirname(os.path.realpath(__file__))
    ord_run = f"{this_dir}/ord_run.py"
    tmpdir = f"{this_dir}"
    ord_run_args = f"--tmpdir {tmpdir} "
    ord_soumet_args = get_ord_soumet_args()
    # Yes we're running a pythong script as a subprocess from another script
    # If that bothers you I can rewrite this script in another language.
    cmd = f"python3 -u {ord_run} {script_path} {ord_run_args} {ord_soumet_args}"
    print(f"ord_run command : '{cmd}'")
    sys.stdout.flush()
    result = subprocess.run(cmd, shell=True)
    return result.returncode

def get_ord_soumet_args():
    ord_soumet_args = []
    prefix = "CUSTOM_ENV_ORD_SOUMET_"
    for k,v in os.environ.items():
        if not k.startswith(prefix):
            continue
        ord_soumet_args.append(f"-{k[len(prefix):].lower()}")
        ord_soumet_args.append(v)
    return ' '.join(ord_soumet_args)

def run_normally(script_path):
    result = subprocess.run(f"bash {script_path}", shell=True)
    return result.returncode

def run_printer_script(script_path):
    with open(script_path) as f:
        script_printer = f.read().replace('eval', 'echo', 1)
    subprocess.run(["bash", "-c", script_printer])

if __name__ == "__main__":
    sys.exit(main())
