# Regression testing
set -e

expected_result=(7 2 1 0 4 1 4 9 5 9)
PASS_COUNT=0

echo "Running testsuite.."
for i in 0 1 2 3 4 5 6 7 8 9 ; do
    # Clean the weights
    make clean;
    result=$(make tcesim INPUT_IMG=test_data/img$i.png | grep -oP '0x0000000\d' | cut -c 10)

    if [ $result -eq ${expected_result[$i]} ] ; then
        echo "img$i: sim output= $result, expected output= ${expected_result[$i]} (Test: PASS)"
        PASS_COUNT=$[PASS_COUNT +1]
    else
        echo "img$i: sim output=$result, expected output= ${expected_result[$i]} (Test: FAIL)"
    fi
done

echo "Pass rate = $PASS_COUNT/10"
