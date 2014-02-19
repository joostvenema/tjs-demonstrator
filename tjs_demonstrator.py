# !/usr/bin/env python3
# 
# tjs-demonstrator
#
# version 0.1

from bottle import Bottle, run, route, request, response, static_file
from collections import OrderedDict, defaultdict
import os
import csv
import codecs
import uuid
import json
import urllib.request
import urllib.parse
from lxml import etree, objectify

app = Bottle()

with open('config.json', 'r') as f:
    cfg = json.load(f)

tjs_service = 'TJS'
tjs_version = '1.0.0'

# Get XML metadata for a specific URL
def get_dataset_meta(uri):
    # Construct url
    url = (cfg['tjs_baseurl'] + '/service=' + tjs_service + '&version=' + tjs_version +
            '&request=DescribeFrameworks&FrameworkURI=' + uri)

    # Fetch data
    try:
        y = urllib.request.urlopen(url)     
        xml = etree.parse(y)
        y.close()
        xml_temp = etree.tostring(xml.getroot()[0])
        root  = xml_temp.replace(b'ns0:', b'')
        parser = etree.XMLParser(ns_clean=True, encoding='utf-8')
        root = etree.fromstring(root, parser=parser)

        return root

    except Exception as err:
        print(err)
        return None

# Function to Join GDAS url with a Framework URI
def joindata(framework_uri, gdas_url):

    url = (cfg['tjs_baseurl'] + 'service=' + tjs_service + '&version=' + tjs_version +
            '&request=JoinData&FrameworkURI=' + urllib.parse.quote(framework_uri) + 
            '&GetDataURL=' + urllib.parse.quote(gdas_url))
    y = urllib.request.urlopen(url)
    xml = etree.parse(y)
    y.close()
    #xml.findall(".//a[@x]")[0]
    wms_url = xml.findtext(".//{http://www.opengis.net/tjs}URL")
    wms_layer = xml.findtext(".//{http://www.opengis.net/tjs}Parameter[@name='layerName']")

    return {'url': wms_url, 'layer': wms_layer}

@app.route('/js/<filename:path>')
def send_static(filename):
    return static_file(filename, root='js')

@app.route('/xml/<filename:path>')
def send_static(filename):
    return static_file(filename, root='xml')

@app.route('/', method='GET')
def upload_form():
    return """<!DOCTYPE HTML>
    <html>
        <head>
            <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap.min.css">
            <link rel="stylesheet" href="js/ol.css" type="text/css">
            <style>
                .map {
                    height: 400px;
                    width: 100%;
                }
            </style>
            <title>TJS Demonstrator</title>
        </head>
        <body>
            <div class="container">
                <div class="row">
		<div class="col-md-5">
                <h1>TJS Demonstrator <small>v0.1.1</small></h1><br><br>

                    <form role="form" class="form-horizontal" action="/" method="post" enctype="multipart/form-data">
		    <div class="form-group">
                      <label for="frameworkKey">Column name containing the key values</label>		                    
                      <input type="text" class="form-control" name="framework_key" />
                    </div>
                    <div class="form-group">
                      <label for="uploadFile">Select a file</label>
                      <input type="file" name="upload" />
                    </div>
                    <div class="form-group">
                      <label for="selectFramework">Select Framework</label>
                      <select class="form-control" id="selectFramework" name="framework_uri"></select>
                    </div>                  
                    <button type="submit" class="btn btn-primary">Submit</button>
                </form>
                </div>
                <div class="col-md-7" style="margin-top: 20px;">
                    <div id="map" class="map">
                    </div>
                </div>
            </div>
        </div>
<script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
<script src="http://cdnjs.cloudflare.com/ajax/libs/proj4js/1.1.0/proj4js-compressed.js"></script>
<script src="js/ol.js" type="text/javascript"></script>
<script src="js/tjs.js"></script>
</body>
<html>"""

@app.route('/', method='POST')
def do_upload():
    framework_key = request.forms.get('framework_key')
    framework_uri = request.forms.get('framework_uri')
    upload     = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    if ext not in ('.csv'):
        return 'Invalid fileformat. Must be csv'

    if ext == '.csv':

        # Setup XML elements
        root = etree.Element("GDAS", version="1.0", service="TJS", 
            capabilities="http://sis.agr.gc.ca/pls/meta/tjs_1x0_getcapabilities",
            xmlns="http://www.opengis.net/tjs/1.0")
	# Fetch corresponding framework metadata
        gdas_framework = root.append(get_dataset_meta(framework_uri))
        gdas_dataset = etree.SubElement(root[0], "Dataset")
        #gdas_dataset.append(etree.XML("""
        etree.SubElement(gdas_dataset, "DatasetURI").text = (cfg['gdas_uri_prefix'] + 
            str(uuid.uuid4()) + '/' + name)
        etree.SubElement(gdas_dataset, "Title").text = name
        etree.SubElement(gdas_dataset, "Organization").text = 'CBS'
        etree.SubElement(gdas_dataset, "Abstract").text = 'N_A'
        etree.SubElement(gdas_dataset, "ReferenceDate").text = 'N_A'
        etree.SubElement(gdas_dataset, "Version").text = '0'
        etree.SubElement(gdas_dataset, "Documentation").text = 'N_A'        

        gdas_columnset = etree.SubElement(gdas_dataset, "Columnset")
        gdas_rowset = etree.SubElement(gdas_dataset, "Rowset")

        # Use codecs to get a string object instead of bytes
        # latin1 works, but...
        reader = csv.DictReader(codecs.iterdecode(upload.file, 'latin1'), delimiter=cfg['csv_delimiter'])
        key_length = []
        #items = OrderedDict because order is pretty important
        try:
            value_attr = defaultdict(dict)
            for items in reader:
                gdas_row = etree.SubElement(gdas_rowset, "Row")
                # ensure the order of records
                items_ordered = OrderedDict(items)
                # extract framework key from set
                try:
                    items_ordered.move_to_end(framework_key)
                    # If no key exists, create 0-value - TODO
                    if items_ordered[framework_key] == '':
                        items_ordered[framework_key] = '0'
                except:
                    return 'Invalid framework-key'
                    break
                etree.SubElement(gdas_row, "K").text = str(items_ordered[framework_key])
                key_length.append(len(items_ordered[framework_key]))
                items_ordered.popitem()
                # handle Values
                for k, v in items_ordered.items():
                    # Create XML element
                    etree.SubElement(gdas_row, "V").text = str(v)
                    # Set the highest value for the length of an element (TODO: detect floats)
                    if k in value_attr and (len(str(v)) > value_attr[k]['length']): 
                        value_attr[k]['length'] = len(str(v))

                    if not k in value_attr:
                        value_attr[k] = {}
                        value_attr[k]['length'] = len(str(v))
                        value_attr[k]['type'] = type(v)

            # Create columns in columnset

            # Create frameworkkey
            gdas_framework_key = etree.SubElement(gdas_columnset, "FrameworkKey")
            gdas_framework_key.attrib['complete'] = 'true'
            gdas_framework_key.attrib['relationship'] = 'one'
            gdas_column = etree.SubElement(gdas_framework_key, "Column")
            gdas_column.attrib['name'] = framework_key
            gdas_column.attrib['type'] = 'http://www.w3.org/TR/xmlschema-2/#string'
            gdas_column.attrib['length'] = str(max(key_length))
            gdas_column.attrib['decimals'] = '0'

            gdas_attributes = etree.SubElement(gdas_columnset, "Attributes")
            for k, v in value_attr.items():
                gdas_column = etree.SubElement(gdas_attributes, "Column")
                gdas_column.attrib['name'] = str(k)
                gdas_column.attrib['type'] = 'http://www.w3.org/TR/xmlschema-2/#string'
                gdas_column.attrib['length'] = str(v['length'])
                gdas_column.attrib['decimals'] = '0'
                gdas_column.attrib['purpose'] = 'Attribute'
                # Add some default/dummy values
                etree.SubElement(gdas_column, "Title")
                etree.SubElement(gdas_column, "Abstract")
                etree.SubElement(gdas_column, "Documentation")   
                gdas_column.append(etree.XML('''<Values><Count><UOM><ShortForm/><LongForm/>
                                                </UOM></Count></Values>'''))
                etree.SubElement(gdas_column, "GetDataRequest")


        except csv.Error as e:
            print(e)

    # write xml to file
    f = open('xml/' + name + '.xml', 'wb')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()

    # Pass generated GDAS to TJS
    gdas_url = cfg['demonstrator_baseurl'] + '/xml/' + name + '.xml'
    
    resp = joindata(framework_uri, gdas_url)

    return """<!DOCTYPE HTML>
    <html>
        <head>
            <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap.min.css">
            <link rel="stylesheet" href="js/ol.css" type="text/css">
            <style>
                .map {
                    height: 400px;
                    width: 100%;
                }
            </style>
            <title>TJS Demonstrator</title>
        </head>
        <body>
            <div class="container">
                <div class="row">
        <div class="col-md-5">
                <h1>TJS Demonstrator <small>v0.1.1</small></h1><br><br>

                    <form role="form" class="form-horizontal" action="/" method="post" enctype="multipart/form-data">
            <div class="form-group">
                      <label for="frameworkKey">Column name containing the key values</label>                           
                      <input type="text" class="form-control" name="framework_key" />
                    </div>
                    <div class="form-group">
                      <label for="uploadFile">Select a file</label>
                      <input type="file" name="upload" />
                    </div>
                    <div class="form-group">
                      <label for="selectFramework">Select Framework</label>
                      <select class="form-control" id="selectFramework" name="framework_uri"></select>
                    </div>                  
                    <button type="submit" class="btn btn-primary">Submit</button>
                </form>
                </div>
                <div class="col-md-7" style="margin-top: 20px;">
                    <div id="map" class="map" data-wms-url='""" + str(resp['url']) + "' data-wms-layer='" + \
                    str(resp['layer']) + """'>
                    </div>
                    <div><p><strong>wms_url: </strong>""" + str(resp['url']) + ", <strong>wms_layer: </strong>" + str(resp['layer']) + """</p>
                    <p><strong>gdas_url: </strong>""" + gdas_url + """</p></div>

                </div>
            </div>
            <div class="row">
                <div class="col-md-12" id="info"></div>
            </div>
        </div>
<script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
<script src="http://cdnjs.cloudflare.com/ajax/libs/proj4js/1.1.0/proj4js-compressed.js"></script>
<script src="js/ol.js" type="text/javascript"></script>
<script src="js/tjs.js"></script>
</body>
<html>"""

@app.route('/tjs')
def reverse_tjs():

    url = cfg['tjs_baseurl'] + request.query_string

    # Fetch data
    try:
        y = urllib.request.urlopen(url)
        data = y.read()
        y.close()

        # force xml header
        response.content_type = 'text/xml'
        return data

    except:
        return "That didn't work out that well..."

# Use waitress to support multi-threading
run(app, host=cfg['demonstrator_host'], port=cfg['demonstrator_port'], reloader=True, server='waitress')