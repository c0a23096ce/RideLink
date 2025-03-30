from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService
from api.services.RouteGenerateService import RouteGenerateService
import api.schemas.routes as route_schema
from fastapi.responses import HTMLResponse

router = APIRouter(
    prefix="/route",
    tags=["Route"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_model=route_schema.RouteGenerateResponse)
def generate_route(
    request: route_schema.RouteGenerateRequest,
    db: Session = Depends(get_db)
):
    """経路生成エンドポイント
    
    Args:
        request (RouteGenerateRequest): ドライバーと乗車者の位置情報、目的地
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).
    
    Returns:
        RouteGenerateResponse: 経路情報
    """
    # RouteGenerateServiceのインスタンスを作成
    route_service = RouteGenerateService(db=db)
    
    # 経路を生成
    route = route_service.route_generate(
        driver_location=request.driver_location,
        passenger_location=request.passenger_location,
        driver_destination=request.driver_destination,
        passenger_destination=request.passenger_destination
    )
    
    return route

@router.post("/plotroute", response_class=HTMLResponse)
def plot_route(
    request: route_schema.RouteGenerateRequest,
    db: Session = Depends(get_db)
):
    """経路を視覚化するエンドポイント
    
    Args:
        request (RouteGenerateRequest): ドライバーと乗車者の位置情報、目的地
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).
    
    Returns:
        HTMLResponse: 経路を地図上に表示したHTML
    """
    # RouteGenerateServiceのインスタンスを作成
    route_service = RouteGenerateService(db=db)
    
    # 経路を生成
    route = route_service.route_generate(
        driver_location=request.driver_location,
        passenger_location=request.passenger_location,
        driver_destination=request.driver_destination,
        passenger_destination=request.passenger_destination
    )
    
    # foliumを使ってマップを作成
    import folium
    import io
    
    # 中心位置を計算（ドライバーの現在位置を中心とする）
    center_lat, center_lon = request.driver_location
    
    # 地図を作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # マーカーを追加
    # ドライバーの現在位置
    folium.Marker(
        location=request.driver_location,
        popup='ドライバー現在位置',
        icon=folium.Icon(color='blue', icon='car', prefix='fa')
    ).add_to(m)
    
    # 乗客の現在位置
    folium.Marker(
        location=request.passenger_location,
        popup='乗客現在位置',
        icon=folium.Icon(color='green', icon='user', prefix='fa')
    ).add_to(m)
    
    # ドライバーの目的地
    folium.Marker(
        location=request.driver_destination,
        popup='ドライバー目的地',
        icon=folium.Icon(color='darkblue', icon='flag-checkered', prefix='fa')
    ).add_to(m)
    
    # 乗客の目的地
    folium.Marker(
        location=request.passenger_destination,
        popup='乗客目的地',
        icon=folium.Icon(color='darkgreen', icon='flag', prefix='fa')
    ).add_to(m)
    
    # ルートを描画
    colors = ['blue', 'green', 'red']
    segment_descriptions = {
        'to_passenger': 'ドライバーから乗客までの経路',
        'to_passenger_destination': '乗客から乗客目的地までの経路',
        'to_driver_destination': '乗客目的地からドライバー目的地までの経路'
    }
    
    for i, segment in enumerate(route['segments']):
        # ルートの座標を取得
        coordinates = segment['route']['geometry']['coordinates']
        # foliumは[lat, lon]の形式を期待するが、GeoJSONは[lon, lat]で返すため変換
        path = [[point[1], point[0]] for point in coordinates]
        
        # ルートを描画
        description = segment_descriptions.get(segment['type'], segment['type'])
        folium.PolyLine(
            locations=path,
            weight=5,
            color=colors[i % len(colors)],
            opacity=0.7,
            popup=description
        ).add_to(m)
    
    # HTMLとして出力
    output = io.BytesIO()
    m.save(output, close_file=False)
    output.seek(0)
    html_content = output.getvalue().decode()
    
    return HTMLResponse(content=html_content)

