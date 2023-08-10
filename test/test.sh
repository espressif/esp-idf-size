#!/usr/bin/env bash

json_test() {
    echo -e "\n***\nProducing JSON output for $1..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json app_$1.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archives app_$1.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --files app_$1.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archive_details libdriver.a app_$1.map | python json_validate_test.py &>> output
}

csv_test() {
    echo -e "\n***\nProducing CSV output for $1..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv app_$1.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archives app_$1.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --files app_$1.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archive_details libdriver.a app_$1.map &>> output
}

{   echo -e "\n***\nRunning esp_idf_size..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size on bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size with overflow..." &>> output \
    && python -m coverage run -a -m esp_idf_size overflow.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives..." &>> output \
    && python -m coverage run -a -m esp_idf_size --archives app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files..." &>> output \
    && python -m coverage run -a -m esp_idf_size --files app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details..." &>> output \
    && python -m coverage run -a -m esp_idf_size --archive_details libdriver.a app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff with bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --diff bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff with itself..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff with another app..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --diff app2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff with app in reverse order..." &>> output \
    && python -m coverage run -a -m esp_idf_size app2.map --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archives with bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archives --diff bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archives with itself..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archives --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archives with another app..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archives --diff app2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archives with app in reverse order..." &>> output \
    && python -m coverage run -a -m esp_idf_size app2.map --archives --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --files with bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --files --diff bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --files with itself..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --files --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --files with another app..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --files --diff app2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --files with app in reverse order..." &>> output \
    && python -m coverage run -a -m esp_idf_size app2.map --files --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archive_details libdriver.a --diff bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with bootloader..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archive_details libc.a --diff bootloader.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with itself..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archive_details libdriver.a --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with another app..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archive_details libdriver.a --diff app2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with app in reverse order..." &>> output \
    && python -m coverage run -a -m esp_idf_size app2.map --archive_details libdriver.a --diff app.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff --archive_details with another app..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --archive_details libfreertos.a --diff app2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size on app with nonzero noload sections..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_nonzero_noload.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives on app with nonzero noload sections..." &>> output \
    && python -m coverage run -a -m esp_idf_size --archives app_nonzero_noload.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files on app with nonzero noload sections..." &>> output \
    && python -m coverage run -a -m esp_idf_size --files app_nonzero_noload.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s2 with overflow..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 overflow_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s2 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size on bootloader for esp32s2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 bootloader_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size on bootloader for esp32s2 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size bootloader_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32s2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 --archives app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32s2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 --files app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32s2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s2 --archive_details libdriver.a app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size diff with another app (different target)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app.map --diff app_esp32s2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32h4..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h4 app_esp32h4.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32h4 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32h4.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32h4..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h4 --archives app_esp32h4.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32h4..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h4 --files app_esp32h4.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32h4..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h4 --archive_details libdriver.a app_esp32h4.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c3 app_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c3 with overflow..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c3 overflow_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c3 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32c3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c3 --archives app_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32c3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c3 --files app_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32c3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c3 --archive_details libdriver.a app_esp32c3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 app_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s3 configured with 32KB of icache..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 app_esp32s3_32k_icache.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s3 with overflow..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 overflow_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32s3 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32s3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 --archives app_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32s3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 --files app_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32s3..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32s3 --archive_details libdriver.a app_esp32s3.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c6..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c6 app_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c6 with overflow..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c6 overflow_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32c6 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32c6..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c6 --archives app_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32c6..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c6 --files app_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32c6..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32c6 --archive_details libdriver.a app_esp32c6.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32h2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h2 app_esp32h2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size for esp32h2 (target autodetected)..." &>> output \
    && python -m coverage run -a -m esp_idf_size app_esp32h2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archives for esp32h2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h2 --archives app_esp32h2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --files for esp32h2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h2 --files app_esp32h2.map &>> output \
    && echo -e "\n***\nRunning esp_idf_size --archive_details for esp32h2..." &>> output \
    && python -m coverage run -a -m esp_idf_size --target esp32h2 --archive_details libdriver.a app_esp32h2.map &>> output \
    && echo -e "\n***\nProducing JSON output..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json app.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archives app.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --files app.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archive_details libdriver.a app.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json app.map --diff app2.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archives app.map --diff app2.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --files app.map --diff app2.map | python json_validate_test.py &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --archive_details libdriver.a app.map --diff app2.map | python json_validate_test.py &>> output \
    && json_test esp32s2 \
    && json_test esp32c3 \
    && json_test esp32h4 \
    && json_test esp32s3 \
    && json_test esp32c6 \
    && json_test esp32h2 \
    && echo -e "\n***\nProducing CSV output..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv app.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archives app.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --files app.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archive_details libdriver.a app.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv app.map --diff app2.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archives app.map --diff app2.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --files app.map --diff app2.map &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --archive_details libdriver.a app.map --diff app2.map &>> output \
    && csv_test esp32s2 \
    && csv_test esp32c3 \
    && csv_test esp32h4 \
    && csv_test esp32s3 \
    && csv_test esp32c6 \
    && csv_test esp32h2 \
    && echo -e "\n***\nProducing JSON file output..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=json --output-file output.json app.map &>> output \
    && echo -e "\n***\nProducing text file output..." &>> output \
    && python -m coverage run -a -m esp_idf_size -o output.txt app.map &>> output \
    && echo -e "\n***\nProducing csv file output..." &>> output \
    && python -m coverage run -a -m esp_idf_size --format=csv --output-file output.csv app.map &>> output \
    && echo -e "\n***\nRunning idf_size_tests.py..." &>> output \
    && python -m coverage run -a test_idf_size.py &>> output \
    && echo -e "\n\nComparing expected output..." \
    && diff -Z output expected_output \
    && echo -e "\n\nComparing expected json output..." \
    && diff -Z output.json expected_output.json \
    && echo -e "\n\nComparing expected text output..." \
    && diff -Z output.txt expected_output.txt \
    && echo -e "\n\nComparing expected csv output..." \
    && diff -Z output.csv expected_output.csv \
    && python -m coverage report \
; } || { echo 'The test for esp_idf_size has failed. Please examine the artifacts.' ; exit 1; }

# Note: "diff -Z is used because some versions of Python print trailing whitespace for JSON pretty-printing, and some don't
