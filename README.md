# 카카오맵 구역 표시 (순수 JavaScript)

`data/` 폴더의 GeoJSON(`.txt`) 파일을 **Python 없이** 브라우저에서 직접 읽어  
카카오맵에 폴리곤 + 주소 마커로 표시합니다.

## 폴더 구조

```
kakao-map-zones/
├── index.html          ← 지도 페이지 (이것만 열면 됩니다)
├── data/               ← 원본 GeoJSON .txt 파일들
│   └── 대평동 668.txt
└── README.md
```

> `js/map_data.js`, `geojson_to_kakao_js.py` 는 더 이상 필요하지 않습니다.  
> (이전 방식이 필요하면 그대로 두셔도 됩니다.)

## 사용 방법

### 1. 카카오맵 API 키

1. [카카오 개발자](https://developers.kakao.com/) → 앱 등록 → **JavaScript 키** 복사
2. `index.html`에서 아래를 찾아 키를 넣습니다:

```html
<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey=YOUR_KAKAO_APP_KEY&autoload=false"></script>
```

GitHub Pages 사용 시 카카오 콘솔 **플랫폼 → Web**에  
`https://아이디.github.io` 도메인을 등록하세요.

### 2. 구역 파일 추가 (두 가지 방법)

#### 방법 A – data/ 폴더 + 파일 목록 지정 (권장, GitHub용)

1. `.txt` 파일을 `data/` 폴더에 넣습니다.
2. `index.html` 안의 `DATA_FILES` 배열에 파일명을 추가합니다:

```js
const DATA_FILES = [
  '대평동 668.txt',
  '다른구역 123.txt',   // ← 추가
];
```

3. 페이지를 새로고침하면 자동으로 로드됩니다.

> 브라우저 보안 정책 때문에 폴더 안 파일 목록을 **자동으로** 가져올 수 없습니다.  
> 파일명만 배열에 적어 주면 됩니다.

#### 방법 B – “파일 추가” 버튼 (로컬에서 바로 확인)

상단 **파일 추가** 버튼으로 `.txt` / `.json` 파일을 여러 개 선택하면  
서버에 올리지 않고도 바로 지도에 표시됩니다.

### 3. 로컬에서 보기

`file://` 로 열면 `fetch`가 막힐 수 있으므로 간단한 서버를 권장합니다.

```bash
cd kakao-map-zones
python -m http.server 8080
# http://localhost:8080
```

### 4. GitHub Pages 배포

```bash
git init
git add .
git commit -m "카카오맵 구역 지도 (순수 JS)"
git branch -M main
git remote add origin https://github.com/아이디/저장소이름.git
git push -u origin main
```

Settings → Pages → Source: `main` 브랜치

## 기능

- `data/` 의 txt를 fetch → GeoJSON 파싱 → 폴리곤/마커 표시
- 마커·폴리곤 클릭 시 주소 인포윈도우
- 우측 목록에서 구역 선택 → 이동
- 전체 보기 / 로컬 파일 추가

## 원본 파일 형식

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": { "type": "MultiPolygon", "coordinates": [ ... ] },
    "properties": {
      "area1": "세종특별자치시__대평동",
      "bon": 668,
      "bu": 0,
      "jimok": "일반"
    }
  }]
}
```
