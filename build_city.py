"""A giant neon cyber city under a forcefield dome, in the far corner of the
plate. Built from the drawing: a ring wall of tough stone round the bottom
with a car-sized turret pod on top every 45 degrees, an arched forcefield gate
in the front of the wall (the side facing the plate), and a simple forcefield
dome sitting on the wall top over everything. Inside: a street grid with two
lit avenues and a ring road, a hundred-odd towers stepping up toward the
centre with lit windows, neon edge strips, antennas and holographic
billboards, ground cars circling the ring road, and flying cars on lanes at
several heights. Everything hangs off the "City" empty; cars are keyed for
the whole timeline so the city is alive in any shot.

  blender -b slimsico.blend --python build_city.py --python-expr "import bpy; bpy.ops.wm.save_mainfile()"

Re-running replaces the city. render_city.py renders the check views.
"""
import bmesh
import bpy
import math
import os
import random
from mathutils import Matrix, Vector

scene = bpy.data.scenes["Scene"]
if bpy.context.window:
    bpy.context.window.scene = scene
random.seed(21)

CITY_POS = Vector((-165.0, -165.0, 0.0))     # the far corner of the plate, away from the story
R_CITY = 92.0                                 # the built-up radius
R_WALL_IN, R_WALL_OUT, WALL_H = 98.0, 102.0, 14.0
R_RING = 84.0                                 # the ring road
GATE_ANGLE = math.radians(45.0)               # the gate faces the plate centre
GATE_W, GATE_H = 16.0, 11.0
FRAMES = (scene.frame_start, max(scene.frame_end, 1656))
FPS = 24
HUD = os.path.join(os.path.dirname(bpy.data.filepath), "textures", "hud", "hud_0001.png")

# ------------------------------------------------------------ cleanup
if "City" in bpy.data.collections:
    col = bpy.data.collections["City"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights):
    for d in list(block):
        if d.users == 0 and d.name.startswith("City"):
            block.remove(d)
col = bpy.data.collections.new("City")
scene.collection.children.link(col)
root = bpy.data.objects.new("City", None)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 10
root.location = CITY_POS
col.objects.link(root)


def attach(obj, parent=root):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    return obj


# ------------------------------------------------------------ materials
def new_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf, out


def plain(name, rgb, rough=0.6, metallic=0.0, emit=None, strength=0.0):
    m, nt, bsdf, _ = new_mat(name)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*(emit if emit else rgb), 1)
    return m


def neon(name, rgb, strength=8.0):
    return plain(name, rgb, rough=0.3, emit=rgb, strength=strength)


def building_mat(name, tint, warm):
    """Dark facade with a grid of windows, lit at random, from a brick texture in
    object space (sizes are baked into the meshes, so windows stay one size)."""
    m, nt, bsdf, _ = new_mat(name)
    bsdf.inputs["Base Color"].default_value = (*tint, 1)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Metallic"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.55, 0.55, 0.42)          # ~1.8 wide, ~2.4 tall windows
    # two brick layers so the pattern reads on every face: one keyed by x, one by y
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.12
    brick.inputs["Bias"].default_value = -0.35
    brick.inputs["Color1"].default_value = (*warm, 1)
    brick.inputs["Color2"].default_value = (0.02, 0.02, 0.03, 1)
    brick.inputs["Mortar"].default_value = (0.01, 0.01, 0.015, 1)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["X"], add.inputs[0])
    nt.links.new(sep.outputs["Y"], add.inputs[1])
    nt.links.new(add.outputs["Value"], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    nt.links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 2.2
    m.diffuse_color = (*tint, 1)
    return m


def stone_mat():
    m, nt, bsdf, _ = new_mat("CityStone")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1.1
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 9.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.2, 0.19, 0.17, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.36, 0.34, 0.31, 1)
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "LESS_THAN"
    edge.inputs[1].default_value = 0.035
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.05, 0.045, 0.04, 1)                # the joints between blocks
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(vor.outputs["Distance"], edge.inputs[0])
    nt.links.new(edge.outputs["Value"], mix.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    m.diffuse_color = (0.25, 0.23, 0.21, 1)
    return m


def forcefield_mat(name, rgb, strength=1.6, alpha=0.18):
    """A see-through field: a fresnel glow at grazing angles and a faint cell
    pattern, over a transparent shader."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = "BLEND"
    m.use_backface_culling = False
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*rgb, 1)
    mixsh = nt.nodes.new("ShaderNodeMixShader")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.5
    lines = nt.nodes.new("ShaderNodeMath")
    lines.operation = "LESS_THAN"
    lines.inputs[1].default_value = 0.06
    cells = nt.nodes.new("ShaderNodeMath")
    cells.operation = "MULTIPLY"
    cells.inputs[1].default_value = 0.12
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "ADD"
    base = nt.nodes.new("ShaderNodeMath")
    base.operation = "ADD"
    base.inputs[1].default_value = alpha
    clamp = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], lines.inputs[0])
    nt.links.new(lines.outputs["Value"], cells.inputs[0])
    nt.links.new(lw.outputs["Fresnel"], fac.inputs[0])
    nt.links.new(cells.outputs["Value"], fac.inputs[1])
    nt.links.new(fac.outputs["Value"], base.inputs[0])
    nt.links.new(base.outputs["Value"], clamp.inputs["Value"])
    nt.links.new(clamp.outputs["Result"], mixsh.inputs["Fac"])
    nt.links.new(transp.outputs["BSDF"], mixsh.inputs[1])
    nt.links.new(emit.outputs["Emission"], mixsh.inputs[2])
    emit.inputs["Strength"].default_value = strength
    nt.links.new(mixsh.outputs["Shader"], out.inputs["Surface"])
    m.diffuse_color = (*rgb, 0.3)
    return m


def car_mat(name, rough=0.3, metallic=0.6):
    """Painted body coloured per object (Object Info colour) so one mesh serves
    every car."""
    m, nt, bsdf, _ = new_mat(name)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = 0.6
    m.diffuse_color = (0.6, 0.6, 0.6, 1)
    return m


ASPHALT = plain("CityAsphalt", (0.035, 0.035, 0.04), rough=0.85)
PAVEMENT = plain("CityPavement", (0.09, 0.09, 0.1), rough=0.8)
DARK = plain("CityDark", (0.03, 0.03, 0.035), rough=0.5, metallic=0.5)
CHROME = plain("CityChrome", (0.7, 0.72, 0.75), rough=0.25, metallic=0.9)
STONE = stone_mat()
NEON_MAG = neon("CityNeonMagenta", (1.0, 0.1, 0.7))
NEON_CYAN = neon("CityNeonCyan", (0.1, 0.9, 1.0))
NEON_BLUE = neon("CityNeonBlue", (0.2, 0.35, 1.0))
NEON_ORANGE = neon("CityNeonOrange", (1.0, 0.45, 0.05))
NEON_LANE = neon("CityNeonLane", (0.35, 0.8, 1.0), strength=3.0)
HEADLIGHT = neon("CityHeadlight", (1.0, 0.95, 0.8), strength=12.0)
TAILLIGHT = neon("CityTaillight", (1.0, 0.08, 0.05), strength=10.0)
FIELD = forcefield_mat("CityForcefield", (0.25, 0.6, 1.0), strength=1.2, alpha=0.04)
GATE_FIELD = forcefield_mat("CityGateField", (0.3, 0.8, 1.0), strength=3.0, alpha=0.22)
CAR_PAINT = car_mat("CityCarPaint")
FLYER_PAINT = car_mat("CityFlyerPaint", rough=0.2, metallic=0.8)
FACADES = [building_mat("CityFacade%d" % i, tint, warm) for i, (tint, warm) in enumerate((
    ((0.05, 0.06, 0.09), (1.0, 0.85, 0.55)), ((0.06, 0.05, 0.08), (0.6, 0.9, 1.0)),
    ((0.04, 0.05, 0.06), (1.0, 0.6, 0.85)), ((0.07, 0.07, 0.08), (0.9, 0.95, 1.0))))]
NEONS = [NEON_MAG, NEON_CYAN, NEON_BLUE, NEON_ORANGE]


# ------------------------------------------------------------ mesh helpers
def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0, parent=root):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.transform(Matrix.Diagonal((*size, 1.0)))
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return attach(o, parent)


def cylinder(name, r, h, loc, mat, verts=24, rot=(0, 0, 0), parent=root):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    return attach(o, parent)


def annulus(name, r0, r1, z, mat, segs=96, parent=root):
    bm = bmesh.new()
    inner = [bm.verts.new((r0 * math.cos(2 * math.pi * i / segs), r0 * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
    outer = [bm.verts.new((r1 * math.cos(2 * math.pi * i / segs), r1 * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    o.data.materials.append(mat)
    scene.collection.objects.link(o)
    return attach(o, parent)


def wall_segment(name, a0, a1, r0, r1, z0, z1, mat, parent=root, outline=None):
    """A block of the ring wall between angles a0..a1. With `outline` (a list
    of (t, z) points, t in 0..1 along the arc) the radial face is that polygon
    instead of a rectangle, extruded through the wall: the gate's arch."""
    bm = bmesh.new()
    if outline is None:
        outline = [(0, z0), (1, z0), (1, z1), (0, z1)]
    layers = []
    for r in (r0, r1):
        ring = []
        for t, z in outline:
            a = a0 + (a1 - a0) * t
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        layers.append(ring)
    n = len(outline)
    bm.faces.new(layers[0][::-1])
    bm.faces.new(layers[1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((layers[0][i], layers[0][j], layers[1][j], layers[1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if len(outline) > 4:
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    o.data.materials.append(mat)
    scene.collection.objects.link(o)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = 0.15
    b.segments = 2
    return attach(o, parent)


# ------------------------------------------------------------ the ground: streets
annulus("City_Ground", 0.0, R_WALL_OUT + 6, 0.04, PAVEMENT, segs=128).name = "City_Ground"
annulus("City_RingRoad", R_RING - 5, R_RING + 5, 0.08, ASPHALT)
annulus("City_RingLaneOut", R_RING + 4.6, R_RING + 4.9, 0.1, NEON_LANE)
annulus("City_RingLaneIn", R_RING - 4.9, R_RING - 4.6, 0.1, NEON_LANE)
annulus("City_RingLaneMid", R_RING - 0.15, R_RING + 0.15, 0.1, NEON_LANE)
for axis in ("x", "y"):
    L = 2 * (R_RING + 5)
    size = (L, 10, 0.06) if axis == "x" else (10, L, 0.06)
    box("City_Avenue_" + axis, size, (0, 0, 0.08), ASPHALT)
    lane = (L, 0.3, 0.02) if axis == "x" else (0.3, L, 0.02)
    box("City_AvenueLane_" + axis, lane, (0, 0, 0.12), NEON_LANE)
    for s in (-1, 1):
        edge = (L, 0.3, 0.02) if axis == "x" else (0.3, L, 0.02)
        pos = (0, s * 4.8, 0.12) if axis == "x" else (s * 4.8, 0, 0.12)
        box("City_AvenueEdge_" + axis, edge, pos, NEON_LANE)
# a central plaza with a spire
cylinder("City_Plaza", 14, 0.3, (0, 0, 0.15), DARK, verts=48)
annulus("City_PlazaRing", 13.5, 14.2, 0.32, NEON_CYAN, segs=64)
cylinder("City_Spire", 2.6, 68, (0, 0, 34), CHROME, verts=12)
cylinder("City_SpireTop", 0.6, 12, (0, 0, 74), NEON_CYAN, verts=8)
for k in range(5):
    annulus("City_SpireRing%d" % k, 2.9, 3.6, 12 + k * 13, NEONS[k % 4], segs=24)
    cylinder("City_SpireDeck%d" % k, 5.0 - k * 0.6, 0.5, (0, 0, 12 + k * 13 - 0.5), DARK, verts=24)

# ------------------------------------------------------------ the towers
SPACING = 11.0
towers = 0
cells = []
n_cells = int(R_CITY / SPACING) + 1
for i in range(-n_cells, n_cells + 1):
    for j in range(-n_cells, n_cells + 1):
        x, y = i * SPACING, j * SPACING
        if abs(x) < 8 or abs(y) < 8:                       # the avenues
            continue
        d = math.hypot(x, y)
        if d > R_CITY - 4 or abs(d - R_RING) < 6.5 or d < 17:
            continue
        cells.append((x, y, d))
for x, y, d in cells:
    falloff = max(0.0, 1 - d / R_CITY)
    h = 14 + 62 * falloff ** 1.3 * random.uniform(0.55, 1.25)
    w = random.uniform(5.5, 8.5)
    dpt = random.uniform(5.5, 8.5)
    facade = random.choice(FACADES)
    tiers = random.choice((1, 1, 2, 2, 3)) if h > 30 else 1
    z = 0
    tw, td = w, dpt
    for t in range(tiers):
        th = h / tiers * random.uniform(0.85, 1.15) if tiers > 1 else h
        box("City_Tower", (tw, td, th), (x, y, z + th / 2), facade, bevel=0.12)
        # neon strips down two opposite vertical edges
        strip = random.choice(NEONS)
        for sx, sy in random.choice((((1, 1), (-1, -1)), ((1, -1), (-1, 1)))):
            box("City_TowerStrip", (0.22, 0.22, th * 0.92), (x + sx * tw / 2, y + sy * td / 2, z + th / 2), strip)
        z += th
        tw *= random.uniform(0.62, 0.82)
        td *= random.uniform(0.62, 0.82)
    # roof: a lit rim, an antenna or a helipad ring
    box("City_TowerCap", (tw * 1.02, td * 1.02, 0.4), (x, y, z + 0.2), DARK)
    if random.random() < 0.45:
        cylinder("City_Antenna", 0.25, h * 0.25, (x, y, z + h * 0.125), CHROME, verts=8)
        cylinder("City_AntennaTip", 0.35, 0.6, (x, y, z + h * 0.25), TAILLIGHT, verts=8)
    if random.random() < 0.3 and h > 35:
        annulus("City_Helipad", tw * 0.3, tw * 0.36, z + 0.42, NEON_ORANGE, segs=24, parent=root)
    # holographic billboards on the tallest
    if h > 45 and random.random() < 0.6:
        side = random.choice(("x", "y"))
        sgn = random.choice((-1, 1))
        bz = z * random.uniform(0.45, 0.75)
        bw, bh = random.uniform(6, 9), random.uniform(8, 12)
        bb = box("City_Billboard", (0.3, bw, bh) if side == "x" else (bw, 0.3, bh),
                 (x + sgn * (w / 2 + 0.6), y, bz) if side == "x" else (x, y + sgn * (dpt / 2 + 0.6), bz), random.choice(NEONS))
        bb["hologram"] = 1
        bb["out"] = (sgn if side == "x" else 0, sgn if side == "y" else 0)
    towers += 1
# filler: low blocks between towers, a bustling ground level
for x, y, d in cells:
    for k in range(2):
        fx, fy = x + random.uniform(-4.5, 4.5), y + random.uniform(-4.5, 4.5)
        fh = random.uniform(4, 9)
        box("City_Block", (random.uniform(2.5, 4), random.uniform(2.5, 4), fh), (fx, fy, fh / 2), random.choice(FACADES), bevel=0.08)
        box("City_Sign", (random.uniform(1.5, 3), 0.15, random.uniform(0.6, 1.2)), (fx, fy - 2.6, fh * 0.6), random.choice(NEONS))

# holographic billboards show the hover-screen HUD on a floating panel
if os.path.exists(HUD):
    hud_mat = bpy.data.materials.get("CityHoloAd") or bpy.data.materials.new("CityHoloAd")
    hud_mat.use_nodes = True
    hud_mat.blend_method = "BLEND"
    nt = hud_mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.get("hud_0001.png") or bpy.data.images.load(HUD)
    emit.inputs["Strength"].default_value = 4.0
    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(transp.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emit.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    for o in [o for o in col.objects if o.get("hologram")][::2]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        p = bpy.context.object
        p.name = "City_HoloAd"
        dims = o.dimensions
        wide = dims.x > 1.0
        p.scale = ((dims.x if wide else dims.y) * 0.9, dims.z * 0.9, 1)
        p.rotation_euler = (math.radians(90), 0, 0 if wide else math.radians(90))
        ox, oy = o["out"]
        p.location = o.location + Vector((ox * 0.4, oy * 0.4, 0))
        p.data.materials.append(hud_mat)
        attach(p)

# ------------------------------------------------------------ the wall, the gate, the turrets
SEGS = 64
gate_half = (GATE_W / 2) / ((R_WALL_IN + R_WALL_OUT) / 2)   # half the gate, in radians
for k in range(SEGS):
    a0 = 2 * math.pi * k / SEGS
    a1 = 2 * math.pi * (k + 1) / SEGS
    mid = (a0 + a1) / 2
    if abs(((mid - GATE_ANGLE + math.pi) % (2 * math.pi)) - math.pi) < gate_half + (a1 - a0) / 2:
        continue                                            # the gate's gap
    wall_segment("City_Wall", a0, a1, R_WALL_IN, R_WALL_OUT, 0, WALL_H, STONE)
    # a course of lighter stone along the top and a lit slit
    wall_segment("City_WallCap", a0, a1, R_WALL_IN - 0.4, R_WALL_OUT + 0.4, WALL_H, WALL_H + 1.2, STONE)
    wall_segment("City_WallLight", a0 + 0.004, a1 - 0.004, R_WALL_OUT, R_WALL_OUT + 0.08, WALL_H * 0.55, WALL_H * 0.55 + 0.35, NEON_CYAN)
# the gate piece: the wall over the gap with an arched opening, and the field in it
ga0, ga1 = GATE_ANGLE - gate_half - 0.02, GATE_ANGLE + gate_half + 0.02
arch_r = GATE_W / 2 * 0.92
arch_c = GATE_H - arch_r
n_arc = 14
arc = [(0.5 + 0.46 * math.cos(math.pi * i / n_arc), arch_c + arch_r * math.sin(math.pi * i / n_arc)) for i in range(1, n_arc)]
# bottom-right corner, right jamb up, over the arch, left jamb down, bottom-left corner, up and over the wall top
outline = [(1.0, 0.0), (0.96, 0.0), (0.96, arch_c)] + arc + [(0.04, arch_c), (0.04, 0.0), (0.0, 0.0), (0.0, WALL_H), (1.0, WALL_H)]
wall_segment("City_GateWall", ga0, ga1, R_WALL_IN, R_WALL_OUT, 0, WALL_H, STONE, outline=outline)
wall_segment("City_GateCap", ga0 - 0.01, ga1 + 0.01, R_WALL_IN - 0.5, R_WALL_OUT + 0.5, WALL_H, WALL_H + 1.6, STONE)
# gate pillars either side, taller, with lights
for s in (-1, 1):
    pa = GATE_ANGLE + s * (gate_half + 0.035)
    r = (R_WALL_IN + R_WALL_OUT) / 2
    box("City_GatePillar", (5.0, 5.0, WALL_H + 5), (r * math.cos(pa), r * math.sin(pa), (WALL_H + 5) / 2), STONE, rot=(0, 0, pa), bevel=0.2)
    box("City_GatePillarLight", (0.5, 5.2, 0.5), (r * math.cos(pa), r * math.sin(pa), WALL_H + 3.5), NEON_CYAN, rot=(0, 0, pa))
# the forcefield in the arch: the same outline as a thin sheet mid-wall
field_outline = [(0.96, 0.0), (0.96, arch_c)] + arc + [(0.04, arch_c), (0.04, 0.0)]
rm = (R_WALL_IN + R_WALL_OUT) / 2
gate_field = wall_segment("City_GateField", ga0, ga1, rm - 0.05, rm + 0.05, 0, GATE_H, GATE_FIELD, outline=field_outline)
gate_field.modifiers.clear()
# an emitter ring round the arch
for i in range(n_arc + 1):
    a = math.pi * i / n_arc
    t = 0.5 + 0.47 * math.cos(a)
    ang = ga0 + (ga1 - ga0) * t
    box("City_GateEmitter", (0.7, 0.7, 0.7), ((rm + 2.1) * math.cos(ang), (rm + 2.1) * math.sin(ang), arch_c + (arch_r + 0.5) * math.sin(a)), NEON_CYAN, rot=(0, 0, ang))
# the turret pods every 45 degrees on the wall top: car-sized, domed, a lit slit and a barrel pointing out
for k in range(8):
    a = math.radians(45 * k)
    r = (R_WALL_IN + R_WALL_OUT) / 2
    px, py = r * math.cos(a), r * math.sin(a)
    z = WALL_H + 1.2
    if abs(((a - GATE_ANGLE + math.pi) % (2 * math.pi)) - math.pi) < 0.01:
        z = WALL_H + 1.6                                    # over the gate cap
    pod = box("City_Pod", (5.5, 3.4, 1.4), (px, py, z + 0.7), DARK, rot=(0, 0, a), bevel=0.3)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.6, segments=24, ring_count=12, location=(px, py, z + 1.3))
    dome = bpy.context.object
    dome.name = "City_PodDome"
    dome.scale = (1.4, 1.0, 0.75)
    dome.rotation_euler = (0, 0, a)
    dome.data.materials.append(DARK)
    bpy.ops.object.shade_smooth()
    attach(dome)
    slit = random.choice((NEON_MAG, NEON_ORANGE))
    box("City_PodSlit", (2.4, 0.12, 0.28), (px + 1.0 * math.cos(a), py + 1.0 * math.sin(a), z + 1.5), slit, rot=(0, 0, a + math.pi / 2))
    bx, by = px + 3.4 * math.cos(a), py + 3.4 * math.sin(a)
    cylinder("City_PodBarrel", 0.28, 3.0, (bx, by, z + 1.4), CHROME, verts=12, rot=(0, math.pi / 2, a))
    cylinder("City_PodBarrelTip", 0.34, 0.3, (px + 4.9 * math.cos(a), py + 4.9 * math.sin(a), z + 1.4), NEON_CYAN, verts=12, rot=(0, math.pi / 2, a))
    for s in (-1, 1):                                       # two stubby legs down onto the wall
        box("City_PodLeg", (0.6, 0.6, 1.4), (px - s * 1.8 * math.sin(a), py + s * 1.8 * math.cos(a), z - 0.5), CHROME)

# ------------------------------------------------------------ the dome: sits on the wall top
dome_zc = -20.0
dome_r = math.hypot((R_WALL_IN + R_WALL_OUT) / 2, WALL_H + 1.2 - dome_zc)
bpy.ops.mesh.primitive_uv_sphere_add(radius=dome_r, segments=96, ring_count=48, location=(0, 0, dome_zc))
dome = bpy.context.object
dome.name = "City_Dome"
bm = bmesh.new()
bm.from_mesh(dome.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z + dome_zc < WALL_H + 0.8], context="VERTS")
bm.to_mesh(dome.data)
bm.free()
dome.data.materials.append(FIELD)
bpy.ops.object.shade_smooth()
attach(dome)
# a bright ring where the field meets the wall
annulus("City_DomeBase", (R_WALL_IN + R_WALL_OUT) / 2 - 0.6, (R_WALL_IN + R_WALL_OUT) / 2 + 0.6, WALL_H + 1.25, NEON_BLUE, segs=128)


# ------------------------------------------------------------ vehicles: one mesh each, instanced
def join_into(name, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    o.data.name = name + "Mesh"
    o.data.transform(Matrix.Translation(o.location))       # mesh in root space, origin on the ground
    o.location = (0, 0, 0)
    return o


def make_car():
    parts = [box("carbody", (4.2, 2.0, 1.0), (0, 0, 0.9), CAR_PAINT, bevel=0.25),
             box("carcabin", (2.2, 1.7, 0.8), (-0.2, 0, 1.75), DARK, bevel=0.25),
             box("carglow", (3.6, 1.6, 0.08), (0, 0, 0.42), NEON_CYAN)]
    for s in (-1, 1):
        parts.append(box("carhead", (0.15, 0.5, 0.3), (2.1, s * 0.6, 0.95), HEADLIGHT))
        parts.append(box("cartail", (0.15, 0.5, 0.25), (-2.1, s * 0.6, 0.95), TAILLIGHT))
        for wx in (-1.4, 1.4):
            parts.append(cylinder("carwheel", 0.42, 0.4, (wx, s * 1.0, 0.42), DARK, verts=16, rot=(math.pi / 2, 0, 0)))
    car = join_into("City_CarProto", parts)
    car.location = (0, 0, -50)
    return car


def make_flyer():
    parts = [box("flybody", (4.6, 1.8, 0.9), (0, 0, 0), FLYER_PAINT, bevel=0.35),
             box("flycanopy", (1.8, 1.3, 0.7), (0.3, 0, 0.55), DARK, bevel=0.3),
             box("flyglow", (3.8, 1.2, 0.1), (0, 0, -0.5), NEON_MAG),
             box("flyhead", (0.15, 1.0, 0.2), (2.3, 0, 0.05), HEADLIGHT)]
    for s in (-1, 1):
        parts.append(box("flyfin", (1.6, 0.15, 0.6), (-1.4, s * 1.0, 0.3), FLYER_PAINT, rot=(s * 0.5, 0, 0)))
        parts.append(box("flytail", (0.2, 0.4, 0.25), (-2.3, s * 0.5, 0.0), TAILLIGHT))
        parts.append(cylinder("flypod", 0.45, 0.5, (0.6, s * 1.25, -0.2), CHROME, verts=12))
        parts.append(cylinder("flypodglow", 0.3, 0.1, (0.6, s * 1.25, -0.5), NEON_CYAN, verts=12))
    fl = join_into("City_FlyerProto", parts)
    fl.location = (0, 0, -50)
    return fl


car_proto = make_car()
flyer_proto = make_flyer()
car_proto.hide_render = flyer_proto.hide_render = True
car_proto.hide_viewport = flyer_proto.hide_viewport = True
PALETTE = [(0.9, 0.1, 0.1), (0.1, 0.3, 0.9), (0.95, 0.95, 0.95), (0.1, 0.1, 0.12), (0.9, 0.6, 0.1), (0.2, 0.8, 0.4), (0.6, 0.1, 0.8), (0.9, 0.9, 0.2)]


def instance(proto, name, colour):
    o = bpy.data.objects.new(name, proto.data)
    o.color = (*colour, 1)
    o.rotation_mode = "XYZ"
    col.objects.link(o)
    o.parent = root
    o.matrix_parent_inverse.identity()
    return o


def drive_circle(o, r, z, a0, speed, ccw=True, wobble=0.0, step=6):
    """Keyed around a circle for the whole timeline: heading along the tangent."""
    for f in range(FRAMES[0], FRAMES[1] + step, step):
        t = (f - FRAMES[0]) / FPS
        a = a0 + (speed / r) * t * (1 if ccw else -1)
        zz = z + wobble * math.sin(2 * math.pi * t / 5.0 + a0)
        o.location = (r * math.cos(a), r * math.sin(a), zz)
        o.rotation_euler = (0, 0, a + (math.pi / 2 if ccw else -math.pi / 2))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    for fc in o.animation_data.action.layers[0].strips[0].channelbag(o.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def drive_line(o, p0, p1, z, speed, step=6, phase=0.0):
    """Back and forth along an avenue, turning round at the ends."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    period = 2 * L / speed
    for f in range(FRAMES[0], FRAMES[1] + step, step):
        t = ((f - FRAMES[0]) / FPS + phase * period) % period
        fwd = t < period / 2
        u = (t / (period / 2)) if fwd else 2 - t / (period / 2)
        p = p0.lerp(p1, u)
        d = (p1 - p0) if fwd else (p0 - p1)
        o.location = (p.x, p.y, z)
        o.rotation_euler = (0, 0, math.atan2(d.y, d.x))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    for fc in o.animation_data.action.layers[0].strips[0].channelbag(o.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


# ground cars: two lanes each way on the ring road, and up and down the avenues
n_cars = 0
for lane_r, ccw in ((R_RING - 3.2, True), (R_RING - 1.2, True), (R_RING + 1.2, False), (R_RING + 3.2, False)):
    for k in range(9):
        c = instance(car_proto, "City_Car", random.choice(PALETTE))
        drive_circle(c, lane_r, 0.12, 2 * math.pi * k / 9 + random.uniform(0, 0.5), random.uniform(7, 11), ccw)
        n_cars += 1
for axis in ("x", "y"):
    for lane in (-3.0, -1.2, 1.2, 3.0):
        for k in range(3):
            c = instance(car_proto, "City_Car", random.choice(PALETTE))
            L = R_RING + 3
            half = random.choice((-1, 1))                   # one stretch of the avenue, either side of the plaza
            a, b = (half * 17, half * L) if lane > 0 else (half * L, half * 17)
            p0, p1 = ((a, lane), (b, lane)) if axis == "x" else ((lane, a), (lane, b))
            drive_line(c, p0, p1, 0.12, random.uniform(7, 11), phase=k / 3.0)
            n_cars += 1
# flying cars: lanes at several heights, both ways, with a gentle bob
n_fly = 0
for lane_r, z, ccw in ((26, 22, True), (38, 30, False), (50, 26, True), (60, 40, False), (34, 48, True), (46, 58, False), (66, 34, True), (20, 66, False)):
    for k in range(5):
        fl = instance(flyer_proto, "City_Flyer", random.choice(PALETTE))
        drive_circle(fl, lane_r + random.uniform(-2, 2), z + random.uniform(-2, 2), 2 * math.pi * k / 5 + random.uniform(0, 0.8),
                     random.uniform(14, 24), ccw, wobble=0.6)
        n_fly += 1
# a few flyers crossing straight over the city
for k in range(8):
    fl = instance(flyer_proto, "City_Flyer", random.choice(PALETTE))
    a = random.uniform(0, 2 * math.pi)
    d = Vector((math.cos(a), math.sin(a)))
    z = random.uniform(30, 70)
    drive_line(fl, tuple(-d * 74), tuple(d * 74), z, random.uniform(16, 26), phase=random.random())
    n_fly += 1

# ------------------------------------------------------------ light: the city glows at street level
for i in range(6):
    a = 2 * math.pi * i / 6
    L = bpy.data.lights.new("CityGlow%d" % i, "POINT")
    L.energy = 4000
    L.color = random.choice(((1.0, 0.3, 0.8), (0.3, 0.8, 1.0), (0.4, 0.5, 1.0)))
    L.shadow_soft_size = 6
    L.use_shadow = False
    lo = bpy.data.objects.new("City_Glow%d" % i, L)
    lo.location = (40 * math.cos(a), 40 * math.sin(a), 18)
    scene.collection.objects.link(lo)
    attach(lo)

# a camera for the check views
camd = bpy.data.cameras.new("CityCam")
camd.lens = 30
camd.clip_end = 5000
citycam = bpy.data.objects.new("CityCam", camd)
scene.collection.objects.link(citycam)
attach(citycam)

bpy.ops.object.select_all(action="DESELECT")
print("city built:", len(col.objects), "objects |", towers, "towers |", n_cars, "cars |", n_fly, "flyers | gate at %.0f deg" % math.degrees(GATE_ANGLE),
      "| dome r %.1f" % dome_r)
