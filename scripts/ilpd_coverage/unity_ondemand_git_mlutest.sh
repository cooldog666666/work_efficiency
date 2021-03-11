echo "unityOffArrayTests.txt V1.26"
echo "Environment Variables"
echo "WORKSPACE: $WORKSPACE"
echo "BUILD_TYPE: $BUILD_TYPE"
echo "ARTIFACTS_URL: $ARTIFACTS_URL"
echo "TESTING_FLAVOR: $TESTING_FLAVOR"
echo "BUILD_TYPE: $BUILD_TYPE"
echo "TEST_CONFIGURATION: $TEST_CONFIGURATION"
echo "TEST_CONFIGURATION_PART: $TEST_CONFIGURATION_PART"
echo "MCX_DSL_SCM: $MCX_DSL_SCM"

# No need to do any population, all code is in $WORKSPACE/Mcx_Reports
SCRIPT_PATH="/net/$JENKINS_SERVER/build_artifacts/Mcx_Reports"

# Print out script version we will be running.
$SCRIPT_PATH/McxDslHelperFunctions.sh GetMcxDslHelperFunctionsVersion

cd $WORKSPACE

echo "Change the permission on the bash script file so that we can execute it.   Get the files version number."
$SCRIPT_PATH/McxDslHelperFunctions.sh ChangeTargetDirectoryOwnerNoGit $WORKSPACE


echo "Retrieve the artifact and expand it"
$SCRIPT_PATH/McxDslHelperFunctions.sh RetrieveBuildArtifacts $ARTIFACTS_URL
$SCRIPT_PATH/McxDslHelperFunctions.sh ExpandTarImage  safe.tar.gz
$SCRIPT_PATH/McxDslHelperFunctions.sh SetupLinuxBuildOrTestEnvironment

echo "Override the workspace mutregress.pl, concurrent.pm, and bullseye.pm with our versions so that we can test parallel covmerge"
cp $SCRIPT_PATH/mutRegress.pl $WORKSPACE/safe/safe_util/adebuild.mod/mutRegress.pl
cp $SCRIPT_PATH/Bullseye.pm $WORKSPACE/safe/safe_util/adebuild.mod/Bullseye.pm
cp $SCRIPT_PATH/concurrent.pm $WORKSPACE/safe/safe_util/adebuild.mod/concurrent.pm

# give privileges to process and all children so tests can run.
echo $$ |sudo /usr/bin/tee -a /sys/fs/cgroup/cpu,cpuacct/tasks

echo "Perform the desired tests on the built image"
$SCRIPT_PATH/McxDslHelperFunctions.sh PerformTest  $TESTING_FLAVOR

echo "If this is a bullseye build move the archive of the bullseye results created by mutregress to the arhost"
if [[ "$BUILD_TYPE" = "Bullseye" ]] || [[ "$BUILD_TYPE" = "bullseye" ]]; then
    $SCRIPT_PATH/McxDslHelperFunctions.sh ArchiveBuildArtifacts $TEST_DATA_STREAM bullseye.tar.gz noimage $WORKSPACE/TestResults.log Bullseye_HTML_Results
fi

echo "Add a link to the original source archive to the list of results"
echo "BUILD_ARCHIVE,$ARTIFACTS_URL" >> $WORKSPACE/TestResults.log
echo "Contents of $WORKSPACE/TestResults.log"
cat  $WORKSPACE/TestResults.log

echo "Parse the test results and put the results in suite.log."
cd $WORKSPACE
ls
if [ "$TEST_CONFIGURATION" !=  "mcr" ]; then
    cd $WORKSPACE
    ls
    export PERL5LIB=$SCRIPT_PATH:$PERL5LIB
    perl $SCRIPT_PATH/processTestLogs.pl
else
    ls $WORKSPACE 
    echo "****Start of MCR generated suite.log****"
    cat $WORKSPACE/suite.log
    echo "****End of suite.log****"
    
    echo "Generate jUnit Results"
    mkdir $WORKSPACE/JResults
    $SCRIPT_PATH/McxDslHelperFunctions.sh GenerateJunitResults $WORKSPACE/suite.log $TEST_CONFIGURATION > $WORKSPACE/JResults/junitResults.xml
    cat $WORKSPACE/JResults/junitResults.xml
fi

ls $WORKSPACE 
echo "jUnit Results"
cat $WORKSPACE/JResults/junitResults.xml

