
main(){
    local script=$1 ; shift
    local soumet_args="$*"

    local jobdir=$(mktemp -d $TMPDIR/ord_run_tmp.XXXXXX)
    local job=${jobdir}/user_job.sh
    local output_file=${jobdir}/output.txt
    local exit_code_file=${jobdir}/exit_code_file

    #
    # Create a job that calls the script that the gitlab runner wants
    # us to run
    #
    cat <<-EOF > ${job}
    #!/bin/bash
    $(realpath ${script}) >> ${output_file} 2>&1
    echo \$? > ${exit_code_file}
EOF

    #
    # Setup signal handlers and cleanup.  If someone clicks 'cancel' in the
    # gitlab interface, the gitlab runner will send us a 'SIGINT' which
    # we will react to by stopping the job with jobdel.
    #
    trap 'sigint_handler' SIGINT
    trap 'cleanup' EXIT

    #
    # The output of this tail process gets forwarded by the gitlab runner
    # to the gitlab web interface
    #
    touch ${output_file}
    setsid tail -f ${output_file} &
    TAIL_PROCESS=$!

    #
    # Submit the job
    #
    ord_soumet_cmd="ord_soumet ${job} ${soumet_args}"
    printf "\033[1;37mord_soumet command : '${ord_soumet_cmd}'\033[0m\n"
    jobid=$(${ord_soumet_cmd} > ${jobdir}/jobid && cat ${jobdir}/jobid)
    printf "\033[1mSubmission complete: jobid is '\033[1;32m${jobid}\033[0m'\n"

    #
    # Wait for the job to end by polling.  If an abort was requested
    # do a jobdel command and go back to waiting for the job to end
    #
    while true ; do
        if [[ -n ${ABORT_REQUESTED} ]] ; then
            printf "Running jobdel command 'jobdel ${jobid%.*}'\n"
            jobdel ${jobid%.*}
            unset ABORT_REQUESTED
        fi
        jobst_output=$(jobst -j ${jobid%.*} --format csv)
        printf "jobst_output : ${jobst_output}\n"
        job_status_code=$(echo ${jobst_output} | cut -d , -f 3)
        printf "job_status_code : '${job_status_code}'\n"
        case ${job_status_code} in
            ""|E|CD|CA) break ;;
        esac
        sleep 5
    done

    #
    # Report the exit code back to the caller
    #
    exit_code=$(cat ${exit_code_file})
    echo "The job exit code is '${exit_code}'"
    if [[ -z ${exit_code} ]] ; then
        echo "Could not get exit code for job"
        return 1
    else
        return ${exit_code}
    fi
}

function cleanup(){
    echo "killing tail process : ${TAIL_PROCESS}"
    kill ${TAIL_PROCESS}

    # What follows could just be 'rm -rf ${jobdir}'
    # But I prefer, if I can, to have at least a hardcoded component
    # to arguments to rm -rf in a script.
    tmpdir_suffix=${jobdir#$TMPDIR/ord_run_tmp.}
    rm -rf $TMPDIR/ord_run_tmp.${tmpdir_suffix}
}

function sigint_handler(){
    echo "SIGINT received, requesting abort"
    ABORT_REQUESTED=TRUE
}

main "$@"
