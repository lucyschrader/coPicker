# Picker, a squirrely project

A web-based tool to allow easy selection of [Te Papa collection images][collections online] into 'included' and 'excluded' groups.

For each of Te Papa's humanities and natural science collections, you can:
* Harvest metadata for all collection items that have freely downloadable images over 2500px on their shortest side
* Display each record with thumbnail images and choose whether to include or exclude each image from your selection
* Export a CSV with IRNs (identifiers) for each record and image

Metadata is harvested from [Te Papa's API][api].

Selections are saved on the fly in an sqlite3 database.

Multiple users can work on selections at the same time. Users can also work on different projects, saving their selections separately.

[collections online]: https://collections.tepapa.govt.nz/
[api]: https://data.tepapa.govt.nz/docs/