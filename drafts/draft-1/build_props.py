"""Props: two big detailed wooden crates. Crate 1 is closed; crate 2 is open
at the top and holds a stack of logs. Each crate is an empty ("Crate1",
"Crate2") with slats, corner posts, diagonal braces, iron corner brackets and
bolts parented to it, so the empty can be animated as one thing.

Run inside Blender with slimsico.blend open. Re-running replaces the props.
"""
import bmesh
import bpy
import math
import random
from mathutils import Vector

scene = bpy.context.scene
random.seed(7)

# ------------------------------------------------------------ cleanup
if "Props" in bpy.data.collections:
    col = bpy.data.collections["Props"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
for m in list(bpy.data.meshes):
    if m.users == 0:
        bpy.data.meshes.remove(m)
col = bpy.data.collections.new("Props")
scene.collection.children.link(col)


def link(obj, parent):
    """Parent obj to the crate empty, keeping obj's transform as a local offset."""
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    return obj


# ------------------------------------------------------------ materials
def new_material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf


def wood_material(name, light, dark, scale=1.0, rough=0.7):
    """Planks: stretched noise grain blended between two browns, with a bump."""
    m, nt, bsdf = new_material(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0 * scale, 12.0 * scale, 1.0 * scale)   # long grain along Y
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.5
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.65
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (*light, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*light, 1)
    return m


def iron_material():
    m, nt, bsdf = new_material("CrateIron")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.08, 0.07, 0.07, 1)
    ramp.color_ramp.elements[1].color = (0.22, 0.18, 0.15, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.55
    m.diffuse_color = (0.12, 0.1, 0.09, 1)
    return m


def bark_material():
    m, nt, bsdf = new_material("LogBark")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (3.0, 3.0, 0.6)        # ridges run along the log
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 10.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.10, 0.06, 0.035, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.32, 0.21, 0.12, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    m.diffuse_color = (0.2, 0.13, 0.08, 1)
    return m


def log_end_material():
    """Concentric growth rings on the cut ends."""
    m, nt, bsdf = new_material("LogEnd")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.rings_direction = "Z"
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 1.2
    wave.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.52, 0.36, 0.2, 1)
    ramp.color_ramp.elements[1].color = (0.78, 0.62, 0.4, 1)
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    m.diffuse_color = (0.7, 0.55, 0.35, 1)
    return m


PLANK = wood_material("CratePlank", (0.62, 0.44, 0.24), (0.36, 0.23, 0.11))
POST = wood_material("CratePost", (0.48, 0.32, 0.16), (0.26, 0.16, 0.07), scale=1.6)
IRON = iron_material()
BARK = bark_material()
LOG_END = log_end_material()


# ------------------------------------------------------------ crate builder
def box(name, size, loc, mat, parent, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return link(o, parent)


def crate(name, size, location, open_top=False):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "CUBE"
    root.empty_display_size = size / 2
    root.location = location
    root["rest"] = list(location)          # where it sits on the ground; animation scripts read this
    col.objects.link(root)
    h = size / 2
    post = 0.34                    # corner post thickness
    slat = 0.16                    # plank thickness
    n_slats = 5
    gap = 0.07
    inner = size - 2 * post
    slat_w = (inner - (n_slats - 1) * gap) / n_slats

    # 12 corner posts (edges of the cube)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("%s_PostZ" % name, (post, post, size), (sx * (h - post / 2), sy * (h - post / 2), 0), POST, root)
        for sz in (-1, 1):
            box("%s_PostY" % name, (post, inner, post), (sx * (h - post / 2), 0, sz * (h - post / 2)), POST, root)
    for sy in (-1, 1):
        for sz in (-1, 1):
            box("%s_PostX" % name, (inner, post, post), (0, sy * (h - post / 2), sz * (h - post / 2)), POST, root)

    # planks: horizontal slats on the four sides, boards on the base (and lid)
    for i in range(n_slats):
        z = -inner / 2 + slat_w / 2 + i * (slat_w + gap)
        for s in (-1, 1):
            box("%s_SlatX" % name, (slat, inner, slat_w), (s * (h - slat / 2 - 0.01), 0, z), PLANK, root, bevel=0.015)
            box("%s_SlatY" % name, (inner, slat, slat_w), (0, s * (h - slat / 2 - 0.01), z), PLANK, root, bevel=0.015)
        x = z
        faces = (-1,) if open_top else (-1, 1)
        for s in faces:
            box("%s_Board" % name, (slat_w, inner, slat), (x, 0, s * (h - slat / 2 - 0.01)), PLANK, root, bevel=0.015)

    # diagonal braces across each side, slightly proud of the slats
    brace_len = math.hypot(inner, inner) * 0.92
    for s in (-1, 1):
        box("%s_BraceX" % name, (slat, 0.5, brace_len), (s * (h + slat / 2 - 0.02), 0, 0), POST, root,
            rot=(math.radians(45 * s), 0, 0))
        box("%s_BraceY" % name, (0.5, slat, brace_len), (0, s * (h + slat / 2 - 0.02), 0), POST, root,
            rot=(0, math.radians(-45 * s), 0))

    # iron corner brackets: three thin plates per corner, with bolt heads
    plate, plate_len, t = 0.9, 0.9, 0.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                cx, cy, cz = sx * h, sy * h, sz * h
                box("%s_Bracket" % name, (t, plate_len, plate), (cx + sx * t / 2, cy - sy * plate_len / 2, cz - sz * plate / 2), IRON, root, bevel=0)
                box("%s_Bracket" % name, (plate_len, t, plate), (cx - sx * plate_len / 2, cy + sy * t / 2, cz - sz * plate / 2), IRON, root, bevel=0)
                if not (open_top and sz == 1):
                    box("%s_Bracket" % name, (plate_len, plate, t), (cx - sx * plate_len / 2, cy - sy * plate / 2, cz + sz * t / 2), IRON, root, bevel=0)
                for (bx, by, bz) in ((cx + sx * t, cy - sy * 0.55, cz - sz * 0.35),
                                     (cx - sx * 0.55, cy + sy * t, cz - sz * 0.35)):
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, segments=12, ring_count=6, location=(bx, by, bz))
                    bolt = bpy.context.object
                    bolt.name = "%s_Bolt" % name
                    bolt.scale = (1, 1, 0.6)
                    bolt.data.materials.append(IRON)
                    bpy.ops.object.shade_smooth()
                    link(bolt, root)
    return root


# ------------------------------------------------------------ logs
def log(name, radius, length, loc, rot, parent):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=28, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(BARK)
    o.data.materials.append(LOG_END)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for f in bm.faces:
        if abs(f.normal.z) > 0.9:              # the cut ends (local Z is the log axis)
            f.material_index = 1
    # rough the bark up a little so it is not a perfect tube
    for v in bm.verts:
        if abs(v.co.z) < length / 2 - 0.01:
            r = 1 + random.uniform(-0.04, 0.04)
            v.co.x *= r
            v.co.y *= r
    bm.to_mesh(o.data)
    bm.free()
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = 0.05
    b.segments = 2
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    return link(o, parent)


SIZE = 5.5
crate1 = crate("Crate1", SIZE, (-7.5, -20.0, SIZE / 2))
crate2 = crate("Crate2", SIZE, (7.0, -19.5, SIZE / 2), open_top=True)

# logs standing upright in the open crate, taller than it, so they rise out of
# the top in a loose bundle
floor_z = -SIZE / 2 + 0.16
spots = [(0, 0), (1.1, 0.2), (-1.1, 0.3), (0.5, 1.05), (-0.6, 1.0), (0.55, -1.05), (-0.5, -1.1)]
for i, (x, y) in enumerate(spots):
    r = 0.5 + random.uniform(-0.05, 0.05)
    length = SIZE + random.uniform(0.9, 2.3)
    tilt = random.uniform(-0.05, 0.05)
    log("Crate2_Log%d" % (i + 1), r, length, (x, y, floor_z + length / 2),
        (tilt, random.uniform(-0.05, 0.05), 0), crate2)

bpy.ops.object.select_all(action="DESELECT")
print("props built:", len(col.objects), "objects")
