#!/usr/bin/env -S python3 -u
import sys
import subprocess
import tempfile
import os
import time
import signal
import argparse
import stat
import shutil

"""
"Run" a script with ord_soumet.

Take a script as an argument, wrap it, and submit the wrapped script to the
scheduler using ord_soumet.

simplified wrapper:

    input-script 2>&1 > output_file
    echo $? exit_code_file

Then launch a subproces doing 'tail -f' of the output file so that the output
of the input-script becomes the output of this process.

Poll the job ID to wait for the job to finish.

Once the job has ended, get the exit code of input-script and exit with that
code.
"""

def get_args():
    p = argparse.ArgumentParser(description="Run jobs with ord_soumet forwarding output and exit code")
    p.add_argument("--tmpdir", help="Prefix for creation of directory containing files", default=os.environ['TMPDIR'])
    p.add_argument("--keep-tmp", action='store_true', help="Do not delete temporary files after job completion")
    return p.parse_known_args()

def main():
    args, other_args = get_args()
    user_script = other_args[0]
    ord_soumet_args = other_args[1:]

    job = OrdJob(user_script, ord_soumet_args, tempdir_prefix=args.tmpdir, keep_tmp=args.keep_tmp)
    print(f"Creating job files in directory '{job.dir}'")
    signal.signal(signal.SIGINT, lambda signum, frame: job.delete())
    signal.signal(signal.SIGTERM, lambda signum, frame: job.delete())

    job.start()
    print(f"Job submission ended: job_id is {job.job_id}")

    job.wait(poll_interval=4)

    job_exit_code = job.get_exit_code()
    if job_exit_code is None:
        print("Could not get exit code of job")
        return 1
    else:
        return job_exit_code

class OrdJob():
    def __init__(self, gitlab_script, ord_soumet_args, tempdir_prefix=None, keep_tmp=False):
        self.dir = tempfile.mkdtemp(prefix="ord_run_temp_", dir=tempdir_prefix)
        self.keep_tmp = keep_tmp
        if tempdir_prefix:
            self.user_script = os.path.join(tempdir_prefix, "user_script.sh")
            shutil.copy2(os.path.realpath(gitlab_script), self.user_script)
        else:
            self.user_script = os.path.realpath(user_script)
        self.output_file = os.path.realpath(f"{self.dir}/output_file")
        self.user_job = os.path.realpath(f"{self.dir}/user_job")
        self.exit_code_file = os.path.realpath(f"{self.dir}/exit_code_file")
        self.ord_soumet_args = ord_soumet_args
        self.tail_process = None
        self.job_id = None
        self.job_id_for_jobst_and_jobdel = None
        self.jobdel_requested = False
        self.cell_name = get_cell_name(ord_soumet_args)

    def start(self):
        self._start_tail()
        self._write_user_job()
        self._submit_user_job()

    def check_status(self):
        if self.cell_name:
            cmd = f"jobst -c {self.cell_name} -j {self.job_id_for_jobst_and_jobdel} --format csv"
        else:
            cmd = f"jobst -j {self.job_id_for_jobst_and_jobdel} --format csv"
        print(f"Running jobst command '{cmd}'")
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            print(f"jobst command {cmd} returned non-zero: {result.returncode}")
            return None

        lines = result.stdout.splitlines()
        if len(lines) > 1:
            raise RuntimeError(f"jobst command '{cmd}' returned more than one result")
        output = lines[0]
        if output == "":
            return None

        fields = output.split(',')
        status = fields[2]
        return status

    def delete(self):
        print(f"Delete request received")
        if self.job_id is None:
            print(f"Delete requested before job_id is known.  Job will be deleted at first poll interval")
            self.jobdel_requested = True
            return

        if self.cell_name:
            cmd = f"jobdel -c {self.cell_name} {self.job_id_for_jobst_and_jobdel}"
        else:
            cmd = f"jobdel {self.job_id_for_jobst_and_jobdel}"
        print(f"Running jobdel command '{cmd}'")
        subprocess.run(cmd, shell=True)

    def get_exit_code(self):
        if not os.path.exists(self.exit_code_file):
            print(f"No exit code file for job {self.job_id}")
            return None
        with open(self.exit_code_file) as f:
            text = f.read().strip()
        return int(text)

    def wait(self, poll_interval):
        while True:
            if self.jobdel_requested:
                self.delete()
                self.jobdel_requested = False
            status = self.check_status()
            print(f"Job {self.job_id} has status {status}")
            if status in [None, "E", "CD", "CA"]:
                break
            time.sleep(poll_interval)

    def _start_tail(self):
        # touch the output file so we can begin the tail immediately
        open(self.output_file, 'w').close()
        self.tail_process = subprocess.Popen(['tail', '-f', self.output_file]);

    def _submit_user_job(self):
        ord_soumet_command = f"ord_soumet {self.user_job} {' '.join(self.ord_soumet_args)}"
        print(f"Running ord_soumet command '{ord_soumet_command}'")
        with open(f"{self.dir}/jobid", 'w') as f:
            result = subprocess.run(ord_soumet_command, shell=True, stdout=f)
        if result.returncode != 0:
            raise RuntimeError("ord_soumet command failed")
        with open(f"{self.dir}/jobid") as f:
            self.job_id = f.read().strip()
        #self.job_id = result.stdout.decode('utf-8').strip()
        self.job_id_for_jobst_and_jobdel = get_jobid_for_jobst_and_jobdel(self.job_id, self.cell_name)
        if self.job_id == "":
            raise RuntimeError(f"ord_soumet did not return a job_id (job_id='{self.job_id}')")

    def _write_user_job(self):
        wrapper_script = f'''#!/bin/bash
        {self.user_script} >> {self.output_file} 2>&1
        echo $? > {self.exit_code_file}'''
        with open(self.user_job, 'w') as f:
            f.write(wrapper_script)
        print(wrapper_script)
        sys.stdout.flush()

    def __del__(self):
        if self.tail_process:
            print(f"Killing tail process {self.tail_process.pid}")
            self.tail_process.send_signal(signal.SIGTERM);
        if not self.keep_tmp:
            shutil.rmtree(self.dir)

def get_cell_name(ord_soumet_args):
    for i, arg in enumerate(ord_soumet_args):
        if arg in ["-mach", "-d"]:
            # Assume that if '-mach' or '-d' is used then there is a next arg
            return arg[i+1]

def get_jobid_for_jobst_and_jobdel(job_id, cell_name):
    """
    Annoying: on the machines listed in the variable 'cell_name', the job IDs
    are of the form <some-numbers>.<hostname-where-job-is-running> but we need
    to pass just the <some-numbers> part to jobst and jobdel
    """
    if cell_name not in ['ppp5', 'ppp6', 'robert', 'underhill']:
        return job_id.split('.')[0]
    return job_id

if __name__ == "__main__":
    sys.exit(main())
