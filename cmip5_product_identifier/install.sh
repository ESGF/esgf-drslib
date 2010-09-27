#!/bin/sh

echo create subdirectory for python shelves
mkdir sh
echo create subdirectory for log files
mkdir logs
echo parse spreadsheets
python cmip5_request_init_v2.py init > logs/installation_log.txt
echo unzipping dummy archive
unzip dummy_archive.zip

echo done, installation log in logs/installation_log.txt
