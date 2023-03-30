#!/bin/bash
set -u

printf "\033[36m$0: $*\033[0m\n"
this_dir=$(cd $(dirname $0) && pwd)

main(){
    local -r script_path=$1
    local -r step_name=$2
    local -r ord_run="${this_dir}/ord_run.sh"
    return_code=0

    if [[ -v CUSTOM_EXECUTOR_DEMO ]] ; then
        printf "\033[1;35mPrinting environment\033[0m\n"
        env -0 | sort -z | tr '\0' '\n'
        printf "\033[1;35mPrinting readable version of script ${script_path}\033[0m\n"
        cat ${script_path} | sed 's/^: |/echo/' | bash
    fi

    case ${step_name} in
        build_script|step_script)
            printf "\033[35mRunning the script with ${this_dir}/ord_run.sh\033[0m\n"
            ${ord_run} ${script_path} $(get_ord_soumet_args)
            return_code=$?
            ;;
        *)
            printf "\033[35mRunning the script normally with BASH\033[0m\n"
            bash ${script_path}
            return_code=$?
            ;;
    esac

    if ((return_code != 0)) ; then
        printf "$0: \033[1;31mStep ${step_name} returned ${return_code}\033[0m\n"
        return ${BUILD_FAILURE_EXIT_CODE}
    else
        return 0
    fi

}

#
# Get arguments for ord_soumet from environment
#
function get_ord_soumet_args(){
    # gitlab passes variables form the YAML through the environment
    # as CUSTOM_ENV_<yaml-var-name>, we only care about the ones
    # where <yaml-var-name> is ORD_SOUMET_<ord-soumet-argname>.
    # We output -<X> <Y>
    # where <X> is the part of the name that comes after CUSTOM_ENV_ORD_SOUMET
    # changed to lowercase, and <Y> is the value of the variable.
    #
    # Ex: CUSTOM_ENV_ORD_SOUMET_TMPFS=2G becomes '-tmpfs 2g'
    local name value
    env -0 | while IFS='=' read -r -d '' name value; do
        if [[ "$name" == CUSTOM_ENV_ORD_SOUMET_* ]] ; then
            local upper_name=${name#CUSTOM_ENV_ORD_SOUMET_}
            local lower_name=${upper_name,,}
            printf -- " -${lower_name} ${value}"
        fi
    done
}


main "$@"
