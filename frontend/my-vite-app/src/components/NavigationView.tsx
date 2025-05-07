// src/components/NavigationView.tsx
import { Box, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import apiClient from '../lib/apiClient';
import mapboxgl from 'mapbox-gl';
import MapboxLanguage from '@mapbox/mapbox-gl-language';
import 'mapbox-gl/dist/mapbox-gl.css';


const mapboxApiKey = import.meta.env.VITE_MAPBOX_API_KEY;

if (typeof mapboxApiKey !== 'string' || mapboxApiKey.trim() === '') {
  throw new Error('Mapbox APIキーが正しく設定されていません。');
}
mapboxgl.setRTLTextPlugin(null, null, false);
mapboxgl.accessToken = mapboxApiKey;

export default function NavigationView() {
  const { match_id } = useParams();
  const [routeData, setRouteData] = useState<any>(null);
  const [usersData, setUsersData] = useState<any[]>([]);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const [alerted, setAlerted] = useState(false);

  // ユーザーごとに色を割り当てる
  const userColors: { [key: number]: string } = {};
  const colorPalette = ['red', 'green', 'orange', 'purple', 'pink', 'brown', 'gray'];

  useEffect(() => {
    const fetchRoute = async () => {
      if (!match_id) return;
      try {
        const res = await apiClient.get(`/matches/${match_id}/route`);
        console.log('取得したデータ:', res.data);
        setRouteData(res.data.route);
        setUsersData(res.data.users);
      } catch (err) {
        console.error('ルート取得失敗:', err);
      }
    };
    fetchRoute();
  }, [match_id]);

  useEffect(() => {
    if (!routeData || !mapContainerRef.current) return;

    const routeCoordinates = routeData.routes[0].geometry.coordinates;

    const mapInstance = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: routeCoordinates[0],
      zoom: 12,
    });

    const language = new MapboxLanguage({
      defaultLanguage: 'ja',
    });
    mapInstance.addControl(language);

    mapInstance.on('load', () => {
      const geojson = {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: {},
            geometry: routeData.routes[0].geometry,
          },
        ],
      };

      mapInstance.addSource('route', {
        type: 'geojson',
        data: geojson,
      });

      mapInstance.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#3b9ddd',
          'line-width': 6,
        },
      });

      // 🚩 ユーザーごとにピンを立てる
      usersData.forEach((user, index) => {
        let color = 'gray';
        if (user.role === 'driver') {
          color = 'blue'; // driver は常に青
        } else {
          // 既に色が決まっていなければ割り当て
          if (!userColors[user.user_id]) {
            userColors[user.user_id] = colorPalette[index % colorPalette.length];
          }
          color = userColors[user.user_id];
        }

        // 緯度経度の順番を確認：[lng, lat] にする
        const startLngLat = [user.start[1], user.start[0]];
        const destLngLat = [user.destination[1], user.destination[0]];
        // console.log('ユーザーの開始地点:', startLngLat);
        // console.log('ユーザーの目的地:', destLngLat);
        // 開始地点
        new mapboxgl.Marker({
          color: color,
        })
          .setLngLat(startLngLat)
          .addTo(mapInstance);

        // 目的地
        new mapboxgl.Marker({
          color: color,
        })
          .setLngLat(destLngLat)
          .addTo(mapInstance);
      });
    });

    setMap(mapInstance);

    return () => {
      mapInstance.remove();
    };
  }, [routeData, usersData]);

  useEffect(() => {
    if (!map || !routeData) return;

    const routeCoordinates = routeData.routes[0].geometry.coordinates;

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        console.log('現在地:', latitude, longitude);

        const lngLat = [longitude, latitude] as [number, number];

        if (!markerRef.current) {
          markerRef.current = new mapboxgl.Marker({ color: 'red' })
            .setLngLat(lngLat)
            .addTo(map);
        } else {
          markerRef.current.setLngLat(lngLat);
        }

        // 距離チェック
        const minDistance = routeCoordinates.reduce((min: number, coord: [number, number]) => {
          const distance = getDistanceFromLatLonInMeters(
            latitude,
            longitude,
            coord[1],
            coord[0]
          );
          return Math.min(min, distance);
        }, Infinity);

        console.log('ルートまでの最短距離:', minDistance, 'm');

        if (minDistance > 100 && !alerted) {
          alert('⚠️ ルートから外れています！');
          setAlerted(true);
        }
      },
      (error) => {
        console.error('位置情報取得エラー:', error);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 5000,
      }
    );

    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, [map, routeData, alerted]);

  if (!routeData) {
    return (
      <Box flex={1} display="flex" justifyContent="center" alignItems="center">
        <Typography>ルート情報を読み込み中...</Typography>
      </Box>
    );
  }

  return (
    <Box
      ref={mapContainerRef}
      flex={1}
      height="100%"
      width="100%"
      position={'relative'}
    />
  );
}

// ヘルパー関数
function getDistanceFromLatLonInMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
) {
  const R = 6371e3;
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) *
    Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}



