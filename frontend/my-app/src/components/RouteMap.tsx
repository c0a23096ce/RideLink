'use client';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useEffect, useRef } from 'react';

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_API_KEY || '';

interface RouteMapProps {
  route: GeoJSON.LineString; // ルートのGeoJSON
}

export default function RouteMap({ route }: RouteMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current || !route) return;

    if (mapRef.current) {
      mapRef.current.remove(); // リセット
    }

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: route.coordinates[0],
      zoom: 13
    });

    map.on('load', () => {
      map.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: route
        }
      });

      map.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: {
          'line-cap': 'round',
          'line-join': 'round'
        },
        paint: {
          'line-color': '#007cbf',
          'line-width': 5
        }
      });

      // ルート全体を表示するようにfitBounds
      const bounds = new mapboxgl.LngLatBounds();
      route.coordinates.forEach(coord => bounds.extend(coord));
      map.fitBounds(bounds, { padding: 60 });
    });

    mapRef.current = map;
  }, [route]);

  return <div ref={mapContainer} style={{ width: '100%', height: '500px' }} />;
}
