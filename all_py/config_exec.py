#!/usr/bin/env python3
import subprocess
import sys
import json
import os
from pprint import pprint

base_dir = os.environ["HOME"]

json.dump({
    # f"/builds/{CUSTOM_ENV_CI_CONCURRENT_PROJECT_ID}/${CUSTOM_ENV_CI_PROJECT_PATH_SLUG}",
    "builds_dir": f"{base_dir}/ords/custom-executor-builds/",
    "cache_dir": f"{base_dir}/ords/custom-executor-builds/",
    "builds_dir_is_shared": True,
    "hostname": "ppp5",
    "driver": {
        "name": "phil test driver",
        "version": "v0.0.1"
    },
    "job_env" : {
        "CUSTOM_ENVIRONMENT": "example"
    }

}, fp=sys.stdout)

