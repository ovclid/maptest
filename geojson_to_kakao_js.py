#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
폴더 내 GeoJSON(.txt / .json) 파일들을 읽어
카카오맵에서 폴리곤 + 마커용으로 쓸 수 있는 JS 파일을 생성합니다.

사용법:
  python geojson_to_kakao_js.py [입력폴더] [출력JS파일]

예시:
  python geojson_to_kakao_js.py ./data ./kakao_map_data.js
  python geojson_to_kakao_js.py          # 기본: 현재 폴더 → kakao_map_data.js
"""

import json
import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


def make_address(props: dict) -> str:
    """properties에서 사람이 읽을 수 있는 주소 문자열 생성"""
    area1 = props.get("area1", "").replace("__", " ").strip()
    bon = props.get("bon")
    bu = props.get("bu", 0)

    if bon is None:
        return area1 or "주소 정보 없음"

    if bu and int(bu) != 0:
        return f"{area1} {bon}-{bu}".strip()
    return f"{area1} {bon}".strip()


def calc_centroid(coords: List[List[float]]) -> Tuple[float, float]:
    """
    링 좌표(GeoJSON [lng, lat])의 대략적인 중심점 (lat, lng) 반환.
    단순 평균 사용 (복잡한 폴리곤에도 충분히 실용적).
    """
    if not coords:
        return 0.0, 0.0
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


def extract_feature(feature: dict, filename: str) -> Optional[Dict[str, Any]]:
    """하나의 Feature를 카카오맵용 객체로 변환"""
    geom = feature.get("geometry")
    if not geom:
        return None

    props = feature.get("properties") or {}
    geom_type = geom.get("type")
    coordinates = geom.get("coordinates")

    if not coordinates:
        return None

    # MultiPolygon / Polygon 모두 처리
    # GeoJSON: MultiPolygon → [ polygon, ... ]
    #          Polygon     → [ ring, ... ]
    polygons = []
    if geom_type == "MultiPolygon":
        polygons = coordinates
    elif geom_type == "Polygon":
        polygons = [coordinates]
    else:
        print(f"  [경고] 지원하지 않는 geometry type: {geom_type} ({filename})")
        return None

    # 카카오맵용 path: 각 링을 [lat, lng] 순서로 변환
    # paths = [ [ [lat,lng], [lat,lng], ... ],  ... ]  (outer + holes)
    paths = []
    all_points_for_center = []

    for polygon in polygons:
        for ring in polygon:
            kakao_ring = []
            for pt in ring:
                if len(pt) < 2:
                    continue
                lng, lat = float(pt[0]), float(pt[1])
                kakao_ring.append([lat, lng])          # 카카오 = [lat, lng]
                all_points_for_center.append([lng, lat])  # 중심 계산용 [lng, lat]
            if kakao_ring:
                paths.append(kakao_ring)

    if not paths:
        return None

    center_lat, center_lng = calc_centroid(all_points_for_center)
    address = make_address(props)

    # 파일명에서 이름 추출 (확장자 제거)
    name = Path(filename).stem

    return {
        "name": name,
        "address": address,
        "pnucode": props.get("pnucode", ""),
        "admcode": props.get("admcode", ""),
        "jimok": props.get("jimok", ""),
        "bon": props.get("bon"),
        "bu": props.get("bu", 0),
        "area1": props.get("area1", ""),
        "center": {"lat": round(center_lat, 8), "lng": round(center_lng, 8)},
        "paths": paths,          # [[lat,lng], ...] 리스트의 리스트
    }


def process_file(filepath: str) -> List[Dict[str, Any]]:
    """한 파일을 읽어 Feature 리스트 반환"""
    results = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [오류] 파일 읽기 실패: {filepath} → {e}")
        return results

    features = data.get("features") if isinstance(data, dict) else None
    if not features:
        # FeatureCollection이 아니라 단일 Feature인 경우도 대응
        if data.get("type") == "Feature":
            features = [data]
        else:
            print(f"  [경고] features 없음: {filepath}")
            return results

    filename = os.path.basename(filepath)
    for feat in features:
        item = extract_feature(feat, filename)
        if item:
            results.append(item)

    return results


def generate_js(data_list: List[Dict[str, Any]], output_path: str) -> None:
    """JS 파일 생성"""
    # JSON을 그대로 넣고 앞에 const 선언만 붙임
    json_str = json.dumps(data_list, ensure_ascii=False, indent=2)

    js_content = f"""/**
 * 카카오맵용 구역 데이터
 * 자동 생성 파일 – 수정하지 마세요.
 * 생성 스크립트: geojson_to_kakao_js.py
 *
 * 사용 예시 (HTML에서):
 *   <script src="kakao_map_data.js"></script>
 *   <script>
 *     // mapData 배열 사용
 *     mapData.forEach(item => {{
 *       const path = item.paths[0].map(p => new kakao.maps.LatLng(p[0], p[1]));
 *       const polygon = new kakao.maps.Polygon({{
 *         path: path,
 *         strokeWeight: 2,
 *         strokeColor: '#004c80',
 *         strokeOpacity: 0.8,
 *         fillColor: '#00a0e9',
 *         fillOpacity: 0.3
 *       }});
 *       polygon.setMap(map);
 *
 *       const marker = new kakao.maps.Marker({{
 *         position: new kakao.maps.LatLng(item.center.lat, item.center.lng)
 *       }});
 *       marker.setMap(map);
 *
 *       const infowindow = new kakao.maps.InfoWindow({{
 *         content: `<div style="padding:5px;font-size:12px;">${{item.address}}</div>`
 *       }});
 *       kakao.maps.event.addListener(marker, 'click', () => infowindow.open(map, marker));
 *     }});
 *   </script>
 */
const mapData = {json_str};

// 브라우저/모듈 양쪽에서 사용 가능하도록
if (typeof module !== 'undefined' && module.exports) {{
  module.exports = mapData;
}}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\n✅ JS 파일 생성 완료: {output_path}")
    print(f"   총 {len(data_list)}개 구역")


def main():
    # 인자 처리
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_js = sys.argv[2] if len(sys.argv) > 2 else "kakao_map_data.js"

    input_dir = os.path.abspath(input_dir)
    if not os.path.isdir(input_dir):
        print(f"❌ 입력 폴더가 존재하지 않습니다: {input_dir}")
        sys.exit(1)

    # .txt / .json 파일 검색
    patterns = ["*.txt", "*.json", "*.geojson"]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(input_dir, pat)))
    files = sorted(set(files))

    if not files:
        print(f"❌ '{input_dir}' 폴더에 .txt / .json / .geojson 파일이 없습니다.")
        sys.exit(1)

    print(f"📂 입력 폴더: {input_dir}")
    print(f"📄 발견된 파일: {len(files)}개\n")

    all_data = []
    for fp in files:
        print(f"  읽는 중: {os.path.basename(fp)}")
        items = process_file(fp)
        if items:
            print(f"    → {len(items)}개 Feature 추출")
            all_data.extend(items)
        else:
            print(f"    → 추출된 Feature 없음")

    if not all_data:
        print("\n❌ 변환할 데이터가 없습니다.")
        sys.exit(1)

    generate_js(all_data, output_js)

    # 간단 미리보기
    print("\n--- 미리보기 (첫 번째 구역) ---")
    first = all_data[0]
    print(f"  이름    : {first['name']}")
    print(f"  주소    : {first['address']}")
    print(f"  중심점  : lat={first['center']['lat']}, lng={first['center']['lng']}")
    print(f"  경로 수 : {len(first['paths'])}개 링, 첫 링 좌표 수={len(first['paths'][0])}")


if __name__ == "__main__":
    main()
