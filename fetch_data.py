#!/bin/bash

curl -s "https://www.investing.com/commodities/gold" \
| grep -oP '"last-price">\K[0-9,.]+' \
>> data/raw/gold_scraped.txt
