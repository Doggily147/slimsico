"""One big wooden crate that can break apart: an empty ("Crate") with corner
posts, slats, base and lid boards, diagonal braces, iron corner brackets and
bolts parented to it, so it drops as one thing and its parts can fly apart.
Every part stores its resting local transform ("rest_loc", "rest_rot") so the
beat script can reset and scatter them.

Run inside Blender with slimsico.blend open. Re-running replaces the crate.
"""
import bpy
import math
import random

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene
random.seed(11)

SIZE = 7.5

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
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    obj["rest_loc"] = list(obj.location)
    obj["rest_rot"] = list(obj.rotation_euler)
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
    m, nt, bsdf = new_material(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0 * scale, 12.0 * scale, 1.0 * scale)
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


PLANK = wood_material("CratePlank", (0.62, 0.44, 0.24), (0.36, 0.23, 0.11))
POST = wood_material("CratePost", (0.48, 0.32, 0.16), (0.26, 0.16, 0.07), scale=1.6)
IRON = iron_material()


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


def crate(name, size, location):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "CUBE"
    root.empty_display_size = size / 2
    root.location = location
    root["rest"] = list(location)
    root["size"] = size
    col.objects.link(root)
    h = size / 2
    post, slat, n_slats, gap = 0.42, 0.2, 6, 0.08
    inner = size - 2 * post
    slat_w = (inner - (n_slats - 1) * gap) / n_slats
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("%s_PostZ" % name, (post, post, size), (sx * (h - post / 2), sy * (h - post / 2), 0), POST, root)
        for sz in (-1, 1):
            box("%s_PostY" % name, (post, inner, post), (sx * (h - post / 2), 0, sz * (h - post / 2)), POST, root)
    for sy in (-1, 1):
        for sz in (-1, 1):
            box("%s_PostX" % name, (inner, post, post), (0, sy * (h - post / 2), sz * (h - post / 2)), POST, root)
    for i in range(n_slats):
        z = -inner / 2 + slat_w / 2 + i * (slat_w + gap)
        for s in (-1, 1):
            box("%s_SlatX" % name, (slat, inner, slat_w), (s * (h - slat / 2 - 0.01), 0, z), PLANK, root, bevel=0.015)
            box("%s_SlatY" % name, (inner, slat, slat_w), (0, s * (h - slat / 2 - 0.01), z), PLANK, root, bevel=0.015)
        for s in (-1, 1):
            box("%s_Board" % name, (slat_w, inner, slat), (z, 0, s * (h - slat / 2 - 0.01)), PLANK, root, bevel=0.015)
    brace_len = math.hypot(inner, inner) * 0.92
    for s in (-1, 1):
        box("%s_BraceX" % name, (slat, 0.6, brace_len), (s * (h + slat / 2 - 0.02), 0, 0), POST, root, rot=(math.radians(45 * s), 0, 0))
        box("%s_BraceY" % name, (0.6, slat, brace_len), (0, s * (h + slat / 2 - 0.02), 0), POST, root, rot=(0, math.radians(-45 * s), 0))
    plate, plate_len, t = 1.1, 1.1, 0.06
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                cx, cy, cz = sx * h, sy * h, sz * h
                box("%s_Bracket" % name, (t, plate_len, plate), (cx + sx * t / 2, cy - sy * plate_len / 2, cz - sz * plate / 2), IRON, root, bevel=0)
                box("%s_Bracket" % name, (plate_len, t, plate), (cx - sx * plate_len / 2, cy + sy * t / 2, cz - sz * plate / 2), IRON, root, bevel=0)
                box("%s_Bracket" % name, (plate_len, plate, t), (cx - sx * plate_len / 2, cy - sy * plate / 2, cz + sz * t / 2), IRON, root, bevel=0)
                for (bx, by, bz) in ((cx + sx * t, cy - sy * 0.65, cz - sz * 0.45), (cx - sx * 0.65, cy + sy * t, cz - sz * 0.45)):
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, segments=12, ring_count=6, location=(bx, by, bz))
                    bolt = bpy.context.object
                    bolt.name = "%s_Bolt" % name
                    bolt.scale = (1, 1, 0.6)
                    bolt.data.materials.append(IRON)
                    bpy.ops.object.shade_smooth()
                    link(bolt, root)
    return root


crate("Crate", SIZE, (0.0, -12.0, SIZE / 2))
bpy.ops.object.select_all(action="DESELECT")
print("crate built:", len(col.objects), "objects, size", SIZE)
