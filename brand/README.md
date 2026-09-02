# 브랜드 3D 심볼 (2026-09-03)

- `reference.jpg` — 청림님이 주신 원본(유일한 소스, PNG뿐).
- `make-w-symbol.py` — 원본을 보고 리본 W를 코드로 모델링. `blender -b -P make-w-symbol.py -- out`
- `out/w-symbol.glb` — 웹(three.js / React Three Fiber)용 모델. 텍스처(그라데이션) 내장, 약 90KB.
- `out/w-symbol.blend` — 블렌더 원본. 세 덩어리(왼쪽 획 / 가운데 V / 오른쪽 획)가 따로 있다.
- `out/w-front.png` `out/w-angle.png` — 사이클스 렌더 미리보기. `*-transparent.png` 는 투명 배경.

블렌더 5.0.1 (apt) + python3-numpy 가 이 컴퓨터에 깔려 있다.
