"""實際建立小型模型並匯出 GLB；輸出留在忽略的 .tools 內。"""
import bpy,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);root.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
p=root/'api-smoke.glb'
bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB')
assert p.read_bytes()[:4]==b'glTF'
assert p.stat().st_size>100
print('通過：Blender Python API、自動立方體建模、GLB 匯出。',bpy.app.version_string)
