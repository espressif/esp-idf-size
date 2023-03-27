#!/usr/bin/env bash

memory_test () {
    cp -r $IDF_PATH/examples/get-started/hello_world memtest \
    && echo -e "\n***\nBuilding project for $1..." &>> output \
    && idf.py -C memtest set-target $1 \
    && idf.py -C memtest build \
    && echo -e "\n***\nRunning mem_test.py for $1..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json memtest/build/hello_world.map > size_output.json \
    && python -m esptool --chip $1 image_info memtest/build/hello_world.bin > esptool_output \
    && python -m coverage run -a mem_test.py size_output.json esptool_output &>> output \
    && rm -rf memtest
}

{   python -m coverage debug sys \
    && python -m coverage erase &> output \
    && memory_test esp32 \
    && memory_test esp32s2 \
    && memory_test esp32s3 \
    && memory_test esp32c3 \
; } || { echo 'The test for esp_idf_size has failed. Please examine the artifacts.' ; exit 1; }
