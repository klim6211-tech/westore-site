"""
위스토어 W 리본 심볼 — 원본 PNG(reference.jpg)를 보고 3D로 다시 만든다 (2026-09-03).

원본을 뜯어보면 **띠 세 덩어리가 앞뒤로 겹친 것**이다.
  A  왼쪽 바깥 획       (맨 뒤)   위·아래 끝이 둥글다
  B  가운데 V (획 2+3)  (중간)    아래 두 끝이 둥글고, 봉우리는 접혀서 뾰족하다
  C  오른쪽 바깥 획     (맨 앞)   위·아래 끝이 둥글다
왼쪽 접힘에서는 B 가 A 위에, 오른쪽 접힘에서는 C 가 B 위에 올라탄다.
색은 왼쪽 연파랑 → 오른쪽 진파랑, 한 장의 그라데이션 텍스처를 x 로 입힌다.

  blender -b -P make-w-symbol.py -- <출력폴더>
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.getcwd()
os.makedirs(out_dir, exist_ok=True)

# ── 1. 형태 (x = 가로, z = 세로, y = 두께 방향. 카메라는 -y 에서 +y 를 본다) ──
W_OUT = 0.50        # 바깥 획 폭 (원본이 가운데보다 굵다)
W_MID = 0.38        # 가운데 V 폭
THICK = 0.06        # 띠 두께
GAP = THICK * 1.15  # 덩어리 사이 앞뒤 간격
CAP_SEG = 28

TOP_L = Vector((-1.12, 0.92)); BOT_L = Vector((-0.48, -0.90))
PEAK  = Vector(( 0.04, 0.22))
BOT_R = Vector(( 0.44, -0.90)); TOP_R = Vector(( 1.12, 0.92))

def unit(v): return v / v.length

def cap_points(center, d, half, segs):
    """center 에서 진행방향 d 로 튀어나온 반원. 왼쪽 법선(+nrm) → 오른쪽(-nrm) 순."""
    nrm = Vector((-d.y, d.x))
    return [center + (nrm * math.cos(math.pi * k / segs) + d * math.sin(math.pi * k / segs)) * half
            for k in range(0, segs + 1)]

def stadium(p0, p1, half):
    """양 끝이 둥근 획. p0→p1."""
    d = unit(p1 - p0)
    pts = cap_points(p1, d, half, CAP_SEG)             # 끝 캡: left → right
    pts += cap_points(p0, -d, half, CAP_SEG)           # 시작 캡: right → left
    return pts

def vee(p0, p1, p2, half):
    """p0→p1(봉우리)→p2. 봉우리는 마이터(접힘), 양 끝은 둥글다."""
    d0 = unit(p1 - p0); d1 = unit(p2 - p1)
    n0 = Vector((-d0.y, d0.x)); n1 = Vector((-d1.y, d1.x))
    m = unit(n0 + n1); L = half / max(m.dot(n0), 0.3)
    pts = []
    pts += cap_points(p0, -d0, half, CAP_SEG)[::-1]    # 시작 캡 (left → right 순으로 뒤집음)
    # 왼쪽 변: p0.left → 봉우리 left → p2.left
    # 봉우리 바깥쪽은 뾰족한 가시가 아니라 둥글게 접힌다 — n0 에서 n1 까지 호
    a0 = math.atan2(n0.y, n0.x); a1 = math.atan2(n1.y, n1.x)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi      # 짧은 쪽으로 돈다 (길게 돌면 홈이 파인다)
    pts_left = [p1 + Vector((math.cos(a0 + da * k / 10), math.sin(a0 + da * k / 10))) * half
                for k in range(0, 11)]
    # 끝 캡
    pts_end = cap_points(p2, d1, half, CAP_SEG)
    pts_right = [p1 - m * L]
    # 순서: 시작캡(right→left) ... 그냥 명시적으로 조립
    start_cap = cap_points(p0, -d0, half, CAP_SEG)     # 시작점에서 뒤로: left(-d0 기준) → right
    # 시작캡의 '왼쪽'은 -d0 기준이라 실제로는 p0 의 오른쪽. 순서를 맞추기 위해 직접 짠다:
    outline = []
    outline += [p0 + n0 * half]
    outline += pts_left
    outline += [p2 + n1 * half]
    outline += pts_end[1:-1]
    outline += [p2 - n1 * half]
    outline += pts_right
    outline += [p0 - n0 * half]
    outline += [p for p in start_cap[1:-1]]
    return outline

def make_slab(name, outline2d, y_offset, thick):
    mesh = bpy.data.meshes.new(name); obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    verts = [bm.verts.new((p.x, 0.0, p.y)) for p in outline2d]
    f = bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(mesh); bm.free()
    sol = obj.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = thick; sol.offset = 0.0; sol.use_even_offset = True
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = thick * 0.30; bev.segments = 4; bev.limit_method = "ANGLE"; bev.angle_limit = math.radians(40)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Solidify")
    bpy.ops.object.modifier_apply(modifier="Bevel")
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    obj.location.y = y_offset
    obj.select_set(False)
    return obj

bpy.ops.wm.read_factory_settings(use_empty=True)
A = make_slab("W_left",  stadium(TOP_L, BOT_L, W_OUT / 2),    +GAP, THICK)   # 뒤 (+y 가 카메라에서 멀다)
B = make_slab("W_mid",   vee(BOT_L + Vector((0.02, -0.05)), PEAK, BOT_R + Vector((-0.02, -0.05)), W_MID / 2), 0.0, THICK)
C = make_slab("W_right", stadium(BOT_R, TOP_R, W_OUT / 2),    -GAP, THICK)   # 앞
slabs = [A, B, C]

# ── 2. 색: x 로 그라데이션 텍스처 + UV ─────────────────────
C0 = (0.58, 0.76, 0.99)   # 왼쪽 연파랑 (#94C2FC)
C1 = (0.03, 0.06, 0.78)   # 오른쪽 진파랑 (AgX 가 채도를 눌러서 더 진하게 준다)
xmin = min(v.co.x for o in slabs for v in o.data.vertices)
xmax = max(v.co.x for o in slabs for v in o.data.vertices)

img = bpy.data.images.new("WGradient", 512, 4, alpha=False)
px = []
for _ in range(4):
    for x in range(512):
        t = (x / 511) ** 1.1
        px += [C0[0] + (C1[0]-C0[0])*t, C0[1] + (C1[1]-C0[1])*t, C0[2] + (C1[2]-C0[2])*t, 1.0]
img.pixels = px
img.filepath_raw = os.path.join(out_dir, "w-gradient.png"); img.file_format = "PNG"; img.save()

mat = bpy.data.materials.new("WRibbon"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Linear"
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.28
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["Coat Weight"].default_value = 0.7
bsdf.inputs["Coat Roughness"].default_value = 0.10

for o in slabs:
    mesh = o.data
    mesh.uv_layers.new(name="UVMap"); uv = mesh.uv_layers.active.data
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index]
            uv[li].uv = ((v.co.x - xmin) / (xmax - xmin), 0.5)
    mesh.materials.append(mat)

# 하나로 합쳐서 내보낸다 (뷰어에서 다루기 쉽게). 원본 세 덩어리는 .blend 에 남는다.
for o in slabs: o.select_set(True)
bpy.context.view_layer.objects.active = B
bpy.ops.object.duplicate()
bpy.ops.object.join()
joined = bpy.context.active_object; joined.name = "WSymbol"
for o in slabs: o.select_set(False); o.hide_render = True; o.hide_set(True)

# ── 3. GLB ────────────────────────────────────────────────
glb = os.path.join(out_dir, "w-symbol.glb")
joined.select_set(True)
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_apply=True, use_selection=True,
                          export_yup=True, export_materials="EXPORT", export_normals=True, export_texcoords=True)
print("GLB:", glb, os.path.getsize(glb), "bytes")

# ── 4. 렌더 ───────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = "CYCLES"; scene.cycles.samples = 128; scene.cycles.device = "CPU"
scene.render.resolution_x = 1000; scene.render.resolution_y = 1000
scene.render.film_transparent = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"

world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.9, 0.93, 1.0, 1); bg.inputs[1].default_value = 0.35

def light(name, loc, energy, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light("Key",  (-2.5, -4.0,  3.5), 260, 3.0)
light("Fill", ( 3.0, -3.5, -0.5),  90, 4.0)
light("Rim",  ( 1.0,  3.0,  2.5), 160, 2.0)

cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 75
cam = bpy.data.objects.new("Cam", cam_data); bpy.context.collection.objects.link(cam); scene.camera = cam

def shoot(name, loc):
    cam.location = loc
    cam.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Z").to_euler()
    scene.render.filepath = os.path.join(out_dir, name)
    bpy.ops.render.render(write_still=True); print("RENDER:", scene.render.filepath)

import numpy as np
def on_white(src, dst):
    im = bpy.data.images.load(src); w, h = im.size
    a = np.array(im.pixels[:]).reshape(h, w, 4)
    rgb = a[..., :3] * a[..., 3:4] + (1 - a[..., 3:4])
    out = bpy.data.images.new("tmp", w, h, alpha=False)
    out.pixels = np.concatenate([rgb, np.ones((h, w, 1))], axis=2).ravel().tolist()
    out.filepath_raw = dst; out.file_format = "PNG"; out.save()
shoot("w-front-transparent.png", (0.0, -6.8, 0.0))
on_white(os.path.join(out_dir, "w-front-transparent.png"), os.path.join(out_dir, "w-front.png"))
shoot("w-angle-transparent.png", (-2.4, -6.0, 1.7))
on_white(os.path.join(out_dir, "w-angle-transparent.png"), os.path.join(out_dir, "w-angle.png"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "w-symbol.blend"))
print("DONE")
