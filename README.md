API Selection:

Google Book API: https://www.googleapis.com/books/v1/volumes

General Search With GBook API: BASE_URL + ?q=SEARCH_TERM

> From Google Books:

```Pagination
You can paginate the volumes list by specifying two values in the parameters for the request:

startIndex - The position in the collection at which to start. The index of the first item is 0.
maxResults - The maximum number of results to return. The default is 10, and the maximum allowable value is 40.
```

# Testing

```bash
python -m unittest test_app
```
