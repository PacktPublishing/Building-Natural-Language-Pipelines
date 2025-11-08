This is a multi-agent architecture that allows me to obtain business reviews using the RapidAPI service

URL: https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews

# Strategy

Use an inmemory document store for this process.

Develop one Haystack pipeline as specified below - store each pipeline in a jupyter notebook under `yelp-navigator`

### Pipeline 1: lets a user or LangGraph agent ask a natural language question searching for businesses and a desired outcome ("best restaurants in town for Mexican food"). The pipeline will use an NER component as seen in named-entity-recognition to extract entities, locations, and use those entities as the keywords. The pipeline returns the key words necessary to populate and execute a query on endpoint SEARCH BUSINESS. The pipeline returns a JSON object with the results found executing that query. Critical information is the business ID and business alias.

### Pipeline 2: let's a user or LangGraph agent get further details about one or more businesses using the output from Pipeline 1 to execute the GET BUSINESS DETAILS endpoint. Uses business ID and business alias to complete query. The pipeline contains a LinkContentFetcher and HTML to Document components to get the website information and stores that information in the form of Haystack documents. It returns Haystack Documents with metadata containing the price range, latitute and longitude, and website. 

## Pipeline 3: let's a user or LangGraph agent get further information about reviews from one or more businesses using the output from Pipeline 1 to execute the GET BUSINESS REVIEWS endpoint. It uses the reviews endpoints and the components used in the pipeline `text-classification/sentiment_analysis.ipynb` to classify the lowest rated and highest rated reviews, it returns a series of Haystack documents with enhanced metadata containing the reviews. One enhanced metadata blob per business. 

## Pipeline 4: lets a user or LangGraph agent obtain a summary, identify key themes and provide a recommendation based on the user request. It will take the Haystack documents from pipeline 3 to form its opinion. 

## Pipeline 5: interacts with the user and asks clarifying questions: it's main objective is to identify a LOCATION and relevant KEY WORDS. 

# ENDPOINTS

## SEARCH BUSINESS: GET BUSINESS ID AND INFORMATION USING LOCATION AND QUERY

Query Params

page
(optional)
Number
Search result page to retrieve, e.g. 3.

Minimum: 1
location
*
Madison, WI
String
Location to search in, e.g. Madison, WI.

sortBy
(optional)
String
Search result ordering.

query
*
Cheese Curds
String
Query string to search for, e.g. Cheese Curds.

### SAMPLE USAGE

```python
import requests

url = "https://yelp-business-reviews.p.rapidapi.com/search"

querystring = {"location":"Madison, WI","query":"Cheese Curds"}

headers = {
	"x-rapidapi-key": "4fb54002a4mshc7a7d2c9c03f45ap15b247jsn289faad3b707",
	"x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

### YIELDS

```bash
HTTP/1.1 200 OK
access-control-allow-credentials: true
access-control-allow-origin: *
content-length: 4479
content-type: application/json
date: Fri, 07 Nov 2025 21:09:13 GMT
server: RapidAPI-1.2.8
vary: Accept-Encoding
x-rapidapi-region: AWS - us-west-2
x-rapidapi-request-id: 88f1bfa503bfa7df176abf189c662cdb854c3625b1673ec5a81612deab0b5786
x-rapidapi-version: 1.2.8
x-ratelimit-rapid-free-plans-hard-limit-limit: 500000
x-ratelimit-rapid-free-plans-hard-limit-remaining: 499991
x-ratelimit-rapid-free-plans-hard-limit-reset: 1046073
x-ratelimit-requests-limit: 50
x-ratelimit-requests-remaining: 41
x-ratelimit-requests-reset: 1046073
{"resultCount":240,"currentPage":1,"totalPages":24,"location":{"city":"Madison, WI"},"results":[{"bizId":"RJNAeNA-209sctUO0dmwuA","name":"The Old Fashioned","alias":"the-old-fashioned-madison","serviceArea":null,"lat":43.07618625,"lon":-89.38375722,"rating":4.1,"reviewCount":2505,"categories":["American","Breakfast & Brunch","Beer Bars"],"services":[],"businessHighlights":[],"priceRange":"$$","phone":"(608) 310-4545","website":"http://theoldfashioned.com/","images":["https://s3-media0.fl.yelpcdn.com/bphoto/n1imsZpO7rNv0aueEL52EQ/348s.jpg"]},{"bizId":"RlulW-HxTuUVk8wSspNXIw","name":"Wisconsin Cheese Mart","alias":"wisconsin-cheese-mart-madison","serviceArea":null,"lat":43.074266,"lon":-89.3873044,"rating":4.2,"reviewCount":25,"categories":["Cheese Shops"],"services":[],"businessHighlights":[],"priceRange":null,"phone":"(414) 272-3544","website":"http://www.wisconsincheesemart.com","images":["https://s3-media0.fl.yelpcdn.com/bphoto/sf4do00IngALCYwkPXu_6Q/348s.jpg"]},
```
----


## GET BUSINESS DETAILS
Query Params

business_aliases
(optional)
the-old-fashioned-madison,the-great-dane-pub-and-brewing-company-madison
String
Comma-separated business aliases

business_ids
(optional)
RJNAeNA-209sctUO0dmwuA,EgtyW19V-64c6PmRuvzSEA
String
Comma-separated business IDs


### SAMPLE USAGE 
```python

import requests

url = "https://yelp-business-reviews.p.rapidapi.com/details"

querystring = {"business_aliases":"the-old-fashioned-madison,the-great-dane-pub-and-brewing-company-madison","business_ids":"RJNAeNA-209sctUO0dmwuA,EgtyW19V-64c6PmRuvzSEA"}

headers = {
	"x-rapidapi-key": "4fb54002a4mshc7a7d2c9c03f45ap15b247jsn289faad3b707",
	"x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

### YIELDS

```bash
HTTP/1.1 200 OK
access-control-allow-credentials: true
access-control-allow-origin: *
content-length: 4479
content-type: application/json
date: Fri, 07 Nov 2025 21:09:13 GMT
server: RapidAPI-1.2.8
vary: Accept-Encoding
x-rapidapi-region: AWS - us-west-2
x-rapidapi-request-id: 88f1bfa503bfa7df176abf189c662cdb854c3625b1673ec5a81612deab0b5786
x-rapidapi-version: 1.2.8
x-ratelimit-rapid-free-plans-hard-limit-limit: 500000
x-ratelimit-rapid-free-plans-hard-limit-remaining: 499991
x-ratelimit-rapid-free-plans-hard-limit-reset: 1046073
x-ratelimit-requests-limit: 50
x-ratelimit-requests-remaining: 41
x-ratelimit-requests-reset: 1046073
{"resultCount":240,"currentPage":1,"totalPages":24,"location":{"city":"Madison, WI"},"results":[{"bizId":"RJNAeNA-209sctUO0dmwuA","name":"The Old Fashioned","alias":"the-old-fashioned-madison","serviceArea":null,"lat":43.07618625,"lon":-89.38375722,"rating":4.1,"reviewCount":2505,"categories":["American","Breakfast & Brunch","Beer Bars"],"services":[],"businessHighlights":[],"priceRange":"$$","phone":"(608) 310-4545","website":"http://theoldfashioned.com/","images":["https://s3-media0.fl.yelpcdn.com/bphoto/n1imsZpO7rNv0aueEL52EQ/348s.jpg"]},{"bizId":"RlulW-HxTuUVk8wSspNXIw","name":"Wisconsin Cheese Mart","alias":"wisconsin-cheese-mart-madison","serviceArea":null,"lat":43.074266,"lon":-89.3873044,"rating":4.2,"reviewCount":25,"categories":["Cheese Shops"],"services":[],"businessHighlights":[],"priceRange":null,"phone":"(414) 272-3544","website":"http://www.wisconsincheesemart.com","images":["https://s3-media0.fl.yelpcdn.com/bphoto/sf4do00IngALCYwkPXu_6Q/348s.jpg"]},
```

----
## GET BUSINESS REVIEWS
Query Params

query
(optional)
String
Text query to filter reviews by, e.g. friendly.

page
(optional)
Number
Review page to retrieve, e.g. 3.

Minimum: 1
sortBy
(optional)
String
Review ordering, e.g. newest.

language
(optional)
String
Review language as ISO 639-1 code, e.g. en.

Path Params

bizId
*
RJNAeNA-209sctUO0dmwuA
String
Business ID, e.g. RJNAeNA-209sctUO0dmwuA

### SAMPLE USAGE

```python
import requests

url = "https://yelp-business-reviews.p.rapidapi.com/reviews/RJNAeNA-209sctUO0dmwuA"

headers = {
	"x-rapidapi-key": "4fb54002a4mshc7a7d2c9c03f45ap15b247jsn289faad3b707",
	"x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

print(response.json())
```

### YIELDS
```bash
HTTP/1.1 200 OK
access-control-allow-credentials: true
access-control-allow-origin: *
content-length: 4479
content-type: application/json
date: Fri, 07 Nov 2025 21:09:13 GMT
server: RapidAPI-1.2.8
vary: Accept-Encoding
x-rapidapi-region: AWS - us-west-2
x-rapidapi-request-id: 88f1bfa503bfa7df176abf189c662cdb854c3625b1673ec5a81612deab0b5786
x-rapidapi-version: 1.2.8
x-ratelimit-rapid-free-plans-hard-limit-limit: 500000
x-ratelimit-rapid-free-plans-hard-limit-remaining: 499991
x-ratelimit-rapid-free-plans-hard-limit-reset: 1046073
x-ratelimit-requests-limit: 50
x-ratelimit-requests-remaining: 41
x-ratelimit-requests-reset: 1046073
{"resultCount":240,"currentPage":1,"totalPages":24,"location":{"city":"Madison, WI"},"results":[{"bizId":"RJNAeNA-209sctUO0dmwuA","name":"The Old Fashioned","alias":"the-old-fashioned-madison","serviceArea":null,"lat":43.07618625,"lon":-89.38375722,"rating":4.1,"reviewCount":2505,"categories":["American","Breakfast & Brunch","Beer Bars"],"services":[],"businessHighlights":[],"priceRange":"$$","phone":"(608) 310-4545","website":"http://theoldfashioned.com/","images":["https://s3-media0.fl.yelpcdn.com/bphoto/n1imsZpO7rNv0aueEL52EQ/348s.jpg"]},{"bizId":"RlulW-HxTuUVk8wSspNXIw","name":"Wisconsin Cheese Mart","alias":"wisconsin-cheese-mart-madison","serviceArea":null,"lat":43.074266,"lon":-89.3873044,"rating":4.2,"reviewCount":25,"categories":["Cheese Shops"],"services":[],"businessHighlights":[],"priceRange":null,"phone":"(414) 272-3544","website":"http://www.wisconsincheesemart.com","images":["https://s3-media0.fl.yelpcdn.com/bphoto/sf4do00IngALCYwkPXu_6Q/348s.jpg"]},
```
