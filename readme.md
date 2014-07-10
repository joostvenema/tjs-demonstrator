# tjs-demonstrator

## What is tjs-demonstrator?

tjs-demonstrator is a web-application written in Python to demonstrate the functionality of a TJS. A work-in-progress TJS can be found here: https://github.com/thijsbrentjens/geoserver/tree/tjs_2.2.x

## What is TJS?

TJS stands for Table Joining Service, read more about it here: http://www.opengeospatial.org/standards/tjs

## Installation

### Requirements

* [Python 3.x](http://www.python.org/getit/)
* [lxml](http://lxml.de/)
* [Bottle](http://bottlepy.org/docs/dev/index.html)
* [Waitress](https://github.com/Pylons/waitress)
* 
### Configuration

Edit config.json. The following settings are required:

`demonstrator_baseurl` - The base URL where the app is running
`tjs_baseurl` - The base URL of the TJS (can be a remote host)
`gdas_uri_prefix` - A prefix for constructing an URI

### Running the app
Start the app: `python3 tjs_demonstrator.py`

To run in the background (linux): `nohup python3 tjs_demonstrator.py > output.log &`

### Using the app

Point your browser to the `base_url` and port (default `8080`). E.g. `http://127.0.0.1:8080`

Upload a csv-file and enter the name of the column wich should be used as the key to join with. In the dropdown-box select a spatial framework to join on.

When submitted, a wms-layer should appear on top of the basemap. Clicking on a feature shows the attribute information in a table.



