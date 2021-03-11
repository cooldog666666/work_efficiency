#!/bin/bash

function finish() {
    echo "[INFO] Reset all root file permissions to current user: $USER"
    local _user=$(id $USER -u)
    local _group=$(id $USER -g)
    cd $WORKSPACE && sudo chown -R ${_user}:${_group} * .*
    echo "[INFO] Reset all root file permissions to current user: $USER [DONE]"
}
trap finish EXIT SIGHUP SIGINT SIGTERM

function die() {
    printf 'ERROR: %s\n' "$@" >&2 
    exit 255 
}

function catch_error() {
    die "An unhandled error occurred at $BASH_SOURCE:$BASH_LINENO"
}

function get_property() {
    var=$1
    echo "[VAR] $var: ${!var}"
}

function technical_debt() {
    echo "[INFO] git credential approve ..." 
    # use same service account for both github and artifactory credentials
    github_hostname=$1
    github_user=$2
    github_password=$3
    artifactory_user=$2
    artifactory_password=$3

    # Cache credentials for a period long enough  (5 days) to perform the import, build and all tests
    git config credential.helper 'cache --timeout 432000' || die "Failed to set credential helper"

    # Set github credentials
    # TODO: test if Jenkins job already stores github credentials
    git credential approve < <(echo -e "protocol=https\nhost=${github_hostname}\nusername=${github_user}\npassword=${github_password}\n") || die "Failed to set credentials for $github_url"    

    # Get the Git LFS url, parse it and set credentials for it
    # TODO: could there be more than one LFS repo?
    declare git_lfs_url=$(git config --file .lfsconfig --get lfs.url)
    [[ $git_lfs_url ]] || die "Failed to obtain Git LFS configuration"
    
    [[ $git_lfs_url =~ ([^:]*)://([^/]*)/(.*) ]] || die "Failed to parse URL $git_lfs_url"

    git credential approve < <(echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n") || die "Failed to set credentials for $url"
}

##############################################################
# Main
##############################################################

echo "[INFO] Getting parameters for MergePush Jenkins (github plugin) build"
[[ -n ${GIT_URL} ]] || die "GIT_URL env variable not set by Jenkins job"
[[ -n ${GIT_BRANCH} ]] || die "GIT_BRANCH env variable not set by Jenkins job"
github_url=$(git config --get remote.origin.url)
github_url=${github_url#git@}
github_url=${github_url#http*://}
github_url=${github_url%:*}
declare ci_github_hostname=${github_url%%/*}
declare ci_git_target_branch=${GIT_BRANCH/#origin\//}
declare ci_build_branch=${BUILD_BRANCH:-${ci_git_target_branch}}

for prop in GIT_URL GIT_BRANCH ci_github_hostname BUILD_BRANCH ci_build_branch ci_git_target_branch BUILD_COMPONENT
do
    get_property $prop
done

git checkout $ci_build_branch || die "Fail to checkout branch: $ci_build_branch"
head_commit_id=$(git rev-parse HEAD)
echo "[INFO] HEAD: ${head_commit_id} @BRANCH: ${ci_build_branch}"
git log --graph --pretty=format:'%h -%d%s (%cr) <%an>' --abbrev-commit -10
echo ""
technical_debt $ci_github_hostname ${USERNAME} ${!USERNAME}
echo "[RUN] git pull"
git pull
echo "[RUN] git lfs pull"
git lfs pull
echo -e "###################\n# build_all image #\n###################"
build_all -f RETAIL +image

