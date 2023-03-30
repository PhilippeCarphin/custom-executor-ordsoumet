#!/bin/bash
#
echo "$0: TMPDIR = '$TMPDIR'" >&2
executor_base_dir=${HOME}/ords/custom_executor_dir

cat <<EOF
{
    "builds_dir": "${executor_base_dir}/builds",
    "cache_dir": "${executor_base_dir}/cache",
    "builds_dir_is_shared": true,
    "hostname": "${HOSTNAME}",
    "driver": {
        "name": "phil test driver",
        "version": "v0.0.1"
    },
    "job_env" : {
        "CUSTOM_ENVIRONMENT": "example"
    }
}
EOF
