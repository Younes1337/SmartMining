import proj4 from 'proj4';

// Define the UTM zone for your coordinates (Northwest Canada is typically UTM zone 9N to 11N)
// You may need to adjust the zone based on your specific location
const UTM_ZONE = '11N'; 
const UTM_SRID = `EPSG:326${UTM_ZONE.match(/\d+/)[0]}`;  // Now resolves to EPSG:32611

// WGS84 projection (standard lat/lon)
proj4.defs('EPSG:4326', '+proj=longlat +datum=WGS84 +no_defs');

/**
 * Convert UTM coordinates to WGS84 (latitude/longitude)
 * @param {number} easting - UTM easting (X coordinate)
 * @param {number} northing - UTM northing (Y coordinate)
 * @returns {[number, number]} - [longitude, latitude]
 */
export function utmToLatLng(easting, northing) {
  try {
    // Convert UTM to WGS84 (lat/lon)
    const [longitude, latitude] = proj4(UTM_SRID, 'EPSG:4326', [easting, northing]);
    return [longitude, latitude];
  } catch (error) {
    console.error('Error converting UTM to Lat/Lng:', error);
    return [null, null];
  }
}

/**
 * Convert WGS84 (latitude/longitude) to UTM
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {{easting: number, northing: number, zone: string}} - UTM coordinates
 */
export function latLngToUtm(lat, lng) {
  try {
    // Convert WGS84 to UTM
    const [easting, northing] = proj4('EPSG:4326', UTM_SRID, [lng, lat]);
    return { easting, northing, zone: UTM_ZONE };
  } catch (error) {
    console.error('Error converting Lat/Lng to UTM:', error);
    return { easting: null, northing: null, zone: UTM_ZONE };
  }
}
