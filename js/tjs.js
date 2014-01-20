Proj4js.defs["EPSG:28992"]="+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs";


var projection = ol.proj.configureProj4jsProjection({
  code: 'EPSG:28992',
  extent: [-285401.92,22598.08,595401.92,903401.92]
});



var brt = new ol.layer.Tile({
    source: new ol.source.TileWMS({
      url: 'http://geodata.nationaalgeoregister.nl/wmsc',
      attributions: [new ol.Attribution({
        html: '&copy; <a href="http://www.pdok.nl">BRT Achtergrondkaart</a>'
      })],
      params: {
      	'VERSION': '1.1.1',
        'LAYERS': 'brtachtergrondkaart',
        'FORMAT': 'image/png'
      },
      extent: extent
    })
  });

var extent = [-285401.92,22598.08,595401.92,903401.92];

var map = new ol.Map({
renderer: ol.RendererHint.CANVAS,
target: 'map',
layers: [brt],
  view: new ol.View2D({
    projection: projection,
    center: [155000, 463000],
    extent: extent,
    zoom: 2
})
});

map.on('singleclick', function(evt) {
  map.getFeatureInfo({
    pixel: evt.getPixel(),
    success: function(featureInfoByLayer) {
      document.getElementById('info').innerHTML = featureInfoByLayer.join('');
      console.log(featureInfoByLayer.join(''));
    }
  });
});


$(document).ready(function(){
  // Populate dropdown with available Frameworks in TJS
  $.ajax({
        type: "GET",
	url: "/tjs?service=TJS&version=1.0.0&request=DescribeFrameworks",
	dataType: "xml",
	success: function(xml) {

            $(xml).find('Framework').each(function(){

                var uri = $(this).find('FrameworkURI').text();
		var title = ($(this).find('Title').text());
		
		$('#selectFramework').append('<option value="' + uri + '">' + title + '</option>')
 
			});
    	}
	}); 

  	// Check if we should put a WMS on top of the basemap
  	if ($('#map').attr('data-wms-url')) {
  		var overlay = new ol.layer.Image({
    		source: new ol.source.ImageWMS({
      		url: $('#map').attr('data-wms-url'),
      		params: {'LAYERS': $('#map').attr('data-wms-layer')},
      		extent: extent
    		}),
    		transformFeatureInfo: function(features) {
    		return features.length > 0 ?
        	features[0].getId() + ': ' + features[0].get('name') : '&nbsp;';
  			}
  		});

  		map.addLayer(overlay);
  	}

});