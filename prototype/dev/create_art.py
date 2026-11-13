"""Blender blockout assets, NOT a Lionheart/Granny export or finished character.

Creates an adult female celestial, a simple rig, sandals, feather wings, a halo,
and two light rings. Run: blender -b --python create_art.py -- OUTPUT_DIRECTORY
"""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

out = Path(sys.argv[sys.argv.index('--') + 1])
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, metal=0, rough=.45, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m


skin = material('Ivory warm skin', (.83, .66, .51))
ivory = material('Ivory celestial cloth', (.92, .93, .88), rough=.65)
feather = material('Pearl feathers', (.93, .96, 1), rough=.52)
gold = material('Brushed gold', (.72, .40, .095), metal=.8, rough=.27)
light = material('Warm luminous aether', (1, .77, .25), metal=.2, rough=.22, emission=3)
hair = material('Pale gold hair', (.60, .40, .16), metal=.12)
sole = material('Sandal leather', (.24, .12, .055))
eye = material('Iris', (.12, .39, .48), rough=.25)
white = material('Eye white', (.94, .95, .91))
lip = material('Lips', (.45, .19, .15))
dark = material('Pupil', (.013, .025, .03))
bindings = []


def finish(obj, name, mat, bone=None):
    obj.name = name
    obj.data.materials.append(mat)
    if hasattr(obj.data, 'polygons'):
        for poly in obj.data.polygons:
            poly.use_smooth = True
    if bone:
        bindings.append((obj, bone))
    return obj


def ellipsoid(name, loc, scale, mat, bone=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bone)


def limb(name, start, end, radius, mat, bone=None, radius2=None):
    start, end = Vector(start), Vector(end)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=radius, radius2=radius2 or radius * .82,
                                  depth=(end - start).length, location=(start + end) / 2)
    ob = bpy.context.object
    ob.rotation_euler = (end - start).to_track_quat('Z', 'Y').to_euler()
    bevel = ob.modifiers.new('Soft seams', 'BEVEL')
    bevel.width = .015
    bevel.segments = 3
    return finish(ob, name, mat, bone)


def ring(name, loc, radius, thickness, mat, rotation=(0, 0, 0), bone=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=8, location=loc,
        major_radius=radius, minor_radius=thickness, rotation=rotation)
    return finish(bpy.context.object, name, mat, bone)


def ribbon(name, points, thickness, mat, bone=None):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = thickness
    curve.bevel_resolution = 3
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for p, v in zip(spline.bezier_points, points):
        p.co = v
        p.handle_left_type = p.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj.select_set(False)
    if bone:
        bindings.append((obj, bone))
    return obj


def dress():
    # A closed modest tunic silhouette, with a short flared skirt.
    profiles = [(.72, .265, .19), (.77, .26, .185), (.92, .235, .155),
        (1.03, .19, .125), (1.15, .155, .12), (1.28, .205, .145),
        (1.38, .20, .14), (1.43, .145, .105)]
    verts, faces = [], []
    n = 48
    for z, rx, ry in profiles:
        for i in range(n):
            t = 2 * math.pi * i / n
            pleat = 1 + (.035 * math.cos(t * 12) if z < 1.03 else 0)
            verts.append((rx * math.cos(t) * pleat, ry * math.sin(t) * pleat, z))
    for j in range(len(profiles) - 1):
        for i in range(n):
            k, q = j * n + i, j * n + (i + 1) % n
            faces.append((k, q, q + n, k + n))
    mesh = bpy.data.meshes.new('Tunic mesh')
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new('Ivory tunic - blockout', mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, obj.name, ivory, 'Bip01 Spine')
    solid = obj.modifiers.new('Cloth thickness', 'SOLIDIFY')
    solid.thickness = .006
    for z, rx, ry in [(.735, .265, .19), (1.09, .17, .125), (1.425, .145, .105)]:
        pts = [(rx * math.cos(i * 2 * math.pi / 48), ry * math.sin(i * 2 * math.pi / 48), z)
               for i in range(49)]
        ribbon('Gold tunic edging', pts, .007, gold, 'Bip01 Spine')


# The model faces -Y. Body proportions are stylized adult proportions.
ellipsoid('Pelvis', (0, 0, .97), (.18, .125, .17), skin, 'Bip01 Pelvis')
ellipsoid('Torso', (0, 0, 1.22), (.175, .115, .24), skin, 'Bip01 Spine')
for side in [-1, 1]:
    prefix = 'L' if side > 0 else 'R'
    thigh, knee, ankle = (side * .10, 0, .91), (side * .11, -.012, .53), (side * .115, .01, .13)
    limb(prefix + ' thigh', thigh, knee, .092, skin, f'Bip01 {prefix} Thigh', .070)
    ellipsoid(prefix + ' knee', knee, (.072, .069, .072), skin, f'Bip01 {prefix} Calf')
    limb(prefix + ' calf', knee, ankle, .065, skin, f'Bip01 {prefix} Calf', .039)
    ellipsoid(prefix + ' foot', (side * .115, -.055, .082), (.047, .108, .045), skin, f'Bip01 {prefix} Foot')
    ellipsoid(prefix + ' sandal sole', (side * .115, -.06, .043), (.052, .113, .017), sole, f'Bip01 {prefix} Foot')
    for y in [-.10, -.035]:
        ribbon(prefix + ' sandal strap', [(side * .115 - .047, y, .073),
            (side * .115, y - .005, .122), (side * .115 + .047, y, .073)], .009, gold, f'Bip01 {prefix} Foot')
    ring(prefix + ' sandal ankle', (side * .115, .008, .15), .043, .007, gold, bone=f'Bip01 {prefix} Calf')
    shoulder, elbow, hand = (side * .20, 0, 1.39), (side * .40, -.015, 1.20), (side * .58, -.03, 1.06)
    ellipsoid(prefix + ' shoulder', shoulder, (.085, .085, .086), skin, f'Bip01 {prefix} UpperArm')
    limb(prefix + ' upper arm', shoulder, elbow, .060, skin, f'Bip01 {prefix} UpperArm', .043)
    ellipsoid(prefix + ' elbow', elbow, (.045, .045, .045), skin, f'Bip01 {prefix} Forearm')
    limb(prefix + ' forearm', elbow, hand, .044, skin, f'Bip01 {prefix} Forearm', .029)
    ellipsoid(prefix + ' hand', (side * .61, -.035, 1.035), (.035, .026, .061), skin, f'Bip01 {prefix} Hand')
    ring(prefix + ' gold wrist cuff', (side * .565, -.03, 1.07), .032, .009, gold,
        (0, math.pi / 4 * side, 0), f'Bip01 {prefix} Hand')
    # Paired luminous rings have separate objects/bone assignments for future export.
    ring(prefix + ' Chakram gold rim', (side * .70, -.06, 1.05), .19, .012, gold,
         (math.pi / 2, 0, 0), f'Bip01 {prefix} Hand')
    ring(prefix + ' Chakram light core', (side * .70, -.063, 1.05), .175, .008, light,
         (math.pi / 2, 0, 0), f'Bip01 {prefix} Hand')
    for i in range(8):
        theta = i * math.pi / 4
        ellipsoid(prefix + ' Chakram light sigil', (side * .70 + .19 * math.cos(theta), -.06,
            1.05 + .19 * math.sin(theta)), (.018, .009, .018), light, f'Bip01 {prefix} Hand')

dress()
limb('Neck', (0, 0, 1.41), (0, 0, 1.55), .052, skin, 'Bip01 Neck')
ellipsoid('Head', (0, -.008, 1.655), (.095, .088, .125), skin, 'Bip01 Head')
ellipsoid('Hair cap', (0, .016, 1.701), (.102, .084, .09), hair, 'Bip01 Head')
for side in [-1, 1]:
    ellipsoid('Ear', (side * .093, -.002, 1.645), (.017, .015, .031), skin, 'Bip01 Head')
    ellipsoid('Eye white', (side * .036, -.085, 1.67), (.024, .008, .011), white, 'Bip01 Head')
    ellipsoid('Iris', (side * .036, -.092, 1.67), (.009, .003, .009), eye, 'Bip01 Head')
    ellipsoid('Pupil', (side * .036, -.095, 1.67), (.004, .002, .006), dark, 'Bip01 Head')
    ribbon('Eyebrow', [(side * .017, -.087, 1.697), (side * .035, -.092, 1.702),
        (side * .057, -.079, 1.695)], .003, hair, 'Bip01 Head')
    ribbon('Long hair', [(side * .065, .025, 1.74), (side * .097, .032, 1.66),
        (side * .104, .04, 1.52), (side * .12, .055, 1.40)], .028, hair, 'Bip01 Head')
ellipsoid('Nose', (0, -.091, 1.641), (.012, .020, .025), skin, 'Bip01 Head')
ribbon('Mouth', [(-.024, -.084, 1.606), (0, -.094, 1.602), (.024, -.084, 1.606)], .0035, lip, 'Bip01 Head')
ring('Luminous halo', (0, .015, 1.88), .145, .010, light, (.12, 0, 0), 'Bip01 Head')
ring('Halo gold inner rim', (0, .015, 1.88), .126, .005, gold, (.12, 0, 0), 'Bip01 Head')

# Small wings: layered tapered leaf meshes rather than a full bird-wing rig.
for side in [-1, 1]:
    prefix = 'L' if side > 0 else 'R'
    base = Vector((side * .13, .095, 1.36))
    for i in range(9):
        end = Vector((side * (.30 + .027 * i), .14 + .015 * i, 1.70 - .042 * i))
        direction = end - base
        perp = Vector((-direction.z, 0, direction.x)).normalized() * (.032 + .001 * i)
        middle = base.lerp(end, .57)
        verts = [base, middle + perp, end, middle - perp, middle + Vector((0, -.014, 0))]
        faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)]
        mesh = bpy.data.meshes.new('Feather')
        mesh.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new(prefix + ' Wing feather ' + str(i + 1), mesh)
        bpy.context.collection.objects.link(ob)
        finish(ob, ob.name, feather, f'Aetherian {prefix} Wing')
        bevel = ob.modifiers.new('Feather edges', 'BEVEL')
        bevel.width, bevel.segments = .004, 2
        ribbon(prefix + ' Feather shaft', [base, middle, end], .002, gold, f'Aetherian {prefix} Wing')

# Simple rigid-segment rig for an editable blockout; not production skinning.
arm = bpy.data.armatures.new('Aetherian blockout skeleton')
rig = bpy.data.objects.new('Aetherian - REFERENCE RIG', arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')


def bone(name, start, end, parent=None):
    b = arm.edit_bones.new(name)
    b.head, b.tail = start, end
    if parent:
        b.parent = arm.edit_bones[parent]


bone('Bip01', (0, 0, 0), (0, 0, .15))
bone('Bip01 Pelvis', (0, 0, .90), (0, 0, 1.04), 'Bip01')
bone('Bip01 Spine', (0, 0, 1.04), (0, 0, 1.40), 'Bip01 Pelvis')
bone('Bip01 Neck', (0, 0, 1.40), (0, 0, 1.55), 'Bip01 Spine')
bone('Bip01 Head', (0, 0, 1.55), (0, 0, 1.78), 'Bip01 Neck')
for side in [-1, 1]:
    prefix = 'L' if side > 0 else 'R'
    bone(f'Bip01 {prefix} Thigh', (side * .10, 0, .91), (side * .11, -.012, .53), 'Bip01 Pelvis')
    bone(f'Bip01 {prefix} Calf', (side * .11, -.012, .53), (side * .115, .01, .13), f'Bip01 {prefix} Thigh')
    bone(f'Bip01 {prefix} Foot', (side * .115, .01, .13), (side * .115, -.13, .06), f'Bip01 {prefix} Calf')
    bone(f'Bip01 {prefix} UpperArm', (side * .20, 0, 1.39), (side * .40, -.015, 1.20), 'Bip01 Spine')
    bone(f'Bip01 {prefix} Forearm', (side * .40, -.015, 1.20), (side * .58, -.03, 1.06), f'Bip01 {prefix} UpperArm')
    bone(f'Bip01 {prefix} Hand', (side * .58, -.03, 1.06), (side * .64, -.035, 1.01), f'Bip01 {prefix} Forearm')
    bone(f'Aetherian {prefix} Wing', (side * .13, .095, 1.36), (side * .43, .19, 1.52), 'Bip01 Spine')
bpy.ops.object.mode_set(mode='OBJECT')
rig.select_set(False)
for ob, name in bindings:
    # Full weight to a reference bone; deforming topology requires a later art pass.
    group = ob.vertex_groups.new(name=name)
    group.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    mod = ob.modifiers.new('Reference skeleton', 'ARMATURE')
    mod.object = rig
    ob.parent = rig

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene['asset_status'] = 'Procedural blockout. No Granny/GR2 export. Not installed in game.'
scene['design'] = 'Adult female lesser celestial; pale palette, small wings, halo, sandals, paired luminous chakrams.'
scene['rig_status'] = 'Reference rigid weights; requires retopology, skinning, animation and exact game skeleton matching.'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.world.color = (.12, .14, .19)

floor_mat = material('Studio slate', (.045, .055, .075), rough=.75)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, .018))
floor = finish(bpy.context.object, 'STUDIO ground - do not export', floor_mat)


def aim(ob, at):
    ob.rotation_euler = (Vector(at) - ob.location).to_track_quat('-Z', 'Y').to_euler()


for name, loc, power, size, color in [('Key', (2, -4, 4), 500, 4, (1, .88, .70)),
    ('Fill', (-3, -2, 2), 350, 3, (.65, .80, 1)), ('Rim', (1, 3, 3), 650, 3, (1, .80, .48))]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size, data.color = power, 'DISK', size, color
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, (0, 0, 1))
bpy.ops.object.camera_add(location=(2.7, -5, 2.5))
camera = bpy.context.object
camera.name = 'Preview camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.45
aim(camera, (0, 0, 1))
scene.camera = camera
scene.view_settings.view_transform = 'AgX'
scene.render.filepath = str(out / 'Aetherian_Blockout_preview.png')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Aetherian_Blockout.blend'))
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for ob, _ in bindings:
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(out / 'Aetherian_Blockout.glb'), use_selection=True,
    export_format='GLB', export_apply=True, export_animations=False)
scene.render.filepath = str(out / 'Aetherian_Blockout_preview.png')
bpy.ops.render.render(write_still=True)
print('ART_COMPLETE', out)
