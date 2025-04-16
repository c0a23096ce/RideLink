'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import RouteMap from './RouteMap';

export default function MatchNavigation() {
  const { match_id } = useParams();
  const [route, setRoute] = useState<GeoJSON.LineString | null>(null);

  useEffect(() => {
    if (!match_id) return;

    fetch(`/api/matches/${match_id}/route`)
      .then((res) => res.json())
      .then((data) => setRoute(data.route));
  }, [match_id]);

  return (
    <div>
      <h2>案内ルート</h2>
      {route ? <RouteMap route={route} /> : <p>ルート読み込み中...</p>}
    </div>
  );
}
