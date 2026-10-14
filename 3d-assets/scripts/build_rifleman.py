"""Papa-Lab：免費、可重複執行的 Q 版步槍兵建模／骨架／動畫／GLB 匯出。"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Euler
OUT = Path(__file__).resolve().parents[1] / 'models' / 'rifleman'
if '--' in sys.argv:
    args=sys.argv[sys.argv.index('--')+1:]
    if args: OUT=Path(args[0]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for action in list(bpy.data.actions): bpy.data.actions.remove(action)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.fps=24
M={}
for name,color in {'Uniform':(0.19,.45,.38),'Helmet':(.22,.52,.45),'Vest':(.14,.27,.30),'Skin':(.96,.70,.46),'Boots':(.12,.20,.23),'Rifle':(.20,.28,.32),'Accent':(1,.72,.27),'Eyes':(.07,.11,.13),'White':(.93,.95,.87)}.items():
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
    p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.82
    M[name]=mat
parts=[]
def bind(obj,bone,material):
    obj.data.materials.append(M[material]);group=obj.vertex_groups.new(name=bone);group.add(list(range(len(obj.data.vertices))),1,'REPLACE');parts.append(obj)
    return obj

def box(name,loc,scale,bone,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('柔和低面數邊緣','BEVEL');mod.width=bevel;mod.segments=1
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return bind(o,bone,mat)
def sphere(name,loc,scale,bone,mat,segments=12,rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return bind(o,bone,mat)
def segment(name,a,b,r,bone,mat,vertices=8):
    a,b=Vector(a),Vector(b);v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=v.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return bind(o,bone,mat)
# 身高約 1.95m；Blender +Z 向上、+Y 向前，腳底中心是 (0,0,0)。
box('圓角制服上身',(0,0,1.15),(.50,.32,.49),'Spine','Uniform',.055)
box('防護背心',(0,.17,1.16),(.47,.12,.35),'Spine','Vest',.035)
for x in [-.13,.13]: box('裝備袋',(x,.25,1.06),(.12,.065,.11),'Spine','Uniform',.012)
box('腰帶',(0,0,.86),(.51,.34,.09),'Pelvis','Vest',.018)
box('金色腰扣',(0,.19,.86),(.085,.025,.055),'Pelvis','Accent',.008)
box('小背包',(0,-.22,1.17),(.31,.16,.33),'Spine','Vest',.045)
sphere('大頭',(0,.01,1.59),(.31,.285,.29),'Head','Skin')
# 半球頭盔：沒有遮住臉的下半球。
verts=[(0,.015,1.95)];faces=[];n=16
for r in range(1,5):
    phi=(math.pi/2)*r/4
    for i in range(n):
        th=2*math.pi*i/n;verts.append((.345*math.sin(phi)*math.cos(th),.015+.315*math.sin(phi)*math.sin(th),1.66+.29*math.cos(phi)))
for i in range(n):faces.append((0,1+i,1+(i+1)%n))
for r in range(3):
    for i in range(n): faces.append((1+r*n+i,1+r*n+(i+1)%n,1+(r+1)*n+(i+1)%n,1+(r+1)*n+i))
mesh=bpy.data.meshes.new('HelmetCap');mesh.from_pydata(verts,[],faces);mesh.update();cap=bpy.data.objects.new('頭盔半球',mesh);scene.collection.objects.link(cap);bind(cap,'Head','Helmet')
box('頭盔帽沿',(0,.035,1.67),(.72,.65,.07),'Head','Helmet',.018)
box('頭盔徽章',(0,.363,1.75),(.08,.025,.08),'Head','Accent',.01)
for x in [-.112,.112]:
    sphere('黑眼睛',(x,.272,1.585),(.027,.018,.037),'Head','Eyes',8,4)
    sphere('眼睛高光',(x-.006,.289,1.601),(.008,.006,.009),'Head','White',6,3)
sphere('鼻子',(0,.297,1.535),(.045,.038,.043),'Head','Skin',8,4)
box('微笑',(0,.271,1.458),(.084,.015,.016),'Head','Vest',.005)
# 下肢：每塊網格只跟隨一節骨頭，簡單機械式卡通骨架。
for side,x in [('L',-.15),('R',.15)]:
    segment('大腿'+side,(x,0,.83),(x,0,.48),.108,'Thigh.'+side,'Uniform')
    segment('小腿'+side,(x,0,.48),(x,0,.16),.083,'Shin.'+side,'Uniform')
    box('靴子'+side,(x,.07,.095),(.23,.34,.19),'Foot.'+side,'Boots',.03)
    box('鞋底'+side,(x,.07,.025),(.235,.35,.05),'Foot.'+side,'Vest',.008)
# 雙手持槍：左手托護木、右手握握把；槍跟隨右手。
JOINTS={}
for side,sh,el,hand in [('L',(-.29,0,1.32),(-.20,.34,1.06),(.12,.68,1.16)),('R',(.29,0,1.32),(.34,.24,1.1),(.13,.43,1.16))]:
    JOINTS[side]=(sh,el,hand)
    sphere('肩膀'+side,sh,(.135,.13,.135),'UpperArm.'+side,'Uniform',8,4)
    segment('上臂'+side,sh,el,.093,'UpperArm.'+side,'Uniform')
    segment('前臂'+side,el,hand,.075,'Forearm.'+side,'Uniform')
    sphere('手套'+side,hand,(.086,.09,.085),'Hand.'+side,'Skin',8,4)
# 朝 +Y 的略放大卡通步槍；沒有發光特效或射出物，留給遊戲邏輯。
box('步槍機匣',(.12,.53,1.20),(.14,.32,.13),'Weapon','Rifle',.018)
box('槍托',(.12,.30,1.20),(.13,.21,.14),'Weapon','Vest',.025)
box('護木',(.12,.76,1.20),(.115,.22,.10),'Weapon','Helmet',.012)
segment('槍管',(.12,.86,1.21),(.12,1.05,1.21),.026,'Weapon','Rifle')
segment('槍口',(.12,1.02,1.21),(.12,1.09,1.21),.040,'Weapon','Vest')
box('彈匣',(.12,.59,1.09),(.085,.13,.15),'Weapon','Vest',.012)
box('瞄具',(.12,.58,1.30),(.045,.12,.045),'Weapon','Accent',.007)
box('握把',(.12,.41,1.095),(.065,.075,.115),'Weapon','Vest',.008)
# 合併為一個 SkinnedMesh，材質仍保留語意名稱，便於未來換色。
bpy.ops.object.select_all(action='DESELECT')
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='RiflemanMesh'
for layer in list(body.data.uv_layers):body.data.uv_layers.remove(layer)
# 每面原材質轉成頂點色，合併為一種材質：每名士兵只需要一個繪圖呼叫。
colors=body.data.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
for poly in body.data.polygons:
    color=body.data.materials[poly.material_index].diffuse_color
    for index in poly.loop_indices: colors.data[index].color=color
unified=bpy.data.materials.new('RiflemanVertexColors');unified.use_nodes=True
shader=unified.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.82
vertex=unified.node_tree.nodes.new('ShaderNodeVertexColor');vertex.layer_name='Color'
unified.node_tree.links.new(vertex.outputs['Color'],shader.inputs['Base Color'])
body.data.materials.clear();body.data.materials.append(unified)
for poly in body.data.polygons:poly.material_index=0
scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
arm_data=bpy.data.armatures.new('RiflemanSkeleton');rig=bpy.data.objects.new('Rifleman',arm_data);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;body.select_set(False);rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=arm_data.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=arm_data.edit_bones[parent]
    return b
bone('Root',(0,0,0),(0,0,.2));bone('Pelvis',(0,0,.83),(0,0,1.02),'Root');bone('Spine',(0,0,1.02),(0,0,1.39),'Pelvis');bone('Head',(0,0,1.40),(0,0,1.9),'Spine')
for side,x in [('L',-.15),('R',.15)]:
    bone('Thigh.'+side,(x,0,.83),(x,0,.48),'Pelvis');bone('Shin.'+side,(x,0,.48),(x,0,.16),'Thigh.'+side);bone('Foot.'+side,(x,0,.16),(x,.25,.16),'Shin.'+side)
for side,(sh,el,hand) in JOINTS.items():
    bone('UpperArm.'+side,sh,el,'Spine');bone('Forearm.'+side,el,hand,'UpperArm.'+side);bone('Hand.'+side,hand,Vector(hand)+Vector((0,.12,0)),'Forearm.'+side)
bone('Weapon',(.12,.43,1.20),(.12,.95,1.20),'Hand.R')
bpy.ops.object.mode_set(mode='OBJECT');mod=body.modifiers.new('低負載骨架','ARMATURE');mod.object=rig
rig['asset']='Papa-Lab Rifleman';rig['forward']='Blender +Y / glTF -Z';rig['origin']='腳底中心';rig['style']='low-poly chibi'
# 將以世界軸定義的關節轉動換算成每根骨頭的局部座標。
def pose(name,angles=(0,0,0),offset=(0,0,0)):
    b=rig.pose.bones[name];basis=b.bone.matrix_local.to_3x3();q=Euler(angles,'XYZ').to_matrix();b.rotation_mode='QUATERNION';b.rotation_quaternion=(basis.inverted() @ q @ basis).to_quaternion();b.location=basis.inverted() @ Vector(offset)
CLIPS={'Idle':(48,True),'Walk':(24,True),'Aim':(18,False),'Shoot':(12,False),'Hit':(14,False),'Death':(36,False)}
rig.animation_data_create()
for name,(end,loop) in CLIPS.items():
    action=bpy.data.actions.new(name);rig.animation_data.action=action
    for f in range(end+1):
        for b in rig.pose.bones:pose(b.name)
        u=f/end;wave=math.sin(u*2*math.pi)
        if name=='Idle':
            pose('Spine',(math.radians(1.6)*wave,0,0),offset=(0,0,.012*wave));pose('Head',(0,0,math.radians(1)*wave))
        elif name=='Walk':
            pose('Root',offset=(0,0,.016*(1-math.cos(u*4*math.pi))))
            for side,sign in [('L',1),('R',-1)]:
                swing=wave*sign;pose('Thigh.'+side,(math.radians(23)*swing,0,0));pose('Shin.'+side,(-math.radians(27)*max(0,-swing),0,0));pose('Foot.'+side,(math.radians(8)*swing,0,0))
            pose('Spine',(0,0,math.radians(3)*wave));pose('Head',(0,0,-math.radians(2)*wave))
        elif name=='Aim':
            ease=u*u*(3-2*u);pose('UpperArm.R',(math.radians(17)*ease,0,0));pose('UpperArm.L',(math.radians(17)*ease,0,0));pose('Head',(-math.radians(5)*ease,0,0));pose('Spine',(-math.radians(3)*ease,0,0))
        elif name=='Shoot':
            kick=math.sin(math.pi*min(u/.3,1)) if u<=.3 else 0
            pose('Spine',(math.radians(5)*kick,0,0));pose('Weapon',(-math.radians(7)*kick,0,0),offset=(0,-.07*kick,0));pose('UpperArm.R',(-math.radians(4)*kick,0,0));pose('UpperArm.L',(-math.radians(4)*kick,0,0))
        elif name=='Hit':
            hit=math.sin(math.pi*u);pose('Root',offset=(0,-.09*hit,0));pose('Spine',(math.radians(14)*hit,0,math.radians(9)*hit));pose('Head',(math.radians(10)*hit,0,0))
        elif name=='Death':
            ease=u*u*(3-2*u);pose('Root',(math.radians(87)*ease,0,0),offset=(0,-.38*ease,.34*ease));pose('Head',(0,0,math.radians(10)*ease));pose('UpperArm.L',(0,-math.radians(23)*ease,0))
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_quaternion',frame=f,group=b.name);b.keyframe_insert('location',frame=f,group=b.name)
    for fc in action.fcurves:
        for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    action['loop']=loop;action.use_fake_user=True
    rig.animation_data.action=None;track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=end;strip.frame_start=0;strip.frame_end=end;track.mute=True
for b in rig.pose.bones:pose(b.name)
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
scene.frame_start=0;scene.frame_end=48
# 保存可編輯來源與純模型 GLB；不把預覽光源／地板混入遊戲模型。
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rifleman.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'rifleman.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_yup=True,export_materials='EXPORT',export_apply=False)
body.data.calc_loop_triangles()
report={'blender':bpy.app.version_string,'height_m':round(max((body.matrix_world@v.co).z for v in body.data.vertices),3),'triangles':len(body.data.loop_triangles),'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'mesh_objects':1,'materials':[m.name for m in body.data.materials],'glb_bytes':(OUT/'rifleman.glb').stat().st_size,'blender_up':'+Z','blender_forward':'+Y','gltf_up':'+Y','gltf_forward':'-Z','origin':[0,0,0],'clips':{n:{'duration_seconds':e/24,'loop':l} for n,(e,l) in CLIPS.items()}}
(OUT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('BUILD_REPORT',json.dumps(report,ensure_ascii=False))
