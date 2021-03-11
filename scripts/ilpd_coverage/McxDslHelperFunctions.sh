###############################################################################
#
#   McxDslHelperFunctions.sh contains shell functions that mcc_dsl.groovy
#   places calls to in the generated jobs to perform operations on a slave.
#   A function either takes inputs and/or uses environment variables.  Each
#   routine specified in this file outputs its input parameters on entry so
#   that if any problems are encountered it hopefully should be easy to debug
#   them.
#
#   To debug functions in this script, Go to the end of the file and modify
#   the debuggingScript variable.   Setting debuggingScript to 1 turns on
#   function logging, Setting debuggingScript to 0 turns off logging.
#
#   IF YOU MAKE A CHANGE TO THIS SCRIPT, BE SURE TO UPDATE THE VERSION NUMBER
#   IN FUNCTION GetMcxDslHelperFunctionsVersion
#
#    Created by MJC 4/1/2016
#
###############################################################################




###############################################################################
#
#   GetMcxDslHelperFunctionsVersion - Returns version number of helper file
#
###############################################################################
GetMcxDslHelperFunctionsVersion() {
    echo ""
    echo ""
    echo ""
    echo ""
    echo "*********************************************************"
    echo "*                                                       *"
    echo "****Version 1.7.99 of McxDslHelperFunctionsVersion.sh ***"
    echo "*                                                       *"
    echo "*********************************************************"
    echo ""
    echo ""
    echo ""
    echo ""
}

###############################################################################
#
#   ConstructAutomatosImageDirectoryName - this subroutine creates a unique
#       directory name that is used to put the binary and possibly bullseye
#       coverage file into for the test to run.
#
#
#   INPUTS:
#       None
#
###############################################################################
function ConstructAutomatosImageDirectoryName() {
    if [ "$debuggingAutomatos" == '1' ]; then
        set -x
    fi

    echo "****Entering ConstructAutomatosImageDirectoryName"
    echo "AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX:$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX"

    thisDate=$(date +%Y%m%d_%H%M%S)
    echo AUTOMATOS_IMAGE_DIR=$(echo $AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX$thisDate) > aidName.properties
    echo "Output aidName.properties"
    cat aidName.properties

    echo "****Exiting ConstructAutomatosImageDirectoryName"

    if [ "$debuggingAutomatos" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   CopyImageForAutomatosRun - this subroutine is copy the OS binary to the
#       a directory on c4shares that the automatos job can get to in or
#       to run automatos tests
#
#
#   This should be used for Nightly image builds.
#
#   INPUTS:
#       None.
###############################################################################
CopyImageForAutomatosRun() {
    if [ "$debuggingAutomatos" == '1' ]; then
        set -x
    fi

    echo "****Entering CopyImageForAutomatosRun: LocalFilePath:$LOCAL_FILE_PATH Artifact:$ARTIFACT_NAME Directory:$AUTOMATOS_IMAGE_DIR"
    echo "AUTOMATOS_TEST_IMAGE_DIRECTORY:$AUTOMATOS_TEST_IMAGE_DIRECTORY"
    echo "AUTOMATOS_IMAGE_DIR:$AUTOMATOS_IMAGE_DIR"
    echo "AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX:$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX"
    echo "AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY:$AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY"

    # create the directories if they don't already exist.
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/OffArraySanity
    
    #create the directory that will hold the automatos test run results
    mkdir $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY
    
    #
    #  Delete any binary file older than 1 day
    #
    # Explanation
    #
    #    The first argument is the path to the files. This can be a path, a directory, or a wildcard as in the example above.
    #       I would recommend using the full path, and make sure that you run the command without the exec rm to make sure you are
    #       getting the right results.
    #    The second argument, -mtime, is used to specify the number of days old that the file is. If you enter +5, it will find
    #       files older than 5 days.
    #    The third argument, -exec, allows you to pass in a command such as rm. The {} \; at the end is required to end the command.
    find  $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX/* -ctime 1 -exec rm -Rfi {} \;

    #  Need to get the image to a place where the automatos job can get to it.  We will copy it
    #  a well known directory on c4share.
    echo "copying $LOCAL_FILE_PATH to $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$ARTIFACT_NAME"
    scp $LOCAL_FILE_PATH $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$ARTIFACT_NAME

    # Copy the MLU OffArraySanity test directory from the workspace to the image directory so that it can be used for a
    # MLU Sanity run if necessary
    scp $WORKSPACE/safe/catmerge/layered/MLU/test/Sanity/OffArraySanity/* $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/OffArraySanity/

    echo "****Exiting CopyImageForAutomatosRun: Path:$LOCAL_FILE_PATH"

    if [ "$debuggingAutomatos" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   SetupBullseyeResultsDirectoryForRun - this subroutine sets up the unique
#    directory to be used by automatos when copying the bullseye coverage
#    files from the array to the host.  
#
#
#   This should be used for Nightly image builds.
#
#   INPUTS:
#      $1 - AUTOX_TESTSET
#      $2 - Stream
###############################################################################
SetupBullseyeResultsDirectoryForRun() {

    if [ "$debuggingAutomatos" == '1' ]; then
        set -x
    fi

    echo "Entering SetupBullseyeResultsDirectoryForRun: TestSet:$1 Stream:$2 WORKSPACE:$WORKSPACE"
    
    # this is a bullseye run, so we need to set up a unique location for Automatos
    # to put our bullseye information so that it does not get overwritten by some other
    # job running the same automatos test set.
    thisDate=$(date +%Y%m%d_%H%M%S)
    mkdir $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY/$2
    mkdir $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY/$2/$1
    mkdir $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY/$2/$1/$thisDate
    echo AUTOMATOS_BULLSEYE_RUN_PATH=$(echo $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY/$2/$1/$thisDate) > $WORKSPACE/abrPath.properties
    echo "Output abrPath.properties"
    cat $WORKSPACE/abrPath.properties
    echo AUTOMATOS_BULLSEYE_SCP_CONFIGURE_PATH=$(echo $AUTOMATOS_BULLSEYE_SCP_CONFIGURE_PATH_BASE/$2/$1/$thisDate) > $WORKSPACE/abrscpPath.properties
    echo "Output abrscpPath.properties"
    cat $WORKSPACE/abrscpPath.properties

    echo "Exiting SetupBullseyeResultsDirectoryForRun: TestSet:$1 Stream:$2"
    
    if [ "$debuggingAutomatos" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   CopyEMSDImageForAutomatosRun - this subroutine is copy the OS binary to the
#       a directory on c4shares that the automatos job can get to in or
#       to run automatos tests
#
#
#   This should be used for Nightly image builds.
#
#   INPUTS:
#       $1 - EMSD link to artifact
#       $2 - Bullseye run, 1 = true, 0 = false
#       $3 - AUTOX_TESTSET
#       $4 - Stream
#       $5 - Upgrade URL 
#
###############################################################################
CopyEMSDImageForAutomatosRun() {
    if [ "$debuggingAutomatos" == '1' ]; then
        set -x
    fi

    echo "****Entering CopyEMSDImageForAutomatosRun: Directory:$AUTOMATOS_IMAGE_DIR"
    echo "AUTOMATOS_TEST_IMAGE_DIRECTORY:$AUTOMATOS_TEST_IMAGE_DIRECTORY"
    echo "AUTOMATOS_IMAGE_DIR:$AUTOMATOS_IMAGE_DIR"
    echo "AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX:$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX"
    echo "AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY:$AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY"
    echo "EMSD artifact link:$1"
    echo "Stream:$STREAM"
    echo "Bullseye Image:$2"
    echo "AUTOX_TESTSET:$3"
    echo "Stream:$4"
    echo "Upgrade artifact link:$5"
    
    # create the directories if they don't already exist.
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR
    mkdir $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/OffArraySanity
    
    #create the directory that will hold the automatos test run results
    mkdir $AUTOMATOS_BULLSEYE_RESULTS_DIRECTORY
    
    # If this is a bullseye run then we need to create a d
    if [ "$2" == "true" ]; then
        echo "Calling SetupBullseyeResultsDirectoryForRun"
        $SS_LOCATION/McxDslHelperFunctions.sh SetupBullseyeResultsDirectoryForRun $AUTOX_TESTSET $STREAM
    fi
    
    #
    #  Delete any binary file older than 1 day
    #
    # Explanation
    #
    #    The first argument is the path to the files. This can be a path, a directory, or a wildcard as in the example above.
    #       I would recommend using the full path, and make sure that you run the command without the exec rm to make sure you are
    #       getting the right results.
    #    The second argument, -mtime, is used to specify the number of days old that the file is. If you enter +5, it will find
    #       files older than 5 days.
    #    The third argument, -exec, allows you to pass in a command such as rm. The {} \; at the end is required to end the command.
    echo "find $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX_*/* -maxdepth 4 -type f -mtime +1 -delete" 
    find $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX_*/* -maxdepth 4 -type f -mtime +1 -delete 
    echo "find $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX_*/* -maxdepth 4 -type d -mtime +1 -exec rm -rf  {} \;" 
    find $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX_*/* -maxdepth 4 -type d -mtime +1 -exec rm -rfdv  {} \;

    # Use curl to retrieve the artifact from the EMSD server.
    $SS_LOCATION/McxDslHelperFunctions.sh RetrieveBuildArtifacts $1
    artifactName=$(basename "$1")
    echo ARTIFACT_NAME=$(echo $artifactName) > artifactName.properties
    echo "Output artifactName.properties"
    cat artifactName.properties
    
    #  Need to get the image to a place where the automatos job can get to it.  We will copy it
    #  a well known directory on c4share.
    echo "copying $artifactName to $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$artifactName"
    scp $artifactName $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$artifactName
    chmod +x $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$artifactName
    
    if [ "$5" != "" ]; then
        # Use curl to retrieve the artifact from the EMSD server.
        $SS_LOCATION/McxDslHelperFunctions.sh RetrieveBuildArtifacts $5
        upgartifactName=$(basename "$5")
        echo UPGRADE_ARTIFACT_NAME=$(echo $upgartifactName) > upgartifactName.properties
        echo "Output upgartifactName.properties"
        cat upgartifactName.properties
        
        #  Need to get the image to a place where the automatos job can get to it.  We will copy it
        #  a well known directory on c4share.
        echo "copying $upgartifactName to $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$upgartifactName"
        scp $upgartifactName $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$upgartifactName
        chmod +x $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/$upgartifactName
        
    fi

    # Copy the MLU OffArraySanity test directory from the workspace to the image directory so that it can be used for a
    # MLU Sanity run if necessary
    scp $WORKSPACE/safe/catmerge/layered/MLU/test/Sanity/OffArraySanity/* $AUTOMATOS_TEST_IMAGE_DIRECTORY/$AUTOMATOS_IMAGE_DIR/OffArraySanity/

    echo "****Exiting CopyEMSDImageForAutomatosRun: Path:$1"

    if [ "$debuggingAutomatos" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   ProcessAutomatosBullseyeInformation - this subroutine is called process the 
#   coverage file returned from an Automatos run on a bullseye image
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#     Relies on the setting of the $WORKSPACE environment variable
#
#   INPUTS:
#       None:
#
###############################################################################
ProcessAutomatosBullseyeInformation() {
    if [ "$debuggingAutomatos" == '1' ]; then
        set -x
    fi

    echo "****Entering ProcessAutomatosBullseyeInformation: AUTOMATOS_JOB_RESULT_LOCATION:$AUTOMATOS_JOB_RESULT_LOCATION AUTOX_TESTSET:$AUTOX_TESTSET"
    echo "AUTOMATOS_ARTIFACTS_LOCATION: $AUTOMATOS_ARTIFACTS_LOCATION"
    echo "AUTOMATOS_IMAGE_DIR: $AUTOMATOS_IMAGE_DIR"
    echo "AUTOMATOS_BULLSEYE_RUN_PATH: $AUTOMATOS_BULLSEYE_RUN_PATH"
    echo "AUTOMATOS_CONFIGURATION_TESTNAME: $AUTOMATOS_CONFIGURATION_TESTNAME"
    
    echo "Running bullshtml on $AUTOMATOS_JOB_RESULT_LOCATION/$AUTOX_TESTSET.cov"
    declare -x PATH=/opt/BullseyeCoverage/bin:$PATH 

    # if we have the bullseye data we need to first run covmerge on the coverage files from SPA and SPB.
    echo "dir of $AUTOMATOS_JOB_RESULT_LOCATION to show the files we will process." 
    ls -lR $AUTOMATOS_JOB_RESULT_LOCATION
    
    echo "dir of $AUTOMATOS_BULLSYE_RUN_PATH to show the files we will process." 
    ls -lR $AUTOMATOS_BULLSEYE_RUN_PATH
    
    if [ ! -e '/BullseyeLicense' ]; then
        sudo mkdir /BullseyeLicense
    fi
    if mount | grep /BullseyeLicense > /dev/null; then
        sudo umount /BullseyeLicense
    fi
    sudo mount -o nfsvers=3 bullseye-lic1.usd.lab.emc.com:/BullseyeLicense /BullseyeLicense
    
    mkdir $WORKSPACE/$AUTOX_TESTSET/
    mkdir $WORKSPACE/BULLSEYE_HTML
    
    covmerge -c -f$AUTOMATOS_JOB_RESULT_LOCATION/$AUTOX_TESTSET.cov $AUTOMATOS_BULLSEYE_RUN_PATH/$AUTOX_TESTSET/*.cov
    covhtml --file $AUTOMATOS_JOB_RESULT_LOCATION/$AUTOX_TESTSET.cov --srcdir $WORKSPACE $WORKSPACE/BULLSEYE_HTML
    
    $BULLS_LOCATION/bullshtml -f $AUTOMATOS_JOB_RESULT_LOCATION/$AUTOX_TESTSET.cov $WORKSPACE/BULLSEYE_HTML
    
    if [ "$DOING_TRIM" == "1" ]; then
        echo "Doing Trim of clover.xml"
        cp $WORKINGPATH/safe/BULLSEYE_HTML/clover.xml $WORKINGPATH/safe/BULLSEYE_HTML/original_clover.xml
        $SS_LOCATION/TrimClover.pl -xmlfilename $WORKINGPATH/safe/BULLSEYE_HTML/original_clover.xml -outputfn $WORKINGPATH/safe/BULLSEYE_HTML/clover.xml -testsuite $AUTOMATOS_CONFIGURATION_TESTNAME
    fi
    
    echo "Running covsrc to generate CSV file for later analysis."
    declare -x PATH=/opt/BullseyeCoverage/bin:$PATH 
    covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager        
    /opt/BullseyeCoverage/bin/covsrc -d $WORKSPACE -f $AUTOMATOS_JOB_RESULT_LOCATION/$AUTOX_TESTSET.cov -c -o $WORKSPACE/BULLSEYE_HTML/test.csv
                        
    echo "Current Directory: $PWD"
    tar --dereference  --hard-dereference -czf artifactory $WORKSPACE/BULLSEYE_HTML
    echo "See if XML is present in $WORKSPACE/BULLSEYE_HTML"
    ls -lr $WORKSPACE/BULLSEYE_HTML/*.xml
    echo "BULLSEYE_HTML files are archived !!!"

    $SS_LOCATION/McxDslHelperFunctions.sh ArchiveBuildArtifacts Automatos/$AUTOMATOS_ARTIFACTS_LOCATION bullseye.tar.gz noimage $WORKSPACE/TestResults.log "$AUTOX_TESTSET"_Bullseye_HTML_Results

    if [ "$debuggingAutomatos" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   ChangeTargetDirectoryOwner - this subroutine is called to remove files
#       in a target directory
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#     Relies on the setting of the $WORKSPACE environment variable
#
#   INPUTS:
#       None:
#
###############################################################################
ChangeTargetDirectoryOwner() {
    if [ "$debuggingWorkspaceCleanup" == '1' ]; then
        set -x
    fi

    exitStatus=0

    
    echo "****Entering ChangeTargetDirectoryOwner: Path:$WORKSPACE"
    
    sudo chown -R c4dev:users $WORKSPACE/*
    sudo chown -R c4dev:users $WORKSPACE/.*
    
    # if we get here do this to mitigate performance issues....
    git status

    echo "****Exiting ChangeTargetDirectoryOwner"
    
    if [ "$debuggingWorkspaceCleanup" == '1' ]; then
        set +x
    fi

   return $exitStatus 
}

###############################################################################
#
#   ChangeTargetDirectoryOwnerNoGit - this subroutine is called to remove files
#       in a target directory
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#     Relies on the setting of the $WORKSPACE environment variable
#
#   INPUTS:
#       None:
#
###############################################################################
ChangeTargetDirectoryOwnerNoGit() {
    if [ "$debuggingWorkspaceCleanup" == '1' ]; then
        set -x
    fi

    exitStatus=0

    
    echo "****Entering ChangeTargetDirectoryOwneNoGit: Path:$WORKSPACE"
    
    sudo chown -R c4dev:users $WORKSPACE/*
    sudo chown -R c4dev:users $WORKSPACE/.*
    

    echo "****Exiting ChangeTargetDirectoryOwnerNoGit"
    
    if [ "$debuggingWorkspaceCleanup" == '1' ]; then
        set +x
    fi

   return $exitStatus 
}

###############################################################################
#
#   MoveFile - this subroutine is called move a file
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - src
#       $2 - destination
#
###############################################################################
MoveFile() {
    if [ "$debuggingImageProcessing" == '1' ]; then
        set -x
    fi
    
    echo "****Entering MoveFile: src:$1 destination:$2"
    
    mv "$1" "$2"

    echo "****Exiting MoveFile"
    if [ "$debuggingImageProcessing" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   CompressTarImage - this subroutine is called compress files to a tar file
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - destination
#       $2 - name of tar file to compress to
#
###############################################################################
CompressTarImage() {
    if [ "$debuggingImageProcessing" == '1' ]; then
        set -x
    fi
    
    for p in "$*";
    do
        echo "[$p]";
    done

    echo "****Entering CompressTarImage: destination:$1 tarfile:$2 $3 $4 $5 $6 $7 $8"
    if [ -e "$1" ]; then
        rm "$1"
    fi
    
    tar --dereference --hard-dereference --exclude='generated' --exclude='*.obj' --exclude='kernel32' --exclude='user' --exclude='user32' -czf  "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8"
    
    echo "Current Directory:$PWD"
    ls -lr "$1"
    
    echo "****Exiting CompressTarImage"
    if [ "$debuggingImageProcessing" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   DecideContentsTarCompressAndArchive - this subroutine is called determine what is going to
#     be zipped up for artifactory
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#
###############################################################################
DecideContentsTarCompressAndArchive() {

    if [ "$debuggingImageProcessing" == '1' ]; then
        set -x
    fi
    
    echo "****Entering DecideContentsTarCompressAndArchive: ISONDEMAND:$ISONDEMAND, BUILDCONFIGURATIONJOBNAME:$BUILDCONFIGURATIONJOBNAME,BUILD_TYPE:$BUILD_TYPE"
    
    if [ '$ISONDEMANDJOB' == '1' ]; then 
        # create a archive 'artifactory' containing safe then transfer it to the artifactory host
        if [[ "$BUILD_TYPE" == "Bullseye" ]] || [[ "$BUILD_TYPE" == "bullseye" ]]; then
            $SS_LOCATION/McxDslHelperFunctions.sh CompressTarImage artifactory $BUILD_TARGET
        else
            $SS_LOCATION/McxDslHelperFunctions.sh CompressTarImage artifactory $BUILD_TARGET/safe/Targets/armada64_*/Simulation/exec
        fi
        $SS_LOCATION/McxDslHelperFunctions.sh ArchiveBuildArtifacts ondemand safe.tar.gz noimage $WORKSPACE/TestResults.log BUILD_ARCHIVE
    else
        # This is not an on demand job, so setup for a nightly build job.
        # Compress the image and then transfer it to the artifactory host
        if [[ "$BUILD_TYPE" == "Bullseye" ]] || [[ "$BUILD_TYPE" == "bullseye" ]]; then
            $SS_LOCATION/McxDslHelperFunctions.sh CompressTarImage artifactory $BUILD_TARGET
        else
            $SS_LOCATION/McxDslHelperFunctions.sh CompressTarImage artifactory $BUILD_TARGET/safe/Targets/armada64_*/Simulation/exec
        fi
        $SS_LOCATION/McxDslHelperFunctions.sh ArchiveBuildArtifacts $BUILDCONFIGURATIONJOBNAME safe.tar.gz noimage $WORKSPACE/TestResults.log BUILD_ARCHIVE
    fi
    
    echo "****Exiting DecideContentsTarCompressAndArchive: ISONDEMAND:$ISONDEMAND, BUILDCONFIGURATIONJOBNAME:$BUILDCONFIGURATIONJOBNAME,BUILD_TYPE:$BUILD_TYPE"    

    if [ "$debuggingImageProcessing" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   ExpandTarImage - this subroutine is called expand a tar file
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - name of tar file to expand
#
###############################################################################
ExpandTarImage() {

    if [ "$debuggingImageProcessing" == '1' ]; then
        set -x
    fi
    
    echo "****Entering ExpandTarImage: tarfile:$1"
    echo "****Entering ExpandTarImage: directory:$PWD"
    tar -xzf "$1"
    ls -lr
    ls -lr safe/
    echo "****Exiting ExpandTarImage"
    
    if [ "$debuggingImageProcessing" == '1' ]; then
        set +x
    fi
}


###############################################################################
#
#   PopulateWorkspace - this subroutine is called populate a workspace
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - if 1, then prepare workspace, if 0 then do not prepare workspace
#
#       We only do --noprepare when we are not going to be building the workspace
#
###############################################################################
PopulateWorkspace() {
    
    if [ "$debuggingWorkspaceProcessing" == '1' ]; then
        set -x
    fi
    
    echo "****Entering PopulateWorkspace STREAM:$STREAM, PREPARE:$1 SCM_TYPE:$SCM_TYPE TRANSACTION_ID:$TRANSACTION_ID*********"

    SOURCE="$STREAM"

    # We need to determine whether or not we are populating a stream or a
    # workspace.  Since we don't know we have to parse the stream name
    # to determine this.  WE ASSUME that stream names start with "upc-" and
    # workspace names do not.
    USERWORKSPACE_BUILD=1
    if [[ $SOURCE =~ .*upc-.* ]]; then
        USERWORKSPACE_BUILD=0
    fi
    
    if [ "$SCM_TYPE" == "accurev" ]; then
        echo "Populating Accurev Workspace...Pop with Overwrite USERWORKSPACE_BUILD:$USERWORKSPACE_BUILD"
    
        if [ "$USERWORKSPACE_BUILD" == '1' ]; then
            if [ "$1" == '1' ]; then
                if [ "$TRANSACTION_ID" == "" ]; then
                    ws pop --prepare --name=$SOURCE --path=.
                else
                    ws pop --prepare --name=$SOURCE --path=. --transaction=$TRANSACTION_ID
                fi
            else
                ws pop --noprepare --name=$SOURCE --path=.
            fi 
        else
            if [ "$1" == '1' ]; then
                ws pop --stream=$SOURCE --head --prepare --path=. kittyhawk-all
            else
                ws pop --stream=$SOURCE --head  --noprepare --path=. kittyhawk-all
            fi
        fi
    else
        echo "Populating GitHub Workspace...Pop with Overwrite USERWORKSPACE_BUILD:$USERWORKSPACE_BUILD"
        $SS_LOCATION/McxDslHelperFunctions.sh PopulateGitHubWorkspace
        if [ $? == 0 ]; then
            # We have successfully populated the workspace.  Now we need to set up the tracking branch
            version="$(date +%m%d%Y%H%M%S)" 
            echo "doing git checkout -B unity-file/file_$version"
            git checkout -B "unity-file/file-$version"
            if [ $? == 0 ]; then
                echo "doing git branch --set-upstream-to=origin/$BRANCH"
                git branch --set-upstream-to="origin/$BRANCH"
            fi
        fi
    fi 
    exitStatus=$?;
    
    echo "Workspace populated !!!"

    echo "****Exiting PopulateWorkspace   exitStatus:$exitStatus"
    if [ "$debuggingWorkspaceProcessing" == '1' ]; then
        set +x
    fi
    
    return $exitStatus;
}

###############################################################################
#
#   GetBullseyeVersion - this subroutine is called to retrieve the bullseye
#       version being used.
#
#
#   This should be used for Bullseye builds
#
#   INPUTS:
#
###############################################################################
GetBullseyeVersion() {

    if [ "$debuggingScript" == '1' ]; then
        set -x
    fi
    
    echo "****Entering GetBullseyeVersion"

    sudo chown c4dev:users safe/Targets/armada64_*/simulation/exec -R 2>/dev/null
    ls | grep -E -v 'Version\.xml|bullshtml\.exe' | xargs rm -rf

    echo "****Exiting GetBullseyeVersion"
    
    if [ "$debuggingScript" == '1' ]; then
        set +x
    fi

}

###############################################################################
#
#   SetupLinuxBuildOrTestEnvironment - this subroutine is used to set up the
#       Linux environment for building or testing.
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#
###############################################################################
SetupLinuxBuildOrTestEnvironment() {

    if [ "$debuggingWorkspaceProcessing" == '1' ]; then
        set -x
    fi
    
    echo "****Entering SetupLinuxBuildOrTestEnvironment"

    # No longer doing c4dev_update automatically we do it once a day 
    # in the Server Client Reboot Job with the -reboot option
    #sudo c4dev_update
    #gosp2 -- --- -c "sudo c4dev_update"
    #gosp3 -- --- -c "sudo c4dev_update"
    #go12 -- --- -c "sudo c4dev_update"
    #go12sp1 -- --- -c "sudo c4dev_update"

    echo "****Entering SetupLinuxBuildOrTestEnvironment"
    if [ "$debuggingWorkspaceProcessing" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   RetrieveBuildArtifacts - this subroutine is used to retrieve the results
#                       to the artificatory host
#
#
#   This should be used for Nightly and OnDemand builds.
#
#   INPUTS:
#       $1 - Artifact to retrieve
#
###############################################################################
RetrieveBuildArtifacts() {
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set -x
    fi
    
    exitStatus=0
    
    echo "****Entering RetrieveBuildArtifacts artifact_to_retrieve:$1"
    
    targetFile="$1"
    RETRIEVE_REPO='https://arhost3.usd.lab.emc.com/artifactory/EMSD_MCC_TEST/'
    fileName="$(basename "$targetFile")"
    
    #    if case "$targetFile" in "$RETRIEVE_REPO"*) true;; *) false;; esac; then
      echo "Fetching $fileName"
      curl -k -o "$fileName" -X GET \
       -u "$ARTIFACTORY_READER_USER:$ARTIFACTORY_READER_PASSWORD" \
       -L "$targetFile"
    #else
      #  echo "You must provide a link to the MCC repository."
      #exit 1
    #fi
    exitStatus=$?
    
    echo "****Exiting RetrieveBuildArtifacts ExitStatus: $exitStatus"
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
}

###############################################################################
#
#   GetDTString - this subroutine is used create a string that has the current
#           Date and time in a format that can be used as a directory name.
#
#
#   This should be used for Nightly and OnDemand builds.
#
#   INPUTS:
#       None.
#
###############################################################################
GetDTString()
{
    echo "****Entering GetDTString"
    VERSION="$(date +%m%d%Y%H%M%S)" 
    echo TODAY_ARCHIVE_VERSION_NAME=$(echo $VERSION) > version_name.properties
    echo "****Exiting GetDTString VERSION: $VERSION"
}

###############################################################################
#
#   ArchiveBuildArtifacts - this subroutine is used to move the results of a test run
#                      to the artifactory host
#
#
#   This should be used for Nightly and OnDemand builds.
#
#   INPUTS:
#       $1 path - directory path of where to put artifact on artifactory host
#       $2 artifact name - name of artifact to store
#       $3 if not "noimage" we are archiving a individual file and want to
#          send it to a special directory (images)
#       $4 Results file location
#       $5 title
#
###############################################################################
ArchiveBuildArtifacts() {
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set -x
    fi
    
    exitStatus=0
    
    echo "****Entering ArchiveBuildArtifacts path:$1 artifact_name:$2 artifact:$3 Results:$4 Title: $5"
    ARCHIVE_REPO='https://arhost3.usd.lab.emc.com/artifactory/EMSD_MCC_TEST'
    VERSION="$(date +%m%d%Y%H%M%S)" 
    if [ -n "$BUILD_USER_ID" ]; then
        VERSION="$VERSION-$BUILD_USER_ID"
    fi
    REMOTE_FILE_PATH="$1/$VERSION"
    ARTIFACT_NAME="$2"
    LOCAL_FILE_PATH="artifactory"
    # See if the 3 parameters is noimage, if it is, then we are trying to send a already created file called artifactory
    # to the artifactory host as what ever was specified in $2
    if [ "$3" != "noimage" ]; then
        xtmp=$(ls -x $3)
        echo "File to archive $xtmp found with string $3"
        LOCAL_FILE_PATH="$xtmp"
        # output the full pathname of the image to the artifact_fullname properties file so that the caller
        # can use it if it needs it.
        echo LOCAL_FILE_PATH=$(echo $LOCAL_FILE_PATH) > artifact_fullname.properties
        ARTIFACT_NAME="$(basename $xtmp)"
        # output the name of the image to the artifact_name properties file so that the caller
        # can use it if it needs it.
        echo ARTIFACT_NAME=$(echo $ARTIFACT_NAME) > artifact_name.properties
        REMOTE_FILE_PATH="$1/$VERSION"
    fi
    
    which md5sum > /dev/null || exit $?
    which sha1sum > /dev/null || exit $?
    
    MD5_VALUE="$(md5sum "$LOCAL_FILE_PATH")"
    MD5_VALUE="${MD5_VALUE:0:32}"
    SHA1_VALUE="$(sha1sum "$LOCAL_FILE_PATH")"
    SHA1_VALUE="${SHA1_VALUE:0:40}"
    
    echo "INFO: Uploading $LOCAL_FILE_PATH to $REMOTE_FILE_PATH/$ARTIFACT_NAME"
    curl -k -i --retry 30 --retry-delay 10 -X PUT \
     -u "$ARTIFACTORY_DEPLOYER_USER:$ARTIFACTORY_DEPLOYER_PASSWORD" \
     -H "X-Checksum-Md5: $MD5_VALUE" \
     -H "X-Checksum-Sha1: $SHA1_VALUE" \
     -T "$LOCAL_FILE_PATH" \
     "$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" > artifactoryurl.txt
     
    exitStatus=$?
    
    echo "Current execution path"
    echo "$PWD"
    cat artifactoryurl.txt
    cat artifactoryurl.txt | (grep 'uri' | sed -e 's#^[ ]*"uri"[ ]*:[ ]*"\(.*\)"$#ARTIFACTS_URL=\1#' -e 's#http:#https:#' > artifactoryUrl.properties)
    echo "Output $WORKSPACE/artifactoryUrl.properties"
    cat artifactoryUrl.properties
    rm artifactoryurl.txt
    
    echo TESTLOG=$(echo $ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME) > testLogUrl.properties
    echo "Output testlogUrl.properties"
    cat testLogUrl.properties
    

    # echo the title and the link into the input results file.   At the completion
    # of the job this will all be rolled into the completion email.
	echo "$5,$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" >> $4
    echo "Contents of $4"
    cat  $4
    
    echo "Current Directory contents"
    ls
    
    echo "****Exiting ArchiveBuildArtifacts ExitStatus: $exitStatus"
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
}

###############################################################################
#
#   ArchiveImageArtifact - this subroutine is used to move a image to the
#       artifactory host.
#
#
#   This should be used for Nightly.
#
#   INPUTS:
#       $1 path - directory path of where to put artifact on artifactory host
#       $2 artifact name - name of artifact to store
#       $3 individual file to send a special directory (images)
#       $4 versionInfo (to make directory name unique)
#       $5 Results file location
#       $6 title
#
###############################################################################
ArchiveImageArtifact() {
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set -x
    fi
    
    exitStatus=0
    
    echo "****Entering ArchiveImageArtifact path:$1 artifact_name:$2 artifact:$3 version:$4 Results:$5 Title: $6"
    ARCHIVE_REPO='https://arhost3.usd.lab.emc.com/artifactory/EMSD_MCC_TEST'
    VERSION="$4" 
    if [ -n "$BUILD_USER_ID" ]; then
        VERSION="$VERSION-$BUILD_USER_ID"
    fi
    REMOTE_FILE_PATH="$1/$VERSION"
    ARTIFACT_NAME="$2"
    xtmp=$(ls -x $3)
    echo "File to archive $xtmp found with string $3"
    LOCAL_FILE_PATH="$xtmp"
    # output the full pathname of the image to the artifact_fullname properties file so that the caller
    # can use it if it needs it.
    echo LOCAL_FILE_PATH=$(echo $LOCAL_FILE_PATH) > artifact_fullname.properties
    ARTIFACT_NAME="$(basename $xtmp)"
    # output the name of the image to the artifact_name properties file so that the caller
    # can use it if it needs it.
    echo ARTIFACT_NAME=$(echo $ARTIFACT_NAME) > artifact_name.properties
    REMOTE_FILE_PATH="$1/$VERSION"
    
    which md5sum > /dev/null || exit $?
    which sha1sum > /dev/null || exit $?
    
    MD5_VALUE="$(md5sum "$LOCAL_FILE_PATH")"
    MD5_VALUE="${MD5_VALUE:0:32}"
    SHA1_VALUE="$(sha1sum "$LOCAL_FILE_PATH")"
    SHA1_VALUE="${SHA1_VALUE:0:40}"
    
    echo "INFO: Uploading $LOCAL_FILE_PATH to $REMOTE_FILE_PATH/$ARTIFACT_NAME"
    curl -k -i --retry 30 --retry-delay 10 -X PUT \
     -u "$ARTIFACTORY_DEPLOYER_USER:$ARTIFACTORY_DEPLOYER_PASSWORD" \
     -H "X-Checksum-Md5: $MD5_VALUE" \
     -H "X-Checksum-Sha1: $SHA1_VALUE" \
     -T "$LOCAL_FILE_PATH" \
     "$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" > artifactoryurl.txt
     
    exitStatus=$?
    
    echo "Current execution path"
    echo "$PWD"
    cat artifactoryurl.txt
    cat artifactoryurl.txt | (grep 'uri' | sed -e 's#^[ ]*"uri"[ ]*:[ ]*"\(.*\)"$#ARTIFACTS_URL=\1#' -e 's#http:#https:#' > artifactoryUrl.properties)
    echo "Output $WORKSPACE/artifactoryUrl.properties"
    cat artifactoryUrl.properties
    rm artifactoryurl.txt
    
    echo TESTLOG=$(echo $ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME) > testLogUrl.properties
    echo "Output testlogUrl.properties"
    cat testLogUrl.properties
    

    # echo the title and the link into the input results file.   At the completion
    # of the job this will all be rolled into the completion email.
    echo "$6,$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" >> $5
    echo "Contents of $5"
    cat  $5
    
    echo "Current Directory contents"
    ls
    
    echo "****Exiting ArchiveImageArtifact ExitStatus: $exitStatus"
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
}

###############################################################################
#
#   ArchiveArtifactoryArtifact - this subroutine is used to move the artifactory
#                      file to the artifactory host
#
#
#   This should be used for Nightly and OnDemand builds.
#
#   INPUTS:
#       $1 path - directory path of where to put artifact on artifactory host
#       $2 artifact name - name of artifact to store
#       $3 version
#       $4 Results file location
#       $5 title
#
###############################################################################
ArchiveArtifactoryArtifact() {
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set -x
    fi
    
    exitStatus=0
    
    echo "****Entering ArchiveArtifactoryArtifact path:$1 artifact_name:$2 version:$3 Results:$4 Title: $5"
    ARCHIVE_REPO='https://arhost3.usd.lab.emc.com/artifactory/EMSD_MCC_TEST'
    VERSION="$3" 
    if [ -n "$BUILD_USER_ID" ]; then
        VERSION="$VERSION-$BUILD_USER_ID"
    fi
    REMOTE_FILE_PATH="$1/$VERSION"
    ARTIFACT_NAME="$2"
    LOCAL_FILE_PATH="artifactory"
    
    which md5sum > /dev/null || exit $?
    which sha1sum > /dev/null || exit $?
    
    MD5_VALUE="$(md5sum "$LOCAL_FILE_PATH")"
    MD5_VALUE="${MD5_VALUE:0:32}"
    SHA1_VALUE="$(sha1sum "$LOCAL_FILE_PATH")"
    SHA1_VALUE="${SHA1_VALUE:0:40}"
    
    echo "INFO: Uploading $LOCAL_FILE_PATH to $REMOTE_FILE_PATH/$ARTIFACT_NAME"
    curl -k -i --retry 30 --retry-delay 10 -X PUT \
     -u "$ARTIFACTORY_DEPLOYER_USER:$ARTIFACTORY_DEPLOYER_PASSWORD" \
     -H "X-Checksum-Md5: $MD5_VALUE" \
     -H "X-Checksum-Sha1: $SHA1_VALUE" \
     -T "$LOCAL_FILE_PATH" \
     "$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" > artifactoryurl.txt
     
    exitStatus=$?
    
    echo "Current execution path"
    echo "$PWD"
    cat artifactoryurl.txt
    cat artifactoryurl.txt | (grep 'uri' | sed -e 's#^[ ]*"uri"[ ]*:[ ]*"\(.*\)"$#ARTIFACTS_URL=\1#' -e 's#http:#https:#' > artifactoryUrl.properties)
    echo "Output $WORKSPACE/artifactoryUrl.properties"
    cat artifactoryUrl.properties
    rm artifactoryurl.txt
    
    echo TESTLOG=$(echo $ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME) > testLogUrl.properties
    echo "Output testlogUrl.properties"
    cat testLogUrl.properties
    

    # echo the title and the link into the input results file.   At the completion
    # of the job this will all be rolled into the completion email.
    echo "$5,$ARCHIVE_REPO/$REMOTE_FILE_PATH/$ARTIFACT_NAME" >> $4
    echo "Contents of $4"
    cat  $4
    
    echo "Current Directory contents"
    ls
    
    echo "****Exiting ArchiveArtifactoryArtifact ExitStatus: $exitStatus"
    if [ "$debuggingArchiveProcessing" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
}

###############################################################################
#
#   GetEMSD_MCC_TESTStorageInfo - this subroutine is called to get storage info
#   From the artifactory host
#
#
#   This is called periodically by the artifactory host cleanup job.
#
#   INPUTS:
#       $1 - file 
#
###############################################################################
function GetEMSD_MCC_TESTStorageInfo() {

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set -x
    fi
    
    echo "****Entering GetEMSD_MCC_TESTStorageInfo ResultsFilePath: NOT IMPLEMENTED"
    
    temp_file=$(mktemp)
    
    curl -k -i -L -f -X GET -u "$ARTIFACTORY_DELETE_USER:$ARTIFACTORY_DELETE_PASSWORD" "https://arhost3.usd.lab.emc.com/api/storageinfo/EMSD_MCC_TEST" > $temp_file
    
    # cat $temp_file
    
    rm $temp_file
    
    echo "****Exiting GetEMSD_MCC_TESTStorageInfo"
    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set +x
    fi
}


###############################################################################
#
#   PerformBuild - this subroutine when called does the specified type of build
#
#
#   This should be used for Nightly, Bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - name of target build.  Either "" or "Bullseye"
#       $2 - "true" if image build, "false" otherwise
#       $3 - "true" mcc tests to be run
#       $4 - "true" mcr tests to be run
#       $5 - "true" mlu tests to be run
#       $6 - "true" file tests to be run
#       $7 - "true" ufs64 tests to be run
#
#       parameters 3 thru 7 are only important if this is a Bullseye run 
#       this helps us select the exclusions file to use.
#
###############################################################################
PerformBuild() {
    if [ "$debuggingScript" == '1' ]; then
        set -x
    fi
    echo "****Entering PerformBuild: Type:$BUILD_TYPE Target:$BUILD_TARGET BuildingImage:$2 mcc:$3 mcr:$4 mlu:$5 file:$6 ufs64:$7"
    echo "Current Workspace: $WORKSPACE"

    echo "****Setup bash trap Workspace: $WORKSPACE ****"
    trap ChangeTargetDirectoryOwner ERR
    
    exitStatus=0
    if [[ "$BUILD_TYPE" == 'Release' ]] || [[ "$BUILD_TYPE" == 'release' ]]; then
        BUILD_FLAVOR='RETAIL'
    else
        # This will be set as the default whether the BUILD_TYPE is Bullseye or Debug.
        BUILD_FLAVOR='DEBUG'
    fi
    
    if [[ "$BUILD_TYPE" == 'Bullseye' ]] || [[ "$BUILD_TYPE" == 'bullseye' ]]; then
        # set up information needed to perform the bullseye build.
        if [ ! -e '/BullseyeLicense' ]; then
            sudo mkdir /BullseyeLicense
        fi
        if mount | grep /BullseyeLicense > /dev/null; then
            sudo umount /BullseyeLicense
        fi
        sudo mount -o nfsvers=3 bullseye-lic1.usd.lab.emc.com:/BullseyeLicense /BullseyeLicense

        echo "Current execution path"
        echo "$PWD"
        # Set the working path for the sudo environment
        sudo bash -c "declare -x WORKINGPATH=$PWD"
        # set the working path for the non-sudo environment
        declare -x WORKINGPATH=$PWD
        echo "sudo execution path"
        sudo bash -c "echo $PWD"
        echo "non-sudo execution path"
        echo "$PWD"
        export CFG_BULLSEYE_LICENSE_DIR=/net/bullseye-lic1.usd.lab.emc.com/BullseyeLicense
    fi
    
    # We have to support falcon streams and the build system
    # has issues where it does not do a covlmgr for those streams
    # Therefore we will look to see if we have to do it....
    grep -Fxq ARTIFACTORY_RPMLIST build/content_tags
    needToDoCovCall=$?
   
    echo "Current execution path: $PWD"
    ls -lr
    
    if [ -e './build/build_flag' ]; then
      #If the distribution for a build target is present under ./build
      DISTRIBUTION=$(./build/build_flag -t GNOSIS C4_CFG_DISTRIBUTION)
    else
     if [ -d 'targets/products' ]; then
      #If the distribution for a build target is present under /targets/products
      DISTRIBUTION=$(grep DISTRIBUTION targets/products/GNOSIS --no-filename | sed -n 's#C4_CFG_DISTRIBUTION=\(.*\)#\1#p')
     else
      DISTRIBUTION=$(grep SLES targets/tags/KHPLATFORM | sed -n 's#addtag \(.*\)#\1#p')
     fi
    fi
    
    # Default the build environment to the old style that used gosp by defaulting newbuildEnv to 0.
    # if it is set to 1 by some build environment then we will use the new method....
    newbuildEnv=0
    
    if [ "$DISTRIBUTION" == 'SLES11SP2' ]; then
      GOSP='gosp2'
      echo 'setting environment for' $GOSP
    else 
      if [ "$DISTRIBUTION" == 'SLES11SP3' ]; then
        GOSP='gosp3'
        echo 'setting environment for' $GOSP
      else 
        if [ "$DISTRIBUTION" == 'SLES12' ]; then
          GOSP='go12'
          echo 'setting environment for' $GOSP
        else
          if [ "$DISTRIBUTION" == 'SLES12SP1' ]; then
            GOSP='go12sp1'
            echo 'setting environment for' $GOSP
            if [ "$needToDoCovCall" == "0" ]; then
                newbuildEnv=1
            fi
          else
            echo 'Unknown build target'
            exit 1
          fi
        fi
      fi
    fi
    
    echo "Starting build..."
    
    # Setup the placement of the build artifacts.
    CFG_OUTPUT_BASE=/net/${JENKINS_SERVER}/build_artifacts/${JOB_NAME}
    CFG_BUILD_WORKSPACE=build-${BUILD_NUMBER}
    CFG_OUTPUT=${CFG_OUTPUT_BASE}/${CFG_BUILD_WORKSPACE}
    echo "CFG_OUTPUT_BASE:$CFG_OUTPUT_BASE"
    echo "CFG_OUTPUT:$CFG_OUTPUT"
    echo "CFG_BUILD_WORKSPACE:$CFG_BUILD_WORKSPACE"
        
    if [[ "$BUILD_TYPE" == 'Bullseye' ]] || [[ "$BUILD_TYPE" == 'bullseye' ]]; then
        echo "See if common simulation exclusion files exist in stream, if not copy temp versions"

#TODO: MJC override the files in the stream with our version for hardware.
#        if [ ! -e '$WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_HW_BullseyeCoverageExclusions.cfg' ]; then
            cp $SS_LOCATION/BlockDomain_HW_BullseyeCoverageExclusions.cfg $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_HW_BullseyeCoverageExclusions.cfg
#        fi
        
#TODO: MJC override the files in the stream with our version for Simulation.
#        if [ ! -e '$WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg' ]; then
            cp $SS_LOCATION/BlockDomain_SIM_BullseyeCoverageExclusions.cfg $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg
#        fi

        # look at the second parameter to determine if we are doing an image build or a normal build
        if [ "$2" == 'true' ]; then
            # image build, use the hardware configuration
            echo "Using Hardware exclusions file with Bullseye"
            cat $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_HW_BullseyeCoverageExclusions.cfg >> $WORKSPACE/build/BullseyeCoverageExclusions
            
            # copy the the appended file over our file so that later when we generate the report we are using the same exclusions file
            cp $WORKSPACE/build/BullseyeCoverageExclusions $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_HW_BullseyeCoverageExclusions.cfg
#            echo "Start of Bullseye Exclusions being used"
#            cat $WORKSPACE/build/BullseyeCoverageExclusions
#            echo "End of Bullseye Exclusions being used"

            # Do the build_all in the correct environment.
            if [ $newbuildEnv == 0 ]; then
                "$GOSP" -- /BullseyeLicense --- -c "/opt/BullseyeCoverage/bin/covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager; cd '$WORKSPACE'; CFG_HEALTH_CHECK=0; build_all -t GNOSIS --no-check-buildenv  --no-incremental -f BULLSEYE -c $BUILD_TARGET"
            else
                cd $WORKSPACE
                CFG_HEALTH_CHECK=0
                build_all -t GNOSIS --no-check-buildenv --no-incremental -f BULLSEYE -c $BUILD_TARGET
            fi
            exitStatus=$?
            echo "Completing Bullseye Hardware Build"
        else
            # non-image build use the simulation configuration
            echo "Using Simulation exclusions file with Bullseye"
            # Mcr, Mcc, and Mlu, now all use the same common coverage file in simulation. Therefore the can all be build with the same command line.
            echo "Performing Bullseye Mcr,Mcc,Mlu Build"
            cat safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg >> build/BullseyeCoverageExclusions
            
            # copy the the appended file over our file so that later when we generate the report we are using the same exclusions file
            cp $WORKSPACE/build/BullseyeCoverageExclusions $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg
            
#            echo "Start of Bullseye Exclusions being used"
#            cat $WORKSPACE/build/BullseyeCoverageExclusions
#            echo "End of Bullseye Exclusions being used"

            # Do the build_all in the correct environment
            if [ $newbuildEnv == 0 ]; then
                "$GOSP" -- /BullseyeLicense --- -c "/opt/BullseyeCoverage/bin/covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager; cd '$WORKSPACE'; CFG_HEALTH_CHECK=0; build_all -t GNOSIS --no-check-buildenv --no-incremental -f BULLSEYE -c $BUILD_TARGET"
            else
                cd $WORKSPACE
                CFG_HEALTH_CHECK=0
                build_all -t GNOSIS --no-check-buildenv --no-incremental -f BULLSEYE -c $BUILD_TARGET
            fi
            exitStatus=$?
            set +x
            echo "Completing Bullseye off-array Build"
        fi
        echo "list output directory"
        ls "$WORKINGPATH"/output
        # if this is not an image build, then need to move the coverage file to the target directory
        if [ "$2" != 'true' ]; then
            echo "list target directory"
            ls "$WORKINGPATH"/safe/Targets
            echo "Copying bullseye_test.cov to test.cov..."
            sudo cp "$WORKINGPATH"/output/bullseye_test.cov "$WORKINGPATH"/safe/Targets/armada64_checked/test.cov
            echo "do a directory to see if test.cov was copied"
            ls "$WORKINGPATH"/safe/Targets/armada64_checked/test.cov
            echo "Finished Copying bullseye_test.cov to test.cov..."
        fi
    else
        if [[ "$BUILD_TYPE" == 'Coverity' ]] || [[ "$BUILD_TYPE" == 'coverity' ]]; then
            # the caller has requested a Coverity Build, do it....
            echo $PATH
            PATH=/opt/cov-analysis-linux64-6.0.2/bin:$PATH
            export PATH
            echo $PATH
            
            echo "****Remove bash trap Workspace: $WORKSPACE ****"
            trap 
            
            "$GOSP" -- /CI-build/ /opt/cov-analysis-linux64-6.0.2 --- /bin/bash -c "cd '$WORKSPACE'; /opt/cov-analysis-linux64-6.0.2/bin/cov-build --dir '$WORKSPACE'/coverity build_all -c -t GNOSIS --no-check-buildenv --no-incremental -f $BUILD_FLAVOR $BUILD_TARGET"
            
            sleep 120
            
            /opt/cov-analysis-linux64-6.0.2/bin/cov-analyze --dir $WORKSPACE/coverity  
            
            /opt/cov-analysis-linux64-6.0.2/bin/cov-commit-defects --host usd-cov-cim.usd.lab.emc.com --dataport 9090 --user devcovuser  --password devCommit1 --dir $WORKSPACE/coverity --stream $STREAM > $WORKSPACE/coverityruninfo.txt
            exitStatus=$?
            
            if [ $exitStatus == 0 ]; then  
                cat $WORKSPACE/coverityruninfo.txt
                
                # if this works then $WORKSPACE//coverityruninfo.txt will contain the snapshot ID that the defects were committed under  
                snapid=$(grep -o 'New snapshot ID[^"]*' $WORKSPACE/coverityruninfo.txt)
                echo "$snapid,https://usd-cov-cim.usd.lab.emc.com:8443/" >> $WORKSPACE/TestResults.log
            fi
            
        else 
            echo "DOING_MODIFIED_BUILD:$DOING_MODIFIED_BUILD"
            if [ "$DOING_MODIFIED_BUILD" == "1" ]; then
                if [ $newbuildEnv == 0 ]; then
                    "$GOSP" -- --- -c "cd '$WORKSPACE'; CFG_HEALTH_CHECK=0; build_all -t GNOSIS --no-check-buildenv --no-incremental --inplace --output "$CFG_OUTPUT" -f $BUILD_FLAVOR $BUILD_TARGET"
                else
                    cd $WORKSPACE
                    CFG_HEALTH_CHECK=0 
                    build_all -t GNOSIS --no-check-buildenv --no-incremental -f $BUILD_FLAVOR --inplace --output "$CFG_OUTPUT" -c $BUILD_TARGET
                fi
            else 
                if [ $newbuildEnv == 0 ]; then
                    "$GOSP" -- --- -c "cd '$WORKSPACE'; CFG_HEALTH_CHECK=0; build_all -t GNOSIS --no-check-buildenv --no-incremental -f $BUILD_FLAVOR $BUILD_TARGET"
                else
                    cd $WORKSPACE
                    CFG_HEALTH_CHECK=0 
                    build_all -t GNOSIS --no-check-buildenv --no-incremental -f $BUILD_FLAVOR -c $BUILD_TARGET
                fi
            fi
            exitStatus=$?
        fi
    fi

    echo "****Build_all exit status is $exitStatus****"
    
    # build.err's presence does not always indicate an error, it can have warnings in it, so this 
    # we search the file for ERROR:
    if [ $exitStatus -ne 0 ]; then 
        echo "$WORKSPACE/output/build.err found, searching to see if ERROR: is present"
        grep "ERROR:" $WORKSPACE/output/build.err
        grepStatus=$?
        if [ $grepStatus -eq 0 ]; then
            echo "$WORKSPACE/output/build.err found and ERROR: is present"
            echo "***************Start of build.err output***********************"
            cat $WORKSPACE/output/build.err
            echo "***************End of build.err output***********************"
            exitStatus=1
        else
            exitStatus=0
        fi
    fi
    
    echo "Now that the build is finished we need to change the ownership of some files"
    echo "This is done so we can delete the afterwards...."
    sudo chown -R c4dev:users $WORKSPACE/*
    sudo chown -R c4dev:users $WORKSPACE/.*
    
    echo "****Exiting PerformBuild: Type:$1 ExitStatus: $exitStatus"
    if [ "$debuggingScript" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
}

###############################################################################
#
#   PerformTest - this subroutine when called performs the set of tests 
#     for the specified target
#
#
#   This should be used for Nightly, bullseye, and OnDemand builds.
#
#   INPUTS:
#       $1 - name of target to test.  Options are MCC, MCR, MLU, FILE, UFS64 or MCF.
#
###############################################################################
PerformTest() {
    if [ "$debuggingScript" == '1' ]; then
        set -x
    fi
    echo "****Entering PerformTest: Test:$1"
    echo "****PerformTest using verbosity level: $VERBOSITY_LEVEL_OUTPUT"
    echo "****PerformTest using testing type: $TESTING_TYPE"
    echo "****PerformTest using extraCli options: $CLIOPTION"
    echo "****PerformTest using testpart: $TEST_CONFIGURATION_PART"
    testtarget=$1

    # The default status is success 
    exitStatus=0

    # remove shared memory files that may have been left over from previous
    # tests
    sudo bash -c "rm /dev/shm/sem.*"
    sudo bash -c "rm /dev/shm/shm.*"
    sudo bash -c "rm /dev/shm/*.mut_shm"

    echo "Current Directory: $PWD"
    echo "Current Workspace: $WORKSPACE"

    # Set the working path for the sudo environment
    sudo bash -c "declare -x WORKINGPATH=$PWD"

    # set the working path for the non-sudo environment
    declare -x WORKINGPATH=$PWD
    echo "sudo execution path"
    sudo bash -c "echo $PWD"
    echo "non-sudo execution path"
    echo "$PWD"
    echo "Changing protection on testing Perl scripts"
    sudo chmod +x safe/safe_util/adebuild.mod/mutRegress.pl    
    sudo chmod +x safe/safe_util/adebuild.mod/regressMCR.pl
    sudo chmod +x safe/Targets/armada64_checked/simulation/exec/fbe_test.py

    echo "copy safe_registry.ini files to simulation/exec"
    targetdir=$(ls 'safe/Targets' | grep 'armada64_')
    cp safe/safe_array/safe_registry.ini.* safe/Targets/$targetdir/simulation/exec
    
    iteration="1"
    case $1 in
        mcc )
            if [ -e 'safe/FabricArray/Cache/Test/Test_List_MCC.JSON' ]; then
                configDir="FabricArray/Cache/Test"
                configList="Test_List_MCC.JSON"
            else
                configDir="FabricArray/Cache/Test"
                configList="Test_List.JSON"
            fi
            timeout="45"
            workers="4"
            ;;
        mcf )
            if [ -e 'safe/FabricArray/Cache/Test/Test_List_MCF.JSON' ]; then
                configDir="FabricArray/Cache/Test"
                configList="Test_List_MCF.JSON"
            else
                configDir="FabricArray/Cache/Test"
                configList="Test_List.JSON"
            fi
            timeout="45"
            workers="4"
            ;;
        mlu )
            configDir="layered/MLU/test/MUT"
            configList="Test_List.JSON"
            timeout="120"
            workers="2"
            ;;
        file )
            configDir="layered/MLU/krnl/Dart/server/src/cbfs/test"
            configList="Test_List.JSON"
            timeout="120"
            workers="4"
            ;;
        ufs64 )
            configDir="layered/MLU/test/MUT/ufs64/ufs64sim"
            configList="Test_List.JSON"
            timeout="120"
            workers="4"
            ;;
         mcr )
            configDir="disk/fbe/src/fbe_test/bullseye"
            configList="Test_List$TEST_CONFIGURATION_PART.JSON"
            timeout="360"
            workers="4"
            ;;
         *)
            echo "Unknown test target $1"
            exit 1
            ;;
    esac
    
    echo "***Parameters to be used for mutRegress.pl run***"
    echo "configDir: $configDir"
    echo "configList: $configList"
    echo "timeout: $timeout"
    echo "workers: $workers"

    echo "reset core_uses_pid back to the default"
    sudo bash -c 'echo 0 > /proc/sys/kernel/core_uses_pid'

    if [[ "$BUILD_TYPE" == "Bullseye" ]] || [[ "$BUILD_TYPE" == "bullseye" ]]; then
        echo "Starting Bullseye regression tests..."
        
        sudo mkdir "$WORKINGPATH"/safe/BULLSEYE_HTML
        sudo chown c4dev:users "$WORKINGPATH"/safe/BULLSEYE_HTML
        # ignore errors on the following 2 commands
        if [ ! -e '/BullseyeLicense' ]; then
            sudo mkdir /BullseyeLicense
        fi
        if mount | grep /BullseyeLicense > /dev/null; then
            sudo umount /BullseyeLicense
        fi
        # stop ignoring errors
        sudo mount -o nfsvers=3 bullseye-lic1.usd.lab.emc.com:/BullseyeLicense /BullseyeLicense
        echo "do a directory to see if test.cov was copied"
        ls "$WORKINGPATH"/safe/Targets/armada64_checked/test.cov
                
        echo "****Setup bash trap Workspace: $WORKSPACE ****"
        trap ChangeTargetDirectoryOwnerNoGit ERR
    
        case "$1" in

        # This is temporary until TEST_LIST_MCC and TEST_LIST_MCF files get promoted        
        'mcc' | 'mcf' )
            echo "Executing $1 bullseye regression tests..."
        
#            echo "Start of Bullseye Exclusions being used"
#            cat $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg
#            echo "End of Bullseye Exclusions being used"
            tProject=$1
            if [ "$tProject" == 'mcf' ]; then
                tProject='fct'
            fi
            
            if [ -n "$CATEGORY" ]; then
                sudo bash -c "cd safe && source SAFE_SET_KHENV && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -category \"$CATEGORY\" -view . -extraCli \"$CLIOPTION\" -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg -runproject $tProject"
                exitStatus=$?
            else
                sudo bash -c "cd safe && source SAFE_SET_KHENV && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -view . -extraCli \"$CLIOPTION\" -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg -runproject $tProject"
                exitStatus=$?
            fi
            echo "Completed $1 bullseye regression tests..."
            ;;
        'file' | 'ufs64' | 'mlu' )
            echo "Executing $1 bullseye regression tests..."
        
#            echo "Start of Bullseye Exclusions being used"
#            cat $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg
#            echo "End of Bullseye Exclusions being used"
            
            if [ -n "$CATEGORY" ]; then
                sudo bash -c "cd safe && source SAFE_SET_KHENV && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -category \"$CATEGORY\" -view . -extraCli \"$CLIOPTION\" -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg"
                exitStatus=$?
            else
                sudo bash -c "cd safe && source SAFE_SET_KHENV && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -view . -extraCli \"$CLIOPTION\" -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg"
                exitStatus=$?
            fi
            echo "Completed $1 bullseye regression tests..."
            ;;
                
        'mcr')
            echo "Executing mcr bullseye regression tests..."
            
#            echo "Start of Bullseye Exclusions being used"
#            cat $WORKSPACE/safe/catmerge/FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg
#            echo "End of Bullseye Exclusions being used"
            
            sudo bash -c "cd safe && source SAFE_SET_KHENV && chmod +x Targets/armada64_checked/simulation/exec/fbe_test.py && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -view $WORKINGPATH/safe -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg"
#            sudo bash -c "cd safe && source SAFE_SET_KHENV && chmod +x Targets/armada64_checked/simulation/exec/fbe_test.py && export PATH=/opt/BullseyeCoverage/bin:$PATH && covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager && safe_util/adebuild.mod/regressMCR.pl -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -bullseye -view $WORKINGPATH/safe -html $WORKINGPATH/safe/BULLSEYE_HTML -template FabricArray/Cache/Test/BlockDomain_SIM_BullseyeCoverageExclusions.cfg"
            sudo bash -c "cp $WORKINGPATH/safe/Targets/armada64_checked/simulation/exec/suite.log $WORKINGPATH/suite.log"

            sudo bash -c "mkdir $WORKINGPATH/safe/Targets/armada64_checked/simulation/exec/fbe_test_results && export PATH=/opt/accurev/bin:$PATH"
            sudo bash -c "cd safe && cd Targets/armada64_checked/simulation/exec/ && cd ../../../../ && echo $PWD"
            sudo bash -c "mkdir $WORKINGPATH/fbe_test_report && chown c4dev:users $WORKINGPATH/fbe_test_report"
            sudo bash -c "python safe/catmerge/tools/auto_fbe_test/fbe_test_analyze.py -n -detailed_results $WORKINGPATH/fbe_test_report"
            exitStatus=$?
            
            echo "Completed mcr fbe bullseye regression tests..."
            ;;
            
         *)
            echo 'Unknown test target'
            exit 1
            ;;
        esac
         
        echo "Completed Bullseye regression tests..."

        sudo chown -R c4dev:users "$WORKINGPATH"/*
        sudo echo "BULLSEYE_RESULTS_PATH: $BULLSEYE_RESULTS_PATH"

        echo "Running bullshtml on $WORKINGPATH/safe/BULLSEYE_HTML/test.cov"
        declare -x PATH=/opt/BullseyeCoverage/bin:$PATH 
        covlmgr --use -f /BullseyeLicense/BullseyeCoverageLicenseManager        
        $BULLS_LOCATION/bullshtml -f $WORKINGPATH/safe/BULLSEYE_HTML/test.cov $WORKINGPATH/safe/BULLSEYE_HTML
        
        if [ "$DOING_TRIM" == "1" ]; then
            echo "Doing Trim of clover.xml"
            cp $WORKINGPATH/safe/BULLSEYE_HTML/clover.xml $WORKINGPATH/safe/BULLSEYE_HTML/original_clover.xml
            $SS_LOCATION/TrimClover.pl -xmlfilename $WORKINGPATH/safe/BULLSEYE_HTML/original_clover.xml -outputfn $WORKINGPATH/safe/BULLSEYE_HTML/clover.xml -testsuite $testtarget
        fi
                
        echo "Running covsrc to generate CSV file for later analysis."
        /opt/BullseyeCoverage/bin/covsrc -d $WORKINGPATH -f $WORKINGPATH/safe/BULLSEYE_HTML/test.cov -c -o $WORKINGPATH/safe/BULLSEYE_HTML/test.csv
                        
        echo "Current Directory: $PWD"
        tar --dereference  --hard-dereference -czf artifactory "$WORKINGPATH"/safe/BULLSEYE_HTML
        echo "See if XML is present in safe/BULLSEYE_HTML"
        ls -lr "$WORKINGPATH"/safe/BULLSEYE_HTML/*.xml
        echo "BULLSEYE_HTML files are archived !!!"
                
    else
        echo "Starting $1 regression tests..."
        echo "directory $PWD"
        ls -lr
        
        echo "****Setup bash trap Workspace: $WORKSPACE ****"
        trap ChangeTargetDirectoryOwnerNoGit ERR
    
        # We are not running bullseye perform setup
        case "$1" in 
    
        'mcc' | 'mcf' )
            echo "Executing $1 regression tests..."
            declare -x BLD_TAG_NAME=$(ls 'Targets' | grep 'armada64_')
                
            tProject=$1
            if [ "$tProject" == 'mcf' ]; then
                tProject='fct'
            fi
            
            if [ -z "$CATEGORY" ]; then
                sudo bash -c "cd safe/ && source SAFE_SET_KHENV && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -view . -extraCli \"$CLIOPTION\" -tagname $(ls 'safe/Targets' | grep 'armada64_') -runproject $tProject"
                exitStatus=$?
            else
                sudo bash -c "cd safe/ && source SAFE_SET_KHENV && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -view . -category \"$CATEGORY\" -extraCli \"$CLIOPTION\" -tagname $(ls 'safe/Targets' | grep 'armada64_') -runproject $tProject"
                exitStatus=$?
            fi
        
            echo "Completed $1 regression tests..."
            ;;
                
        'mlu' | 'file' | 'ufs64' )
            echo "Executing $1 regression tests..."
            declare -x BLD_TAG_NAME=$(ls 'Targets' | grep 'armada64_')
                
            if [ -z "$CATEGORY" ]; then
                sudo bash -c "cd safe/ && source SAFE_SET_KHENV && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -view . -extraCli \"$CLIOPTION\" -tagname $(ls 'safe/Targets' | grep 'armada64_')"
                exitStatus=$?
            else
                sudo bash -c "cd safe/ && source SAFE_SET_KHENV && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -view . -category \"$CATEGORY\" -extraCli \"$CLIOPTION\" -tagname $(ls 'safe/Targets' | grep 'armada64_')"
                exitStatus=$?
            fi
        
            echo "Completed $1 regression tests..."
            ;;
                
        'mcr')
            echo "Executing mcr regression tests..."

            sudo bash -c "cd safe/ && source SAFE_SET_KHENV && safe_util/adebuild.mod/mutRegress.pl -configDir ${configDir} -list ${configList} -timeout ${timeout} -worker ${workers} -testType \"$TESTING_TYPE\" -verbosity \"$VERBOSITY_LEVEL_OUTPUT\" -nocleanup -view . -extraCli \"$CLIOPTION\" -tagname $(ls 'safe/Targets' | grep 'armada64_')"
#             sudo bash -c "cd safe && source SAFE_SET_KHENV && cd Targets/armada64_checked/simulation/exec/ && python fbe_test.py -tests sep_mrg_test_suite -i 1 -n 8 -nogui"
#            if [ $TEST_CONFIGURATION_PART == "0"] ; then
#                sudo bash -c "cd safe && source SAFE_SET_KHENV && cd Targets/armada64_checked/simulation/exec/ && python fbe_test.py -tests sep_trg_test_suite -i 1 -n 8"
#            else
#                sudo bash -c "cd safe && source SAFE_SET_KHENV && cd Targets/armada64_checked/simulation/exec/ && python fbe_test.py -tests spe_mrg_test_suite -i 1 -n 8"
#            fi
            sudo bash -c "cp $WORKINGPATH/safe/Targets/armada64_checked/simulation/exec/suite.log $WORKINGPATH/suite.log"
            echo "MCR Suite.log results start..."
            sudo bash -c "cat $WORKINGPATH/suite.log"
            echo "MCR Suite.log results end..."

            sudo bash -c "mkdir $WORKINGPATH/safe/Targets/armada64_checked/simulation/exec/fbe_test_results && export PATH=/opt/accurev/bin:$PATH"
            sudo bash -c "cd safe && cd Targets/armada64_checked/simulation/exec/ && cd ../../../../ && echo $PWD"
            sudo bash -c "mkdir $WORKINGPATH/fbe_test_report && chown c4dev:users $WORKINGPATH/fbe_test_report"
            sudo bash -c "python safe/catmerge/tools/auto_fbe_test/fbe_test_analyze.py -n -detailed_results $WORKINGPATH/fbe_test_report"
            exitStatus=$?
            
            echo "Completed mcr fbe regression tests..."
            ;;
            
            
         *)
            echo 'Unknown test target'
            exit 1
            ;;
            
         esac

        # Change the ownership of the files so the can be deleted later
        sudo chown -R c4dev:users "$WORKINGPATH"/*
        sudo chmod -R 777 "$WORKINGPATH"/*
            
    fi
    echo "****Exiting PerformTest: Type:$1 ExitStatus: $exitStatus"
    if [ "$debuggingScript" == '1' ]; then
        set +x
    fi
    
    exit $exitStatus
 }
 
###############################################################################
#
#   RemoveWorkspace - this subroutine is called to remove the contents of a
#       workspace.
#
#   This should be used for Nightly, bullseye, and OnDemand builds.
#
#   INPUTS:
#       None.
#
###############################################################################
RemoveWorkspace() {
    if [ "$debuggingScript" == '1' ]; then
        set -x
    fi
    
    echo "CHOWN and RM Workspace..."
    sudo chown -R c4dev:users *
    rm -rf safe/*
    rm -rf sade/*
    echo "CHOWN and RM Workspace done..."
    
    # disable synctime, supposedly time problem fixed in accurev
    #sudo /opt/accurev/bin/accurev synctime
    if [ "$debuggingScript" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   CaptureFailureLogs - this subroutine is called to capture the failure log
#     for the tests that were run.
#
#   This should be used for Nightly, bullseye, and OnDemand builds.
#
#   INPUTS:
#       None.
#
###############################################################################
CaptureFailureLogs() {
    if [ "$debuggingScript" == '1' ]; then
        set -x
    fi
    echo "****Entering CaptureFailureLogs"
    
        #capture Test logs
    mkdir parallelTestlogs
    cp safe/Targets/armada64_*/simulation/exec/*.log parallelTestlogs
    cp safe/Targets/armada64_*/simulation/exec/*.dbt parallelTestlogs
    echo "Current Directory is $PWD"
    tar -czf artifactory parallelTestlogs $(find safe/Targets/armada64_*/simulation/exec/ | grep -e '.dmp.*' -e '.dbt' -e '.txt' )

    echo "****Entering CaptureFailureLogs"
    if [ "$debuggingScript" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#   GenerateJunitResults - this subroutine is called to create Junit Results
#       script accepts filename as parameter
#       file needs to contain parses test results in the specified below format
#       script converts results into JUnit format
#       accepted format:
#       <test suite name> <# of tests> <# of tests passed> <# of tests failed> 
#                     <execution time> <test suite result: PASSED|FAILED> <executable name>
#
#   This should be used for OnDemand builds.
#
#   INPUTS:
#       $1 - test results log file
#       $2 - package name
#
###############################################################################
GenerateJunitResults() {
# script accepts filename as parameter
# file needs to contain parses test results in the specified below format
# script converts results into JUnit format
# accepted format:
# <test suite name> <# of tests> <# of tests passed> <# of tests failed> <execution time> <test suite result: PASSED|FAILED> <executable name>
# SCRIPT Parameters:
# $1 - test results log file
# $2 - package name

# validate if filename is provided in $1 and if that file exists
show_help=false
if [ $# -le 0 ]
then
  show_help=true
else
  if [ ! -e $1 ]
  then
    show_help=true
  fi
fi

# display help and exit if not all required parameters were provided
if [ $show_help = true ]
then
  echo "No source file provided"
  echo "Usage:"
  echo "$1 - file with test results"
  echo "$2 - module name. Optional"
  echo "File format:  <test suite name> <# of tests> <# of tests passed> <# of tests failed> <execution time> <test suite result: PASSED|FAILED> <executable name>"
  exit 1
fi

# first awk execution finds TOTALS section in the log
# and adds summary (<tstsuites>) section to the top of the logfile
# it passes results along with original file (using cat) to the second awk instance
awk '
{
#  cmd = "date"
#  cmd | getline execdatetime
#  close(cmd)

#         if ($1 == "TOTALS:"){
#    print "<testsuites tests=\"" $2 "\" failures=\"" $4 "\" time=\"" $5 "\" timestamp=\"" execdatetime "\">"
#  }
}
END {
  # store package name parameter to pass to the next awk cycle
  print "PACKAGENAME " package
}' \
package=$2 $1 | cat - $1 | \
# This section creates actual test records
awk '
BEGIN {
  # adding XML header
  print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
  print "<testsuites>"
}
{
  if ($1 == "PACKAGENAME"){
    package = $2
  }

  # re-printing <testsuites> header created by previous awk run
#  if ($1 == "<testsuites") print $0

  # only processing test SUCCESS and FAILURE records
    if ($6 == "PASSED" || $6 == "FAILED" || $5 == "PASSED" || $5 == "FAILED"){
    # validating proper values to avoid generating garbage
    if ($2 >= 0 && $3 >= 0 && $4 >= 0) {
      # adding test suite record with passes/failures and execution time
      strTime = "\" time=\"" 0 "\""
      if ($5 >= 0)
        strTime = "\" time=\"" $5 "\""

      print "\t" "<testsuite name=\"" $1 "\" package=\"" package "\" tests=\"" $2 "\" failures=\"" $4 strTime ">"

      # creating actual test records based on total number of tests $2 and number of failures $4
      # testsuite execution time will be divided across all tests
      for (i = 0; i < $3; i++){
        strTime = "time=\"" 0 "\""
        if ($5 >= 0)
          strTime = "time=\"" $5/$3 "\""
        print "\t\t" "<testcase name=\"" $1 ":" i+1 "\" status=\"run\" " strTime " classname=\"" package "." $1 "\"/>"
      }

      # looping through failures
      for (i = 0; i < $4; i++){
        strTime = "time=\"" 0 "\""
        if ($5 >= 0)
          strTime = "time=\"" $5/$4 "\""
        print "\t\t" "<testcase name=\"" $1 ":" i+1 "\" status=\"run\" " strTime " classname=\"" package "." $1 "\">"
        print "\t\t\t" "<failure message=\"" $1 ":" i+1 " test failed\"> </failure>"
        print "\t\t" "</testcase>"
      }
      print "\t" "</testsuite>"
    }
  }
}
END {
  print "</testsuites>"
}
'
}

###############################################################################
#
#    GenerateHtmlReport - This subroutine is called to create report.html 
#    which is email template used for sending email to user after build 
#    and test on jenkins. It execute generateEmailTemplate.pl and store result 
#    in report.html and if there is an error it goes to console log.
#
###############################################################################
GenerateHtmlReport() {

    if [ "$debuggingGenerateReport" == '1' ]; then
        set -x
    fi

    echo "****Entering GenerateHtmlReport: Report: report.html"
    echo "****Entering GenerateHtmlReport: directory:$PWD"
    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    result=$(perl $SS_LOCATION/generateEmailTemplate.pl 2>&1);
    if [ "$?" = "0" ]; then
    
       echo $result > report.html
    
    else
       echo $result 
    fi
 
    echo "****Exiting GenerateHtmlReport"

    if [ "$debuggingGenerateReport" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    DeleteEMSD_MCC_TESTArtifacts - This subroutine is called to delete 
#    files that are eligible for deletion from Artifact host
#
#
###############################################################################
DeleteEMSD_MCC_TESTArtifacts() {

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set -x
    fi

    echo "****Entering  DeleteEMSD_MCC_TESTArtifacts : directory:$PWD"

    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    perl $SS_LOCATION/deleteEMSDArtifacts.pl $2>&1;

    echo "****Exiting DeleteEMSD_MCC_TESTArtifacts"

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    UpdateTestFarmStatus - This subroutine is called to update the status
#    of the arrays in the test farm
#
#
###############################################################################
UpdateTestFarmStatus() {

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set -x
    fi

    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    
    echo "****Entering  UpdateTestFarmStatus : directory:$PWD ciserver: $1"

    ciServer=$1

    if [ -e "$WORKSPACE/TestFarmStatus.txt" ]; then
        chmod 777 $WORKSPACE/TestFarmStatus.txt;
    fi
    
    # Generate the TestFramStatus.txt file that we will use for display
    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    
    perl $SS_LOCATION/graph-testbed-v2.pl $ciServer $2>&1;
    
    # do a line count of the file so that we can attempt to dynamically determine the
    # size of the image we want to generate.  15 seems like a good number to use for
    # the height of each line of text.
    wc -l < $WORKSPACE/TestFarmStatus.txt > /tmp/lc.txt
    linecount="$(cat /tmp/lc.txt)"
    rm /tmp/lc.txt
    height=$(($linecount * 15));
    echo "linecount = $linecount, height = $height"
    
    # convert the text file into a image and move it to the userContent directory on
    # Jenkins so it can be displayed by the automatos-pipeline-workflow page.
    convert -size 1900x"$height" xc:white -font "/usr/share/fonts/truetype/VeraMono.ttf" -pointsize 12 -fill black -annotate +15+15 "@$WORKSPACE/TestFarmStatus.txt" $JENKINS_HOME/userContent/TestFarmStatus.png

    echo "****Exiting UpdateTestFarmStatus"

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    RunWeeklyBullseyeReportGenerator - This subroutine is called to create
#       weekly bullseye reports
#
#
###############################################################################
RunWeeklyBullseyeReportGenerator() {

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set -x
    fi

    echo "****Entering  RunWeeklyBullseyeReportGenerator : directory:$PWD"

    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    
    #perl $SS_LOCATION/BullseyeReportGenerator.pl -email "Mark.Cariddi@emc.com" $2>&1;
    perl $SS_LOCATION/BullseyeReportGenerator.pl $2>&1;
    
    # go back to the top of the workspace
    cd $WORKSPACE

    echo "****Exiting RunWeeklyBullseyeReportGenerator"

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    RunWeeklyJunitReportGenerator - This subroutine is called to create
#       weekly junit reports
#
#
###############################################################################
RunWeeklyJunitReportGenerator() {

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set -x
    fi

    echo "****Entering  RunWeeklyJunitReportGenerator : directory:$PWD"

    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    
    #perl $SS_LOCATION/JunitReportGenerator.pl -email "Mark.Cariddi@emc.com" $2>&1;
    perl $SS_LOCATION/JunitReportGenerator.pl  $2>&1;
    
    # go back to the top of the workspace
    cd $WORKSPACE

    echo "****Exiting RunWeeklyJunitReportGenerator"

    if [ "$debuggingEMSDAdmin" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    GenerateDoxygenReport - This subroutine is called to generate doxygen reports
#       if the stream being built requests it.
#
#
#   INPUTS:
#       $1 - name of doxygen configuration file to use
#
###############################################################################
GenerateDoxygenReport() {
    if [ "$debuggingDoxygen" == '1' ]; then
        set -x
    fi

    echo "*** Entering GenerateDoxygenReport WORKSPACE:$WORKSPACE***"
    
    cd $WORKSPACE
    
    # Clean up the HTML output directory that may or may not exist in the workspace.
    
    mkdir -p $WORKSPACE/output/Doxygen_HTML
    rm -f $WORKSPACE/output/Doxygen_HTML/html/*
    
    # Setup an environment variable named DOXY_WS_VERSION for Doxygen to use for displaying the version of code
    # used to generate documentation.
    
    ws="${JOB_NAME}"
    # If JOB_NAME does not have 'ondemand' in substring then its a nightly build.
    if [[ "$ws" == *"ondemand"* ]]; then
        export DOXY_WS_VERSION="Workspace: $STREAM"
    else
        export DOXY_WS_VERSION="Stream:$ACCUREV_STREAM Transaction_ID:$ACCUREV_LAST_TRANSACTION"
    fi
    
    # Generate the new doxygen files.
    export PERL5LIB=$SS_LOCATION:$PERL5LIB
    /usr/bin/doxygen $SS_LOCATION/Doxygen/$1
    
    echo "*** Exiting GenerateDoxygenReport ***"

    if [ "$debuggingDoxygen" == '1' ]; then
        set +x
    fi
}

###############################################################################
#
#    PopulateFromSourceControl - This subroutine is called to populate some
#       item or items from source control
#
#
#   INPUTS:
#       $1 - What to populate
#       $2 - Recursive flag if needed
#
###############################################################################
PopulateFromSourceControl() {
    if [ "$debuggingPopulateFromSourceControl" == '1' ]; then
        set -x
    fi

    echo "*** Entering PopulateFromSourceControl WORKSPACE:$WORKSPACE, MCX_DSL_SCM:$MCX_DSL_SCM Populating:$1***"
    
    if [ "$MCX_DSL_SCM" == 'accurev' ]; then
        accurev pop -O $2 -v $SCRIPTS_STREAM -L $WORKSPACE $1
    else
        wget -x -nH $SCRIPTS_STREAM $1
    fi
    echo "*** Exiting PopulateFromSourceControl ***"

    if [ "$debuggingPopulateFromSourceControl" == '1' ]; then
        set +x
    fi
}

###############################################################################
function die() {
    printf 'ERROR: %s\n' "$@" >&2
    exit 255
}

function technical_debt() {

    echo "*** Entering technical_debt ***"

    if [ "$debuggingGitHub" == '1' ]; then
        set -x
    fi

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
    
    echo -e "protocol=https\nhost=${github_hostname}\nusername=${github_user}\npassword=${github_password}\n"

    # Get the Git LFS url, parse it and set credentials for it
    # TODO: could there be more than one LFS repo?
    
    # MJB: original command:   declare git_lfs_url=$(git config --file ../.lfsconfig --get lfs.url)
    declare git_lfs_url=$(git config --file .lfsconfig --get lfs.url)
    # MJB: hardcode value, as .lfsconfig doesn't exist yet.
    # MJB: clare git_lfs_url='https://amaas-mr-mw1.cec.lab.emc.com/artifactory/api/lfs/unity-git-lfs'
    [[ $git_lfs_url ]] || die "Failed to obtain Git LFS configuration"

    [[ $git_lfs_url =~ ([^:]*)://([^/]*)/(.*) ]] || die "Failed to parse URL $git_lfs_url"

    git credential approve < <(echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n") || die "Failed to set credentials for $url"
    
    echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n"

    echo "*** Exiting technical_debt ***"

    if [ "$debuggingGitHub" == '1' ]; then
        set +x
    fi
}

function PopulateGitHubWorkspace() {

    echo "*** Entering PopulateGitHubWorkspace ***"

    if [ "$debuggingGitHub" == '1' ]; then
        set -x
    fi

    # Get github hostname by getting the GitHub url and parsing it
    github_url=$STREAM
#    github_url=$(git config --get remote.origin.url)
    github_url=${github_url#git@}
    github_url=${github_url#http*://}
    github_url=${github_url%:*}
    declare ci_github_hostname=${github_url%%/*}
    [[ -n $ci_github_hostname ]] || die "Failed to obtain GitHub hostname"
    
    # save credentials for github access and git lfs - not handled by Jenkins job
    # NOTE: save credentials here because don't want to expose passwords in sourced config file
    [[ -n ${USERNAME} ]] || die "USERNAME env variable not set by Jenkins job"
    [[ -n ${!USERNAME} ]] || die "!USERNAME ${USERNAME} env variable not set by Jenkins job"
    
    technical_debt $ci_github_hostname ${USERNAME} ${!USERNAME}
    
    
    #github_url=$(git config --get remote.origin.url)
    #git lfs clone  --branch ${BRANCH} ${github_url} src
    
    pwd
    ls -a
    
    git lfs pull || die "Failed to populate binaries into the workspace"
    
    pwd
    ls -a

    echo "*** Exiting PopulateGitHubWorkspace ***"

    if [ "$debuggingGitHub" == '1' ]; then
        set +x
    fi

}
###############################################################################

# Set debuggingScript to 1 to see the script output in the log, 0 stops logging
debuggingScript=1
debuggingPromotion=1
debuggingEMSDAdmin=1
debuggingImageProcessing=1
debuggingArchiveProcessing=0
debuggingWorkspaceProcessing=1
debuggingWorkspaceCleanup=0
debuggingJunitResults=0
debuggingSetupForTestRun=0
debuggingGenerateReport=1
debuggingAutomatos=1
debuggingDoxygen=0
debuggingPopulateFromSourceControl=1
debuggingGitHub=1

# Artifactory Repository that we use
ARTIFACTORY_REPO='https://arhost3.usd.lab.emc.com/artifactory/EMSD_MCC_TEST'
ARTIFACTORY_REPO_START="$ARTIFACTORY_REPO/"

# Different user names and passwords for dealing with artifactory host
ARTIFACTORY_DELETE_USER='mcc_test_deleter2'
ARTIFACTORY_DELETE_PASSWORD='Ehxrqecuj0CJtnrrA3kW'

ARTIFACTORY_READER_USER='mcc_test_reader'
ARTIFACTORY_READER_PASSWORD='mcc*read*poc1'

ARTIFACTORY_DEPLOYER_USER='mcc_test_deployer'
ARTIFACTORY_DEPLOYER_PASSWORD='mcc*deploy*poc1'

# Location of where Automatos images are kept for runs
AUTOMATOS_TEST_IMAGE_SUBDIR_PREFIX="automatosimage"

# Base Location of this file
#SS_LOCATION=$WORKSPACE/devenable/CI/Jenkins/CodeGeneration/MCX_DSL
SS_LOCATION=/net/$JENKINS_SERVER/build_artifacts/Mcx_Reports
BULLS_LOCATION=/net/$JENKINS_SERVER/build_artifacts/Mcx_Reports/bullshtml

# call arguments verbatim:
$@
  
