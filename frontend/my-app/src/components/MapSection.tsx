// components/MapSection.tsx
'use client';

import { MapContainer, Marker, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

function ChangeMapCenter({ position }: { position: [number, number] }) {
  const map = useMap();
  map.setView(position, 13);
  return null;
}

export default function MapSection({
  origin,
  destination,
  focus,
}: {
  origin: [number, number] | null;
  destination: [number, number] | null;
  focus: 'origin' | 'destination';
}) {
  const center = destination || origin || [35.6895, 139.6917];
  return (
    <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {origin && <Marker position={origin} />}
      {destination && <Marker position={destination} />}
      {focus === 'origin' && origin && <ChangeMapCenter position={origin} />}
      {focus === 'destination' && destination && <ChangeMapCenter position={destination} />}
    </MapContainer>
  );
}