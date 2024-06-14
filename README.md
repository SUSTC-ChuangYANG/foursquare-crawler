# Foursquare-Crawler
A crawler used to crawl foursquare check-in data.
## Features 
- **Check-in Data Crawling**: allows you to crawl check-in data from Foursquare web pages by providing a URL. It supports both `batch` and `debug` modes. In `batch` mode, you can crawl all check-in URLs from a file and save the results, while in `debug` mode, you can crawl a single URL and print the output.

- **Progress Bar**: displays the progress of the crawling process, giving you real-time feedback on the current state of your crawling tasks.

- **Error Handling and Logging**: saves both successful and failed crawling attempts. For failed attempts, logs the reason for failure, such as WrongUrl (incorrect URL) or PageNotFound (deleted or hidden check-in). See `data/sample_url_failed.csv` FYI.

- **Random User-Agent Generation**: Supports the generation of random User-Agents to simulate requests from different browsers, enhancing the stealthiness of the crawling process.

- **Location statistics**: besides the time, location, and category of each check-in, also gathers statistical information about the POI, including the total number of check-ins, total number of visitors, and tips count.

- **IP Pool Support**: Utilizes an IP pool to counter anti-crawling measures, ensuring more reliable and continuous data crawling.

- **Multi processing Support**: Support multi-process crawling to improve efficiency. 

**Notice**: This repository is for research purposes only. I created it for fun.


### Output Example 
```json 
{
    "fsq_id": "4b89fd41f964a520685a32e3",
    "name": "Tokyo International (Haneda) Airport (HND)",
    "category": [
        {
            "id": "63be6904847c3692a84b9c29",
            "name": "International Airport",
            "primary": true
        }
    ],
    "location": {
        "city": "東京",
        "lng": 139.7802546992898,
        "contextLine": "日本東京",
        "state": "東京都",
        "neighborhood": "羽田空港",
        "country": "日本",
        "postalCode": "144-0041",
        "address": "羽田空港3-3-2",
        "cc": "JP",
        "lat": 35.54846517643472
    },
    "uid": "61142668",
    "location_stats": {
        "checkinsCount": 1178831,
        "usersCount": 169816,
        "tipCount": 492
    },
    "fsq_url": "https://www.swarmapp.com/c/1XCAyGz7knL",
    "tweet_url": "https://t.co/9bSYbewb5K",
    "user_screenname": "test_user"
}
```

### Requirement 
```shell
# more details > requirements.txt
python3.9 
fake-useragent
bs4
requests
pandas 
tqdm 
lxml
pyyaml
```

### Usage
```shell
# batch mode
python fsq_crawler.py --file data/sample_url.csv --outdir ./data/ 
# debug mode 
python fsq_crawler.py --mode debug --url https://t.co/Qm5WGMZiGE 
# large scale crawling mode
python batch_run.py --pool_size 200  --indir your_data_dir --outdir target_dir --ip_pool your_ip_pool_config 

# Output two files by default.
**.successed.csv 
**.failed.csv 
```

----
### Appendix 
#### Explanation for the Output Fields:
```
- fsq_id: The POI (Point of Interest) ID on Foursquare, e.g., '12345'
- name: The name of the POI, e.g., 'Subway Chikusa Station'
- category: Information about the category of the POI
    - category['id']: The ID of the category, e.g., '4bf58dd8d48988d1fd931735'
    - category['name']: The name of the category, e.g., 'Metro Station'
    - category['primary']: Indicates if it is the primary category, e.g., True
- location: Information about the location of the POI
    - location['contextLine']: Contextual information (place name), e.g., 'Nagoya, Japan'
    - location['country']: The country, e.g., 'Japan'
    - location['state']: The prefecture, e.g., 'Aichi Prefecture'
    - location['city']: The city, e.g., 'Nagoya'
    - location['lat']: Latitude, e.g., 35.170653
    - location['lng']: Longitude, e.g., 136.929907
    - location['address']: The address, e.g., '3-15-21 Aoi, Higashi-ku'
    - location['postalCode']: The postal code, e.g., '461-0004'
    - location['cc']: The country code, e.g., 'JP'
    - location['neighborhood']: The neighborhood, e.g., 'Higashi-ku' (Note: some locations may not have this field)
- location_stats: Statistical information about the location
    - location_stats['checkinsCount']: Number of check-ins, e.g., 10523
    - location_stats['usersCount']: Number of users, e.g., 1306
    - location_stats['tipCount']: Number of tips, e.g., 3
- uid: User ID, e.g., '1272416'
- fsq_url: The Foursquare url, e.g., https://www.swarmapp.com/c/k3miIHJz7DU
- tweet_url: The Twitter url, e.g., https://t.co/Qm5WGMZiGE
```



