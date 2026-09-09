"""A giant neon cyber city under a forcefield dome, in the far corner of the
plate. Built from the drawing: a ring wall of tough stone round the bottom
with a car-sized turret pod on top every 45 degrees, an arched forcefield gate
in the front of the wall (the side facing the plate), and a simple forcefield
dome sitting on the wall top over everything. Inside: a street grid with two
lit avenues and a ring road, a hundred-odd towers stepping up toward the
centre, each one mesh with real recessed windows and balconies, neon edges,
antennas and holographic billboards; cars with people in them on the ring
road and avenues, flying cars on lanes at several heights, people walking
the sidewalks, lamp posts, benches, kiosks, planters, drones and floating ads. Everything hangs off the "City" empty; cars are keyed for
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


def neon(name, rgb, strength=14.0):
    return plain(name, rgb, rough=0.3, emit=rgb, strength=strength)


def building_mat(name, tint, warm, rough=0.45, metallic=0.35):
    """Facade panels: a dark tinted cladding with a faint panel grid in the
    bump only (the windows are real geometry)."""
    m, nt, bsdf, _ = new_mat(name)
    bsdf.inputs["Base Color"].default_value = (*tint, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 0.6
    brick.inputs["Mortar Size"].default_value = 0.04
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
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
FACADES = [building_mat("CityFacade%d" % i, tint, None, rough, metallic) for i, (tint, rough, metallic) in enumerate((
    ((0.10, 0.11, 0.14), 0.45, 0.35), ((0.13, 0.11, 0.15), 0.45, 0.35), ((0.08, 0.10, 0.12), 0.3, 0.6),      # dark claddings
    ((0.17, 0.165, 0.155), 0.7, 0.05), ((0.21, 0.205, 0.195), 0.75, 0.0),                                  # concrete panel
    ((0.32, 0.34, 0.38), 0.3, 0.85), ((0.22, 0.24, 0.28), 0.25, 0.9),                                       # brushed metal
    ((0.45, 0.12, 0.18), 0.5, 0.2), ((0.12, 0.3, 0.42), 0.5, 0.2), ((0.5, 0.35, 0.12), 0.5, 0.2)))]        # coloured composite accents
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
CONCRETE = plain("CityConcrete", (0.16, 0.16, 0.17), rough=0.75)
CONCRETE_KERB = plain("CityKerb", (0.22, 0.22, 0.24), rough=0.85)
annulus("City_Ground", 0.01, R_WALL_OUT + 6, 0.04, PAVEMENT, segs=128)
annulus("City_RingRoad", R_RING - 5, R_RING + 5, 0.08, ASPHALT)
annulus("City_RingLaneOut", R_RING + 4.6, R_RING + 4.9, 0.1, NEON_LANE)
annulus("City_RingLaneIn", R_RING - 4.9, R_RING - 4.6, 0.1, NEON_LANE)
annulus("City_RingLaneMid", R_RING - 0.15, R_RING + 0.15, 0.1, NEON_LANE)
annulus("City_RingKerbOut", R_RING + 5, R_RING + 8.5, 0.16, CONCRETE_KERB)      # the sidewalks
annulus("City_RingKerbIn", R_RING - 8.5, R_RING - 5, 0.16, CONCRETE_KERB)
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
        walk = (L, 3.2, 0.12) if axis == "x" else (3.2, L, 0.12)
        wpos = (0, s * 6.7, 0.14) if axis == "x" else (s * 6.7, 0, 0.14)
        box("City_Sidewalk_" + axis, walk, wpos, CONCRETE_KERB)
GLASS_LIT = plain("CityGlassLit", (0.9, 0.8, 0.6), rough=0.15, metallic=0.2, emit=(1.0, 0.85, 0.55), strength=1.1)
ROOM = plain("CityRoom", (0.3, 0.24, 0.18), rough=0.9, emit=(1.0, 0.8, 0.55), strength=0.35)
ROOM_COOL = plain("CityRoomCool", (0.18, 0.24, 0.3), rough=0.9, emit=(0.6, 0.8, 1.0), strength=0.35)
GLASS_COOL = plain("CityGlassCool", (0.6, 0.85, 1.0), rough=0.15, metallic=0.2, emit=(0.55, 0.85, 1.0), strength=2.2)
GLASS_DARK = plain("CityGlassDark", (0.03, 0.05, 0.08), rough=0.08, metallic=0.9)
INTERIOR = plain("CityInterior", (0.08, 0.06, 0.05), rough=0.9, emit=(0.9, 0.6, 0.3), strength=0.6)
RAILING = plain("CityRailing", (0.5, 0.75, 0.9), rough=0.1, metallic=0.6)
TOWER_SLOTS = [None, GLASS_LIT, GLASS_DARK, CONCRETE, INTERIOR, RAILING, GLASS_COOL, ROOM, ROOM_COOL]

# a central plaza with a spire
cylinder("City_Plaza", 14, 0.3, (0, 0, 0.15), DARK, verts=48)
annulus("City_PlazaRing", 13.5, 14.2, 0.32, NEON_CYAN, segs=64)
GRASS = plain("CityGrass", (0.12, 0.42, 0.2), rough=0.95)
annulus("City_Park", 14.2, 17.5, 0.2, GRASS, segs=64)
annulus("City_ParkKerb", 17.5, 18.2, 0.24, CONCRETE_KERB, segs=64)
WATER = plain("CityWater", (0.2, 0.55, 0.85), rough=0.05, metallic=0.2, emit=(0.15, 0.45, 0.8), strength=0.5)
cylinder("City_FountainBasin", 6.5, 0.9, (0, 0, 0.75), CONCRETE, verts=48)
cylinder("City_FountainWater", 6.1, 0.15, (0, 0, 1.15), WATER, verts=48)
annulus("City_FountainRim", 6.4, 6.7, 1.22, NEON_CYAN, segs=48)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=3.6, radius2=1.3, depth=70, location=(0, 0, 35))
spire = bpy.context.object
spire.name = "City_Spire"
spire.data.materials.append(GLASS_COOL)
bpy.ops.object.shade_smooth()
attach(spire)
for k in range(8):                                          # lit seams up the shaft
    a = 2 * math.pi * k / 8
    for zz, rr in ((10, 3.25), (30, 2.6), (50, 1.95), (65, 1.45)):
        box("City_SpireSeam", (0.16, 0.16, 18), (rr * math.cos(a), rr * math.sin(a), zz), NEON_CYAN, rot=(0, 0, a))
cylinder("City_SpireBase", 5.5, 4.0, (0, 0, 2.0), DARK, verts=32)
cylinder("City_ObsDeck", 6.5, 0.5, (0, 0, 46.0), DARK, verts=32)
cylinder("City_ObsGlass", 6.2, 3.2, (0, 0, 48.0), GLASS_COOL, verts=32)
cylinder("City_ObsRoof", 6.6, 0.5, (0, 0, 49.8), DARK, verts=32)
annulus("City_ObsNeon", 6.5, 6.9, 46.3, NEON_MAG, segs=48)
holo = annulus("City_HoloRing", 4.0, 5.6, 72.0, NEON_CYAN, segs=48)
for f in (FRAMES[0], FRAMES[1]):
    holo.rotation_euler = (math.radians(12), 0, (f - FRAMES[0]) / FPS * 0.6)
    holo.keyframe_insert("rotation_euler", frame=f)
cylinder("City_SpireMast", 0.3, 12, (0, 0, 76), CHROME, verts=8)
cylinder("City_SpireBlink", 0.6, 0.6, (0, 0, 82.3), TAILLIGHT, verts=8)

# ------------------------------------------------------------ the towers
# One mesh per tower body: the footprint polygon is walked in piers and
# windows, every floor is a spandrel, a window row and a lintel, and the
# window quads are inset and recessed, lit or dark at random. Residential
# floors get balconies: the spandrel comes out as a slab with a railing and
# the window behind it becomes a doorway. Six silhouettes on top of that.


def facade_tower(name, footprint, h, facade, x, y, z0=0.0, floor_h=3.4, balconies=False, lit=0.55, cool=False):
    """A tower body from a footprint polygon (counter-clockwise, around 0,0)."""
    bm = bmesh.new()
    n = len(footprint)
    floors = max(1, int(round(h / floor_h)))
    fh = h / floors
    zs = [z0]
    for f in range(floors):
        base = z0 + f * fh
        zs += [base + 0.95, base + fh - 0.55, base + fh]
    perim, kinds = [], []
    for i in range(n):
        p0, p1 = Vector(footprint[i]), Vector(footprint[(i + 1) % n])
        L = (p1 - p0).length
        cols = max(1, int(round(L / 2.4)))
        pier = min(0.5, L * 0.12)
        win = (L - pier * (cols + 1)) / cols
        t = 0.0
        for c in range(cols):
            perim.append(p0.lerp(p1, t / L)); kinds.append("pier")
            t += pier
            perim.append(p0.lerp(p1, t / L)); kinds.append("win")
            t += win
        perim.append(p0.lerp(p1, t / L)); kinds.append("pier")
    m = len(perim)
    rings = [[bm.verts.new((p.x + x, p.y + y, z)) for p in perim] for z in zs]
    faces = {}
    for zi in range(len(zs) - 1):
        for pi in range(m):
            pj = (pi + 1) % m
            f = bm.faces.new((rings[zi][pi], rings[zi][pj], rings[zi + 1][pj], rings[zi + 1][pi]))
            faces[(zi, pi)] = f
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    balcony_floors = set(range(1, floors, 2)) if balconies else set()
    windows, balc_slabs, doors = [], [], []
    for (zi, pi), f in faces.items():
        row = zi % 3                                        # 0 spandrel, 1 window, 2 lintel
        floor = zi // 3
        if kinds[pi] != "win":
            continue
        if floor in balcony_floors and row == 0:
            balc_slabs.append(f)
        elif floor in balcony_floors and row == 1:
            doors.append(f)
        elif row == 1:
            windows.append(f)
    # windows: a frame and a recess
    if windows:
        inner = bmesh.ops.inset_individual(bm, faces=windows, thickness=0.14, depth=0.0, use_even_offset=True)["faces"]
        for f in inner:
            lit_win = random.random() < lit
            reveal = {lf for e in f.edges for lf in e.link_faces if lf is not f}
            bmesh.ops.translate(bm, verts=f.verts, vec=-f.normal * (0.42 if lit_win else 0.2))
            f.material_index = (6 if cool else 1) if lit_win else 2
            if lit_win:                                     # the room behind the glass: lit walls, floor and ceiling
                for lf in reveal:
                    lf.material_index = 8 if cool else 7
    # balconies: the slab comes out, a railing rises off its outer edge, the doorway goes in
    for f in balc_slabs:
        normal = f.normal.copy()
        nf = bmesh.ops.extrude_discrete_faces(bm, faces=[f])["faces"][0]
        bmesh.ops.translate(bm, verts=nf.verts, vec=normal * 0.9)
        nf.material_index = 3
        top = max(v.co.z for v in nf.verts)
        top_edges = [e for e in nf.edges if all(abs(v.co.z - top) < 1e-4 for v in e.verts)]
        if top_edges:
            rail = bmesh.ops.extrude_edge_only(bm, edges=top_edges)["geom"]
            rverts = [g for g in rail if isinstance(g, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=rverts, vec=(0, 0, 0.75))
            for g in rail:
                if isinstance(g, bmesh.types.BMFace):
                    g.material_index = 5
    if doors:
        inner = bmesh.ops.inset_individual(bm, faces=doors, thickness=0.12, depth=0.0, use_even_offset=True)["faces"]
        for f in inner:
            bmesh.ops.translate(bm, verts=f.verts, vec=-f.normal * 0.7)
            f.material_index = 4 if random.random() < 0.5 else 2
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(o)
    for slot in TOWER_SLOTS:
        o.data.materials.append(slot or facade)
    attach(o)
    return o


def rect(w, d):
    return [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]


def ngon(r, n):
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def frange(a, b, step):
    v = a
    while v < b:
        yield v
        v += step


def ledge(x, y, w, d, z, mat=DARK, lip=0.35, h=0.35):
    box("City_Ledge", (w + 2 * lip, d + 2 * lip, h), (x, y, z), mat)


def strips(x, y, w, d, z0, z1, corners, mat):
    for sx, sy in corners:
        box("City_TowerStrip", (0.2, 0.2, (z1 - z0) * 0.9), (x + sx * w / 2, y + sy * d / 2, (z0 + z1) / 2), mat)


LOBBIES = []
SHOPS = []


def podium(x, y, w, d, facade):
    ph = random.choice((3.4, 6.8))
    pw, pd = w + random.uniform(2.5, 4.5), d + random.uniform(2.5, 4.5)
    pw = min(pw, 2 * (abs(x) - 9.0))                          # never onto the avenue sidewalks
    pd = min(pd, 2 * (abs(y) - 9.0))
    if pw < w or pd < d:
        pw, pd = max(pw, w), max(pd, d)
    if ph > 3.5:
        facade_tower("City_Podium", rect(pw, pd), ph - 3.4, facade, x, y, z0=3.4, lit=0.8, cool=True)
    else:
        box("City_PodiumSlab", (pw, pd, 0.4), (x, y, 3.2), DARK)
    LOBBIES.append((x, y, pw, pd))
    ledge(x, y, pw, pd, ph + 0.15, lip=0.6, h=0.3)
    box("City_PodiumBand", (pw + 0.12, pd + 0.12, 0.22), (x, y, ph - 0.5), random.choice(NEONS))
    sx, sy = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
    box("City_Canopy", (3.2 if sy else 1.0, 1.0 if sy else 3.2, 0.15), (x + sx * (pw / 2 + 0.5), y + sy * (pd / 2 + 0.5), 2.7), DARK)
    box("City_CanopyLight", (2.8 if sy else 0.12, 0.12 if sy else 2.8, 0.12), (x + sx * (pw / 2 + 0.9), y + sy * (pd / 2 + 0.9), 2.6), NEON_CYAN)
    box("City_Door", (2.0 if sy else 0.1, 0.1 if sy else 2.0, 2.4), (x + sx * (pw / 2 + 0.02), y + sy * (pd / 2 + 0.02), 1.2), GLASS_COOL)
    return ph


def roof_clutter(x, y, w, d, z, h):
    box("City_TowerCap", (w * 1.04, d * 1.04, 0.5), (x, y, z + 0.25), DARK)
    for k in range(random.randint(1, 3)):
        mw, md, mh = random.uniform(1.0, 2.2), random.uniform(1.0, 2.2), random.uniform(0.8, 1.8)
        box("City_RoofBox", (mw, md, mh), (x + random.uniform(-w / 2 + 1.3, w / 2 - 1.3), y + random.uniform(-d / 2 + 1.3, d / 2 - 1.3), z + 0.5 + mh / 2), CONCRETE)
    if random.random() < 0.4:
        cylinder("City_Tank", 0.8, 1.6, (x + random.uniform(-w / 3, w / 3), y + random.uniform(-d / 3, d / 3), z + 1.3), CHROME, verts=16)
    if random.random() < 0.25:
        ah = random.uniform(h * 0.15, h * 0.3)
        ax, ay = x + random.uniform(-w / 4, w / 4), y + random.uniform(-d / 4, d / 4)
        cylinder("City_Antenna", 0.18, ah, (ax, ay, z + 0.5 + ah / 2), CHROME, verts=8)
        for k in range(3):
            cylinder("City_AntennaRing", 0.45, 0.12, (ax, ay, z + 0.5 + ah * (0.5 + 0.17 * k)), random.choice(NEONS), verts=12)
        cylinder("City_AntennaTip", 0.3, 0.5, (ax, ay, z + 0.5 + ah), TAILLIGHT, verts=8)
    if random.random() < 0.3 and h > 35:
        r = min(w, d) * 0.3
        annulus("City_Helipad", r, r * 1.18, z + 0.52, NEON_ORANGE, segs=24)
        box("City_HelipadH", (r * 0.5, 0.25, 0.03), (x, y, z + 0.53), NEON_ORANGE)


def style_tiers(x, y, w, d, h, z, facade, res):
    tiers = random.choice((2, 3, 3)) if h > 30 else random.choice((1, 2))
    tw, td = w, d
    for t in range(tiers):
        th = h / tiers * random.uniform(0.8, 1.2)
        facade_tower("City_Tower", rect(tw, td), th, facade, x, y, z0=z, balconies=res)
        ledge(x, y, tw, td, z + 0.2)
        strips(x, y, tw, td, z, z + th, random.choice((((1, 1), (-1, -1)), ((1, -1), (-1, 1)), ((1, 1), (1, -1), (-1, 1), (-1, -1)))), random.choice(NEONS))
        z += th
        tw *= random.uniform(0.66, 0.84)
        td *= random.uniform(0.66, 0.84)
    return z, tw, td


def style_cylinder(x, y, w, d, h, z, facade, res):
    r = (w + d) / 4
    facade_tower("City_Tower", ngon(r, 20), h, facade, x, y, z0=z, balconies=res)
    for rz in frange(z + 7, z + h - 3, 8):
        cylinder("City_Ring", r + 0.35, 0.3, (x, y, rz), DARK, verts=28)
    cylinder("City_RingNeon", r + 0.12, 0.15, (x, y, z + h - 1.0), random.choice(NEONS), verts=28)
    facade_tower("City_Crown", ngon(r * 0.6, 20), 3.4, facade, x, y, z0=z + h, cool=True)
    cylinder("City_CrownNeon", r * 0.62, 0.2, (x, y, z + h + 3.5), NEON_CYAN, verts=28)
    return z + h + 3.4, r * 1.2, r * 1.2


def style_slab(x, y, w, d, h, z, facade, res):
    sw, sd = w * 1.5, d * 0.6
    facade_tower("City_Tower", rect(sw, sd), h, facade, x, y, z0=z, balconies=res, cool=True)
    for fz in frange(z + 4, z + h - 1, 6.8):
        box("City_Fin", (sw + 0.6, sd + 0.5, 0.18), (x, y, fz), DARK)
    strips(x, y, sw, sd, z, z + h, ((1, 1), (-1, 1), (1, -1), (-1, -1)), random.choice(NEONS))
    for k in (-1, 0, 1):
        mh = random.uniform(4, 9)
        cylinder("City_Mast", 0.15, mh, (x + k * sw * 0.3, y, z + h + mh / 2), CHROME, verts=8)
        cylinder("City_MastTip", 0.25, 0.4, (x + k * sw * 0.3, y, z + h + mh), TAILLIGHT, verts=8)
    return z + h, sw, sd


def style_twin(x, y, w, d, h, z, facade, res):
    tw = w * 0.52
    gap = 2.6
    for s in (-1, 1):
        cx = x + s * (tw / 2 + gap / 2)
        facade_tower("City_Tower", rect(tw, d), h, facade, cx, y, z0=z, balconies=res)
        strips(cx, y, tw, d, z, z + h, ((-s, 1), (-s, -1)), random.choice(NEONS))
    for u in (0.45, 0.75):
        bz = z + h * u
        box("City_Bridge", (gap + 1.0, d * 0.45, 1.6), (x, y, bz), GLASS_COOL, bevel=0.1)
        box("City_BridgeLight", (gap + 0.6, d * 0.45 + 0.1, 0.12), (x, y, bz - 0.85), NEON_CYAN)
    box("City_TwinCap", (w * 1.1, d * 1.04, 0.5), (x, y, z + h + 0.25), DARK)
    return z + h, tw, d


def style_taper(x, y, w, d, h, z, facade, res):
    tw, td = w * 1.1, d * 1.1
    steps = 4
    for k in range(steps):
        th = h / steps
        facade_tower("City_Tower", rect(tw, td), th, facade, x, y, z0=z, balconies=res)
        ledge(x, y, tw, td, z + th - 0.15, lip=0.25, h=0.3)
        z += th
        tw *= 0.8
        td *= 0.8
    cylinder("City_Spike", 0.3, 8.0, (x, y, z + 4.0), CHROME, verts=8)
    cylinder("City_SpikeNeon", 0.4, 2.0, (x, y, z + 7.5), random.choice(NEONS), verts=8)
    return z, tw, td


def style_hex(x, y, w, d, h, z, facade, res):
    r = (w + d) / 3.4
    facade_tower("City_Tower", ngon(r, 6), h, facade, x, y, z0=z, balconies=res)
    for rz in frange(z + 6, z + h - 2, 7):
        cylinder("City_Ring", r + 0.3, 0.25, (x, y, rz), DARK, verts=6)
    mat = random.choice(NEONS)
    for k in range(3):
        a = math.radians(60 + 120 * k)
        box("City_TowerStrip", (0.22, 0.22, h * 0.92), (x + r * math.cos(a), y + r * math.sin(a), z + h / 2), mat, rot=(0, 0, a))
    cylinder("City_HexCap", r * 1.05, 0.5, (x, y, z + h + 0.25), DARK, verts=6)
    cylinder("City_HexNeon", r * 0.5, 0.3, (x, y, z + h + 0.6), mat, verts=6)
    return z + h + 0.6, r * 1.4, r * 1.4


def sector_neons(x, y):
    a = (math.atan2(y, x) + 2 * math.pi) % (2 * math.pi)
    return [(NEON_CYAN, NEON_BLUE), (NEON_MAG, NEON_CYAN), (NEON_ORANGE, NEON_MAG), (NEON_BLUE, NEON_ORANGE)][int(a / (math.pi / 2)) % 4]


SPACING = 11.0
towers = 0
cells = []
n_cells = int(R_CITY / SPACING) + 1
for i in range(-n_cells, n_cells + 1):
    for j in range(-n_cells, n_cells + 1):
        x, y = i * SPACING, j * SPACING
        if abs(x) < 8.5 or abs(y) < 8.5:                   # the avenues and their sidewalks
            continue
        d = math.hypot(x, y)
        if d > R_CITY - 4 or abs(d - R_RING) < 9.5 or d < 17:
            continue
        cells.append((x, y, d))
def style_twist(x, y, w, d, h, z, facade, res):
    tiers = 8
    tw, td = w * 1.15, d * 1.15
    for t in range(tiers):
        th = h / tiers
        a = math.radians(6.0 * t)
        R = Matrix.Rotation(a, 2)
        fp = [tuple(R @ Vector(pt)) for pt in rect(tw, td)]
        facade_tower("City_Tower", fp, th, facade, x, y, z0=z, balconies=False, cool=True, lit=0.65)
        z += th
        tw *= 0.96
        td *= 0.96
    cylinder("City_TwistCrown", max(tw, td) * 0.6, 0.4, (x, y, z + 0.2), NEON_CYAN, verts=24)
    return z, tw, td


def style_ringcrown(x, y, w, d, h, z, facade, res):
    r = (w + d) / 3.2
    facade_tower("City_Tower", ngon(r, 24), h, facade, x, y, z0=z, cool=True, lit=0.7)
    for rz in frange(z + 8, z + h - 4, 9):
        cylinder("City_Ring", r + 0.4, 0.3, (x, y, rz), DARK, verts=28)
    cylinder("City_CrownRing", r * 2.2, 1.2, (x, y, z + h + 2.0), DARK, verts=36)
    annulus("City_CrownNeonTop", r * 1.9, r * 2.25, z + h + 2.62, NEON_MAG, segs=48)
    annulus("City_CrownNeonBot", r * 1.9, r * 2.25, z + h + 1.38, NEON_MAG, segs=48)
    for k in range(4):
        a = math.radians(90 * k + 45)
        box("City_CrownStrut", (0.5, 0.5, 2.6), (x + r * 1.6 * math.cos(a), y + r * 1.6 * math.sin(a), z + h + 1.0), CHROME)
    cylinder("City_CrownSpike", 0.35, 10.0, (x, y, z + h + 7.6), CHROME, verts=8)
    cylinder("City_CrownBlink", 0.5, 0.5, (x, y, z + h + 12.6), TAILLIGHT, verts=8)
    return z + h + 2.6, r * 2, r * 2


STYLES = [(style_tiers, 4), (style_cylinder, 2), (style_slab, 2), (style_twin, 1), (style_taper, 1), (style_hex, 2)]
LANDMARKS = {}
for ang, sty in ((25, style_twist), (140, style_ringcrown), (255, style_twin), (330, style_taper)):
    best = min(cells, key=lambda c: abs(math.hypot(c[0], c[1]) - 42) + 0.4 * abs((math.degrees(math.atan2(c[1], c[0])) - ang + 180) % 360 - 180))
    LANDMARKS[(best[0], best[1])] = sty
for x, y, d in cells:
    falloff = max(0.0, 1 - d / R_CITY)
    h = 14 + 62 * falloff ** 1.3 * random.uniform(0.55, 1.25)
    w = random.uniform(5.5, 8.5)
    dpt = random.uniform(5.5, 8.5)
    facade = random.choice(FACADES)
    style = random.choice([s for s, n in STYLES for _ in range(n)])
    if (x, y) in LANDMARKS:
        style = LANDMARKS[(x, y)]
        h = h * 1.9
        w, dpt = w * 1.3, dpt * 1.3
    res = random.random() < 0.45                            # residential: balconies
    NEONS[:] = list(sector_neons(x, y)) + [random.choice((NEON_CYAN, NEON_MAG, NEON_BLUE, NEON_ORANGE))]
    z = podium(x, y, w, dpt, facade) if (h > 24 and random.random() < 0.6) else 0.0
    top, tw, td = style(x, y, w, dpt, h, z, facade, res)
    roof_clutter(x, y, tw, td, top, h)
    if h > 45 and random.random() < 0.6:
        side = random.choice(("x", "y"))
        sgn = random.choice((-1, 1))
        bz = top * random.uniform(0.45, 0.75)
        bw, bh = random.uniform(6, 9), random.uniform(8, 12)
        bb = box("City_Billboard", (0.3, bw, bh) if side == "x" else (bw, 0.3, bh),
                 (x + sgn * (w / 2 + 0.8), y, bz) if side == "x" else (x, y + sgn * (dpt / 2 + 0.8), bz), random.choice(NEONS))
        bb["hologram"] = 1
        bb["out"] = (sgn if side == "x" else 0, sgn if side == "y" else 0)
    towers += 1
# street level between the towers: shops (built once the citizens exist)
for x, y, d in cells:
    for k in range(2):
        sx_ = x + random.choice((-1, 1)) * 7.2                 # beside the tower, never on a sidewalk or an avenue
        sy_ = y + random.uniform(-3.0, 3.0)
        if abs(sx_) < 13.0 or abs(sy_) < 13.0 or abs(math.hypot(sx_, sy_) - R_RING) < 10.5 or math.hypot(sx_, sy_) > R_CITY - 6:
            continue
        SHOPS.append((sx_, sy_))

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
    # big floating ads over the avenues, turning slowly
    for k in range(6):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        p = bpy.context.object
        p.name = "City_FloatAd"
        p.scale = (9.0, 13.0, 1)
        along = random.choice(("x", "y"))
        pos = random.uniform(-52, 52)
        p.location = (pos, random.choice((-1, 1)) * 12, 18) if along == "x" else (random.choice((-1, 1)) * 12, pos, 18)
        p.rotation_euler = (math.radians(90), 0, 0)
        p.data.materials.append(hud_mat)
        attach(p)
        for f in (FRAMES[0], FRAMES[1]):
            p.rotation_euler = (math.radians(90), 0, (f - FRAMES[0]) / FPS * 0.25)
            p.keyframe_insert("rotation_euler", frame=f)

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



# ------------------------------------------------------------ vehicles: one smooth mesh per type, instanced
def see_through_glass(name, rgb, alpha=0.4):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = "BLEND"
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Alpha"].default_value = alpha
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = (*rgb, alpha)
    return m


GLASS_CAR = see_through_glass("CityCarGlass", (0.5, 0.7, 0.85), alpha=0.35)
SKINS = [plain("CitySkin%d" % i, c, rough=0.7) for i, c in enumerate(((1.0, 0.72, 0.08), (0.2, 0.5, 0.95), (0.9, 0.25, 0.3), (0.3, 0.8, 0.45),
                                                                     (0.95, 0.55, 0.85), (0.95, 0.95, 0.9), (0.55, 0.3, 0.8), (1.0, 0.6, 0.15)))]
CLOTH = [plain("CityCloth%d" % i, c, rough=0.9) for i, c in enumerate(((0.12, 0.12, 0.14), (0.25, 0.2, 0.35), (0.1, 0.25, 0.3), (0.35, 0.12, 0.12), (0.2, 0.3, 0.2)))]


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


def apply_all(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def profile_body(name, pts, width, mat, glass_z=None, bevel=0.14, taper=0.0, arches=()):
    """A body from a side profile (x along, z up) extruded across `width`,
    narrowed toward the ends by `taper`, bevelled and subdivided smooth, with
    wheel arches cut where `arches` lists (x, radius). Side faces above
    `glass_z` are glass."""
    bm = bmesh.new()
    xs = [px for px, _ in pts]
    xc, half = (max(xs) + min(xs)) / 2, (max(xs) - min(xs)) / 2
    def wid(px):
        return width * (1 - taper * ((px - xc) / half) ** 2)
    front = [bm.verts.new((px, -wid(px) / 2, pz)) for px, pz in pts]
    back = [bm.verts.new((px, wid(px) / 2, pz)) for px, pz in pts]
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.data.materials.append(GLASS_CAR)
    if glass_z is not None:
        for poly in o.data.polygons:
            if poly.center.z > glass_z and poly.normal.z < 0.7:
                poly.material_index = 1
    attach(o)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = bevel
    b.segments = 4
    b.limit_method = "ANGLE"
    sub = o.modifiers.new("Smooth", "SUBSURF")
    sub.levels = 1
    if arches:
        cutter_parts = []
        for ax, ar in arches:
            for s in (-1, 1):
                cutter_parts.append(cylinder("cut", ar, 0.9, (ax, s * width / 2, ar - 0.05), DARK, verts=24, rot=(math.pi / 2, 0, 0)))
        cutter = join_into("cutter", cutter_parts)
        cutter.location = (0, 0, 0)
        bo = o.modifiers.new("Arches", "BOOLEAN")
        bo.object = cutter
        bo.operation = "DIFFERENCE"
        apply_all(o)
        bpy.data.objects.remove(cutter, do_unlink=True)
    else:
        apply_all(o)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    return o


def wheel(x, y, r=0.45, w=0.42):
    parts = [cylinder("tyre", r, w, (x, y, r), DARK, verts=28, rot=(math.pi / 2, 0, 0)),
             cylinder("rim", r * 0.62, w + 0.04, (x, y, r), CHROME, verts=20, rot=(math.pi / 2, 0, 0)),
             cylinder("hub", r * 0.18, w + 0.08, (x, y, r), NEON_CYAN, verts=12, rot=(math.pi / 2, 0, 0))]
    for k in range(5):
        a = 2 * math.pi * k / 5
        parts.append(box("spoke", (r * 0.42, 0.06, 0.1), (x + r * 0.3 * math.cos(a), y, r + r * 0.3 * math.sin(a)), DARK, rot=(0, -a, 0)))
    return parts


def person(x, y, z, skin, cloth, seated=False, scale=1.0):
    """A small figure: head, body, arms; seated ones are shorter and lean."""
    s = scale
    parts = []
    body_h = 0.9 * s if seated else 1.25 * s
    parts.append(cylinder("torso", 0.36 * s, body_h, (x, y, z + body_h / 2), cloth, verts=14))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3 * s, segments=16, ring_count=10, location=(x, y, z + body_h + 0.28 * s))
    head = bpy.context.object
    head.name = "head"
    head.data.materials.append(skin)
    bpy.ops.object.shade_smooth()
    attach(head)
    parts.append(head)
    for side in (-1, 1):
        parts.append(cylinder("arm", 0.11 * s, 0.8 * s, (x + (0.15 * s if seated else 0), y + side * 0.42 * s, z + body_h * 0.6),
                              cloth, verts=8, rot=(0, math.radians(35) if seated else 0, 0)))
    if not seated:
        for side in (-1, 1):
            parts.append(cylinder("leg", 0.13 * s, 1.2 * s, (x, y + side * 0.16 * s, z - 0.6 * s + 0.02), cloth, verts=8))
    return parts


CAR_KINDS = ("sedan", "sport", "van", "bus")


def make_car(kind, variant):
    if kind == "sedan":
        pts = [(2.3, 0.5), (2.45, 0.9), (2.2, 1.1), (1.0, 1.15), (0.5, 1.75), (-0.8, 1.8), (-1.6, 1.3), (-2.3, 1.2), (-2.4, 0.9), (-2.3, 0.5)]
        width, glass, wheels, L, seat = 2.0, 1.2, ((1.5, 0.45), (-1.5, 0.45)), 2.45, (0.1, 0.62)
    elif kind == "sport":
        pts = [(2.4, 0.4), (2.55, 0.75), (1.0, 0.95), (0.3, 1.4), (-1.0, 1.45), (-1.9, 1.05), (-2.4, 1.0), (-2.5, 0.6), (-2.4, 0.4)]
        width, glass, wheels, L, seat = 2.1, 1.0, ((1.55, 0.47), (-1.5, 0.47)), 2.5, (-0.2, 0.5)
    elif kind == "van":
        pts = [(2.4, 0.5), (2.6, 1.0), (2.3, 1.5), (1.6, 2.3), (-2.5, 2.4), (-2.6, 0.5)]
        width, glass, wheels, L, seat = 2.1, 1.55, ((1.5, 0.47), (-1.6, 0.47)), 2.6, (1.2, 0.85)
    else:
        pts = [(4.0, 0.5), (4.15, 1.2), (4.0, 2.7), (-4.0, 2.7), (-4.15, 1.2), (-4.0, 0.5)]
        width, glass, wheels, L, seat = 2.3, 1.6, ((2.8, 0.5), (-2.6, 0.5)), 4.15, (3.0, 0.9)
    body = profile_body("carbody", pts, width, CAR_PAINT, glass_z=glass, taper=0.12 if kind != "bus" else 0.03,
                        arches=[(wx, wr + 0.14) for wx, wr in wheels])
    parts = [body]
    for wx, wr in wheels:
        for s in (-1, 1):
            parts += wheel(wx, s * (width / 2 - 0.08), r=wr)
    hz = 0.85 if kind != "bus" else 1.0
    parts.append(box("bumperF", (0.25, width * 0.9, 0.3), (L - 0.05, 0, 0.6), DARK, bevel=0.06))
    parts.append(box("bumperR", (0.25, width * 0.9, 0.3), (-L + 0.05, 0, 0.6), DARK, bevel=0.06))
    parts.append(box("plate", (0.05, 0.7, 0.2), (-L - 0.1, 0, 0.6), HEADLIGHT))
    for s in (-1, 1):
        parts.append(box("head", (0.12, 0.42, 0.22), (L + 0.02, s * (width / 2 - 0.4), hz), HEADLIGHT))
        parts.append(box("mirror", (0.25, 0.3, 0.18), (0.9 if kind != "bus" else 3.4, s * (width / 2 + 0.2), glass + 0.25), DARK))
        parts.append(box("handle", (0.3, 0.05, 0.08), (-0.2, s * (width / 2 * 0.98), glass - 0.15), CHROME))
        # door seams
        for dx in ((0.7, -0.9) if kind != "bus" else (2.0, -0.5, -3.0)):
            parts.append(box("seam", (0.03, 0.03, glass - 0.55), (dx, s * (width / 2 * 0.99), (glass + 0.5) / 2), DARK))
    parts.append(box("tail", (0.1, width * 0.8, 0.16), (-L - 0.02, 0, hz), TAILLIGHT))
    parts.append(box("glow", (L * 1.5, width * 0.7, 0.06), (0, 0, 0.3), random.choice((NEON_CYAN, NEON_MAG, NEON_BLUE))))
    if kind == "sport":
        parts.append(box("spoiler", (0.5, width * 0.95, 0.08), (-2.2, 0, 1.45), DARK))
        for s in (-1, 1):
            parts.append(box("spoilerLeg", (0.12, 0.12, 0.4), (-2.2, s * (width * 0.4), 1.2), DARK))
    if kind == "bus":
        parts.append(box("busSign", (0.1, 1.6, 0.35), (4.16, 0, 2.2), NEON_ORANGE))
        parts.append(box("busRoof", (7.0, 1.6, 0.25), (0, 0, 2.8), DARK, bevel=0.06))
    # people inside: a driver, and passengers by variant
    sx, sz = seat
    people = [(sx, -0.45)]
    if variant >= 1:
        people.append((sx, 0.45))
    if variant >= 2 and kind != "sport":
        people.append((sx - 1.3, -0.45))
        people.append((sx - 1.3, 0.45))
    if kind == "bus":
        people = [(3.0, -0.6)] + [(1.6 - k * 1.3, s * 0.6) for k in range(5) for s in (-1, 1) if random.random() < 0.6]
    for px, py in people:
        parts += person(px, py, sz, random.choice(SKINS), random.choice(CLOTH), seated=True, scale=0.62)
    car = join_into("City_CarProto_%s%d" % (kind, variant), parts)
    car.location = (0, 0, -50)
    return car


def make_flyer(kind, variant):
    if kind == "sport":
        pts = [(2.9, 0.45), (2.4, 0.05), (-2.2, 0.0), (-3.0, 0.35), (-3.0, 0.85), (-1.4, 1.05), (-0.2, 1.5), (1.2, 1.35), (2.4, 0.95)]
        width, glass, seat = 1.7, 1.0, (0.2, 0.45)
    else:
        pts = [(3.0, 0.3), (2.5, 0.0), (-3.0, 0.0), (-3.2, 1.2), (1.5, 1.6), (2.6, 1.1)]
        width, glass, seat = 2.0, 1.15, (1.2, 0.5)
    body = profile_body("flybody", pts, width, FLYER_PAINT, glass_z=glass, bevel=0.16, taper=0.3)
    parts = [body]
    for s in (-1, 1):
        py = s * (width / 2 + 0.55)
        parts.append(cylinder("pod", 0.42, 2.0, (-0.4, py, 0.45), FLYER_PAINT, verts=24, rot=(0, math.pi / 2, 0)))
        parts.append(cylinder("podIntake", 0.3, 0.2, (0.65, py, 0.45), DARK, verts=24, rot=(0, math.pi / 2, 0)))
        parts.append(cylinder("podGlow", 0.32, 0.15, (-1.45, py, 0.45), NEON_CYAN, verts=24, rot=(0, math.pi / 2, 0)))
        parts.append(box("strut", (0.8, 0.5, 0.18), (-0.2, s * (width / 2 + 0.2), 0.55), DARK, bevel=0.04))
        parts.append(box("winglet", (1.2, 0.12, 0.7), (-2.2, s * (width / 2 - 0.1), 0.9), FLYER_PAINT, rot=(s * 0.35, 0, 0), bevel=0.03))
        parts.append(box("wingTip", (0.5, 0.14, 0.12), (-2.2, s * (width / 2 + 0.05), 1.22), TAILLIGHT))
    parts.append(cylinder("thruster", 0.34, 0.3, (-3.1, 0, 0.6), NEON_MAG, verts=24, rot=(0, math.pi / 2, 0)))
    parts.append(box("head", (0.12, 0.9, 0.16), (2.85, 0, 0.5), HEADLIGHT))
    parts.append(box("underglow", (4.0, width * 0.7, 0.06), (0, 0, -0.02), NEON_MAG))
    sx, sz = seat
    people = [(sx, 0.0)] if kind == "sport" else [(sx, -0.4)] + ([(sx, 0.4)] if variant else [])
    for px, py in people:
        parts += person(px, py, sz, random.choice(SKINS), random.choice(CLOTH), seated=True, scale=0.55)
    fl = join_into("City_FlyerProto_%s%d" % (kind, variant), parts)
    fl.location = (0, 0, -50)
    return fl


car_protos = [make_car(k, v) for k in CAR_KINDS for v in (0, 1, 2)]
flyer_protos = [make_flyer(k, v) for k in ("sport", "cargo") for v in (0, 1)]
for p in car_protos + flyer_protos:
    p.hide_render = True
    p.hide_viewport = True
CAR_WEIGHTS = [3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 0]        # sedans and sports most, buses rare


def pick_car():
    return random.choices(car_protos, weights=CAR_WEIGHTS)[0]


def pick_flyer():
    return random.choice(flyer_protos)


# the citizens: blobs like Yellow and Purple. Yellow's body is baked from his
# rest pose and scaled to street size, with eyes and a smile; some are white
# and those carry a drawn eye on the forehead
BLOB_SKIN = car_mat("CityBlobSkin", rough=0.9, metallic=0.0)
BLOB_SKIN.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.0
BLOB_DARK = plain("CityBlobDark", (0.05, 0.035, 0.03), rough=0.4)
BLOB_SCALE = 0.29                                           # 9 studs tall -> 2.6, next to the cars


def rest_body_mesh():
    rig = bpy.data.objects["CharacterRig"]
    body = bpy.data.objects["Character"]
    rig.data.pose_position = "REST"
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
    rig.data.pose_position = "POSE"
    return mesh


def make_blob(white, v):
    mesh = rest_body_mesh()
    mesh.materials.clear()
    mesh.materials.append(BLOB_SKIN)
    blob = bpy.data.objects.new("blob", mesh)
    scene.collection.objects.link(blob)
    attach(blob)
    parts = [blob]
    head_z = 7.55

    def on_face(pt):
        ok, loc, normal, _ = blob.closest_point_on_mesh(Vector(pt))
        return loc, normal.normalized()

    for sx in (-1, 1):
        loc, n = on_face((sx * 0.52, -2.0, head_z + 0.25))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.21, segments=16, ring_count=10, location=loc - n * 0.04)
        eye = bpy.context.object
        eye.name = "eye"
        eye.scale = (0.84, 0.5, 1.0)
        eye.rotation_mode = "QUATERNION"
        eye.rotation_quaternion = n.to_track_quat("Y", "Z")
        eye.data.materials.append(BLOB_DARK)
        bpy.ops.object.shade_smooth()
        attach(eye)
        parts.append(eye)
    # the smile: the lower half of a thin ring laid on the face
    loc, n = on_face((0, -2.0, head_z - 0.55))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.035, major_segments=32, minor_segments=8, location=loc + n * 0.02)
    smile = bpy.context.object
    smile.name = "smile"
    smile.rotation_mode = "QUATERNION"
    smile.rotation_quaternion = n.to_track_quat("Z", "Y")
    smile.location = loc + n * 0.02 + Vector((0, 0, 0.45))
    bm = bmesh.new()
    bm.from_mesh(smile.data)
    bmesh.ops.delete(bm, geom=[vv for vv in bm.verts if vv.co.y > -0.15], context="VERTS")   # keep the bottom arc (local y is up on the face)
    bm.to_mesh(smile.data)
    bm.free()
    smile.data.materials.append(BLOB_DARK)
    attach(smile)
    parts.append(smile)
    if white:
        # the eye drawn on the forehead: an almond outline and a pupil
        loc, n = on_face((0, -2.0, head_z + 0.95))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.035, major_segments=32, minor_segments=8, location=loc + n * 0.02)
        ring = bpy.context.object
        ring.name = "foreheadEye"
        ring.rotation_mode = "QUATERNION"
        ring.rotation_quaternion = n.to_track_quat("Z", "Y")
        ring.scale = (1.0, 0.55, 1.0)
        ring.data.materials.append(BLOB_DARK)
        attach(ring)
        parts.append(ring)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=12, ring_count=8, location=loc + n * 0.03)
        pupil = bpy.context.object
        pupil.name = "pupil"
        pupil.scale = (1.0, 0.5, 1.0)
        pupil.rotation_mode = "QUATERNION"
        pupil.rotation_quaternion = n.to_track_quat("Y", "Z")
        pupil.data.materials.append(BLOB_DARK)
        bpy.ops.object.shade_smooth()
        attach(pupil)
        parts.append(pupil)
    w = join_into("City_BlobProto_%s%d" % ("white" if white else "colour", v), parts)
    w.data.transform(Matrix.Scale(BLOB_SCALE, 4))
    w.location = (0, 0, -50)
    return w


walker_protos = [make_blob(False, 0), make_blob(True, 0)]
for p in walker_protos:
    p.hide_render = True
    p.hide_viewport = True
BLOB_COLOURS = [(1.0, 0.72, 0.08), (0.55, 0.3, 0.85), (0.9, 0.25, 0.3), (0.2, 0.55, 0.95), (0.3, 0.8, 0.45), (1.0, 0.55, 0.15), (0.95, 0.5, 0.8), (0.2, 0.8, 0.85)]


def pick_walker():
    """(prototype, colour): about a third are white with the forehead eye."""
    if random.random() < 0.33:
        return walker_protos[1], (0.95, 0.95, 0.95)
    return walker_protos[0], random.choice(BLOB_COLOURS)


PALETTE = [(0.9, 0.1, 0.1), (0.1, 0.3, 0.9), (0.95, 0.95, 0.95), (0.1, 0.1, 0.12), (0.9, 0.6, 0.1), (0.2, 0.8, 0.4), (0.6, 0.1, 0.8), (0.9, 0.9, 0.2)]


def instance(proto, name, colour, size=1.0):
    o = bpy.data.objects.new(name, proto.data)
    o.color = (*colour, 1)
    o.scale = (size, size, size)
    o.rotation_mode = "XYZ"
    col.objects.link(o)
    o.parent = root
    o.matrix_parent_inverse.identity()
    return o


def linearize(o):
    for fc in o.animation_data.action.layers[0].strips[0].channelbag(o.animation_data.action_slot).fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def drive_circle(o, r, z, a0, speed, ccw=True, wobble=0.0, step=6, bob=0.0, sway=0.0):
    """Keyed around a circle for the whole timeline: heading along the tangent."""
    for f in range(FRAMES[0], FRAMES[1] + step, step):
        t = (f - FRAMES[0]) / FPS
        a = a0 + (speed / r) * t * (1 if ccw else -1)
        zz = z + wobble * math.sin(2 * math.pi * t / 5.0 + a0) + bob * abs(math.sin(2 * math.pi * t * 1.8 + a0))
        o.location = (r * math.cos(a), r * math.sin(a), zz)
        o.rotation_euler = (sway * math.sin(2 * math.pi * t * 1.8 + a0), 0, a + (math.pi / 2 if ccw else -math.pi / 2))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    linearize(o)


def drive_line(o, p0, p1, z, speed, step=6, phase=0.0, bob=0.0, sway=0.0):
    """Back and forth along a line, turning round at the ends."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    period = 2 * L / speed
    for f in range(FRAMES[0], FRAMES[1] + step, step):
        t0 = (f - FRAMES[0]) / FPS
        t = (t0 + phase * period) % period
        fwd = t < period / 2
        u = (t / (period / 2)) if fwd else 2 - t / (period / 2)
        p = p0.lerp(p1, u)
        d = (p1 - p0) if fwd else (p0 - p1)
        o.location = (p.x, p.y, z + bob * abs(math.sin(2 * math.pi * t0 * 1.8 + phase * 7)))
        o.rotation_euler = (sway * math.sin(2 * math.pi * t0 * 1.8 + phase * 7), 0, math.atan2(d.y, d.x))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    linearize(o)


# ground cars: two lanes each way on the ring road, and up and down the avenues
n_cars = 0
for lane_r, ccw in ((R_RING - 3.2, True), (R_RING - 1.2, True), (R_RING + 1.2, False), (R_RING + 3.2, False)):
    for k in range(14):
        c = instance(pick_car(), "City_Car", random.choice(PALETTE))
        drive_circle(c, lane_r, 0.12, 2 * math.pi * k / 14 + random.uniform(0, 0.3), random.uniform(7, 11), ccw)
        n_cars += 1
for axis in ("x", "y"):
    for lane in (-3.0, -1.2, 1.2, 3.0):
        for half in (-1, 1):
            for k in range(3):
                c = instance(pick_car(), "City_Car", random.choice(PALETTE))
                L = R_RING + 3
                a, b = (half * 17, half * L) if lane > 0 else (half * L, half * 17)
                p0, p1 = ((a, lane), (b, lane)) if axis == "x" else ((lane, a), (lane, b))
                drive_line(c, p0, p1, 0.12, random.uniform(7, 11), phase=k / 3.0)
                n_cars += 1
# flying cars: lanes at several heights, both ways, with a gentle bob
n_fly = 0
for lane_r, z, ccw in ((58, 62, True), (64, 55, False), (70, 50, True), (76, 66, False), (82, 44, True), (60, 74, False), (68, 80, True), (88, 40, False),
                       (74, 88, True), (50, 84, False)):
    for k in range(8):
        fl = instance(pick_flyer(), "City_Flyer", random.choice(PALETTE))
        drive_circle(fl, lane_r + random.uniform(-2, 2), z + random.uniform(-2, 2), 2 * math.pi * k / 8 + random.uniform(0, 0.5),
                     random.uniform(14, 24), ccw, wobble=0.6)
        n_fly += 1
for k in range(12):
    fl = instance(pick_flyer(), "City_Flyer", random.choice(PALETTE))
    a = random.uniform(0, 2 * math.pi)
    d = Vector((math.cos(a), math.sin(a)))
    z = random.uniform(86, 100)
    drive_line(fl, tuple(-d * 74), tuple(d * 74), z, random.uniform(16, 26), phase=random.random())
    n_fly += 1

# people on the sidewalks: round the ring both ways and along the avenues, with a walking bob
n_people = 0
for walk_r, ccw in ((R_RING - 7.5, True), (R_RING - 6.2, False), (R_RING + 6.2, True), (R_RING + 7.6, False)):
    for k in range(34):
        proto, colour = pick_walker()
        w = instance(proto, "City_Walker", colour, size=random.uniform(0.85, 1.15))
        drive_circle(w, walk_r + random.uniform(-0.3, 0.3), 0.2, 2 * math.pi * k / 34 + random.uniform(0, 0.15), random.uniform(1.3, 2.2), ccw,
                     step=4, bob=0.07, sway=0.04)
        n_people += 1
for axis in ("x", "y"):
    for side in (-1, 1):
        for k in range(22):
            proto, colour = pick_walker()
            w = instance(proto, "City_Walker", colour, size=random.uniform(0.85, 1.15))
            lane = side * random.uniform(5.6, 7.8)
            L = R_RING - 6
            a, b = (-L, L) if random.random() < 0.5 else (L, -L)
            p0, p1 = ((a, lane), (b, lane)) if axis == "x" else ((lane, a), (lane, b))
            drive_line(w, p0, p1, 0.2, random.uniform(1.3, 2.2), step=4, phase=random.random(), bob=0.07, sway=0.04)
            n_people += 1
# a crowd in the plaza, milling in small circles
for k in range(30):
    proto, colour = pick_walker()
    w = instance(proto, "City_Walker", colour)
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(5, 12)
    cx, cy = r * math.cos(a), r * math.sin(a)
    o_r = random.uniform(1.0, 2.5)
    # small circle around (cx, cy): parametrized by offsetting a circle drive
    for f in range(FRAMES[0], FRAMES[1] + 4, 4):
        t = (f - FRAMES[0]) / FPS
        ang = a + t * 0.8 / o_r
        w.location = (cx + o_r * math.cos(ang), cy + o_r * math.sin(ang), 0.32 + 0.07 * abs(math.sin(2 * math.pi * t * 1.8 + a)))
        w.rotation_euler = (0, 0, ang + math.pi / 2)
        w.keyframe_insert("location", frame=f)
        w.keyframe_insert("rotation_euler", frame=f)
    linearize(w)
    n_people += 1

# ------------------------------------------------------------ street furniture
LAMP = plain("CityLampGlow", (1.0, 0.95, 0.85), rough=0.3, emit=(1.0, 0.95, 0.8), strength=6.0)
LEAF = plain("CityLeaf", (0.15, 0.55, 0.35), rough=0.8, emit=(0.1, 0.5, 0.3), strength=0.4)


def lamp(x, y, heading):
    cylinder("City_LampPost", 0.12, 5.0, (x, y, 2.5), CHROME, verts=10)
    ax, ay = x + 0.9 * math.cos(heading), y + 0.9 * math.sin(heading)
    box("City_LampArm", (1.8, 0.1, 0.1), ((x + ax) / 2, (y + ay) / 2, 4.95), CHROME, rot=(0, 0, heading))
    box("City_LampHead", (0.7, 0.35, 0.18), (ax, ay, 4.9), LAMP, rot=(0, 0, heading))


def bench(x, y, heading):
    box("City_Bench", (1.8, 0.5, 0.08), (x, y, 0.62), DARK, rot=(0, 0, heading))
    box("City_BenchBack", (1.8, 0.08, 0.5), (x - 0.22 * math.sin(heading), y + 0.22 * math.cos(heading), 0.95), DARK, rot=(0, 0, heading))
    for s in (-1, 1):
        box("City_BenchLeg", (0.1, 0.45, 0.5), (x + s * 0.75 * math.cos(heading), y + s * 0.75 * math.sin(heading), 0.4), CHROME, rot=(0, 0, heading))


def kiosk(x, y, heading):
    cylinder("City_Kiosk", 0.35, 3.0, (x, y, 1.5), CHROME, verts=12)
    cylinder("City_KioskBase", 0.6, 0.2, (x, y, 0.25), DARK, verts=12)
    if os.path.exists(HUD):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 2.6))
        p = bpy.context.object
        p.name = "City_KioskScreen"
        p.scale = (1.1, 1.6, 1)
        p.rotation_euler = (math.radians(90), 0, heading)
        p.data.materials.append(bpy.data.materials["CityHoloAd"])
        attach(p)


def planter(x, y):
    cylinder("City_Planter", 0.7, 0.7, (x, y, 0.5), CONCRETE, verts=12)
    cylinder("City_Trunk", 0.12, 1.6, (x, y, 1.6), DARK, verts=8)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.1, location=(x, y, 2.9))
    c = bpy.context.object
    c.name = "City_Canopy"
    c.scale = (1.0, 1.0, 0.8)
    c.data.materials.append(LEAF)
    bpy.ops.object.shade_smooth()
    attach(c)
    annulus("City_PlanterGlow", 0.72, 0.82, 0.86, NEON_CYAN, segs=12)


for k in range(28):
    a = 2 * math.pi * k / 28
    for r, inward in ((R_RING + 8.0, True), (R_RING - 8.0, False)):
        lamp(r * math.cos(a), r * math.sin(a), a + (math.pi if inward else 0))
    if k % 2 == 0:
        bench((R_RING + 7.4) * math.cos(a + 0.05), (R_RING + 7.4) * math.sin(a + 0.05), a + math.pi / 2)
    if k % 3 == 0:
        planter((R_RING - 7.6) * math.cos(a + 0.06), (R_RING - 7.6) * math.sin(a + 0.06))
    if k % 4 == 1:
        kiosk((R_RING + 7.2) * math.cos(a - 0.05), (R_RING + 7.2) * math.sin(a - 0.05), a)
for axis in ("x", "y"):
    for s in (-1, 1):
        for pos in frange(-R_RING + 8, R_RING - 6, 12.0):
            if abs(pos) < 16:
                continue
            x, y = (pos, s * 8.0) if axis == "x" else (s * 8.0, pos)
            lamp(x, y, (math.pi / 2 if s < 0 else -math.pi / 2) if axis == "x" else (0 if s < 0 else math.pi))
            if int(pos) % 24 < 12:
                bx, by = (pos + 5, s * 7.6) if axis == "x" else (s * 7.6, pos + 5)
                bench(bx, by, 0 if axis == "x" else math.pi / 2)
            else:
                px, py = (pos + 5, s * 7.4) if axis == "x" else (s * 7.4, pos + 5)
                planter(px, py)
for k in range(8):
    a = 2 * math.pi * k / 8 + 0.2
    planter(11.5 * math.cos(a), 11.5 * math.sin(a))
    bench(12.6 * math.cos(a + 0.25), 12.6 * math.sin(a + 0.25), a + math.pi / 2)



# ------------------------------------------------------------ interiors: shops and lobbies you can see into
SIGN_WORDS = ["NOVA", "RAMEN", "HOTEL", "NEON", "SUSHI", "BANK", "CLUB 9", "DRONES", "NIMBUS", "ARCADE", "SKY BAR", "GRID", "PODS", "TAXI",
              "NOODLE", "PARTS", "SYNTH", "HOLO", "CAFE", "MOTO", "VAULT", "ZERO", "ORBIT", "FLUX"]
PRODUCT = [plain("CityProduct%d" % i, c, rough=0.5) for i, c in enumerate(((0.9, 0.2, 0.2), (0.2, 0.6, 0.9), (0.9, 0.8, 0.2), (0.3, 0.85, 0.5), (0.9, 0.5, 0.9)))]
SHOP_FLOOR = plain("CityShopFloor", (0.35, 0.33, 0.3), rough=0.3, metallic=0.1)
SHOP_WALL = plain("CityShopWall", (0.55, 0.5, 0.45), rough=0.9, emit=(0.9, 0.75, 0.55), strength=0.25)


def sign_text(word, x, y, z, heading, size, mat):
    """A neon word, extruded, facing `heading`."""
    curve = bpy.data.curves.new("CitySignText", type="FONT")
    curve.body = word
    curve.extrude = 0.06
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    o = bpy.data.objects.new("City_SignText", curve)
    scene.collection.objects.link(o)
    o.scale = (size, size, size)
    o.rotation_euler = (math.radians(90), 0, heading + math.pi)
    o.location = (x, y, z)
    o.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    return attach(o)


def standing_blob(x, y, heading, z=0.0):
    proto, colour = pick_walker()
    b = instance(proto, "City_Citizen", colour)
    b.location = (x, y, z)
    b.rotation_euler = (0, 0, heading)
    return b


def shop(x, y):
    """A shop unit: an open glass front you can see into, with a counter, shelves of
    goods, a hanging light, a shopkeeper and a customer, and a neon name over the door."""
    w, d, h = random.uniform(4.5, 6.0), random.uniform(4.5, 6.0), 3.6
    heading = random.choice((0, math.pi / 2, math.pi, -math.pi / 2))   # which way the front faces
    R = Matrix.Rotation(heading, 3, "Z")

    def L(px, py, pz):                                       # shop-local (front is -y) to city space
        v = R @ Vector((px, py, pz))
        return (x + v.x, y + v.y, v.z)

    facade = random.choice(FACADES)
    parts = [box("shopFloor", (w, d, 0.2), L(0, 0, 0.2), SHOP_FLOOR),
             box("shopRoof", (w + 0.4, d + 0.4, 0.3), L(0, 0, h + 0.15), facade, bevel=0.05),
             box("shopBack", (w, 0.25, h), L(0, d / 2, h / 2), SHOP_WALL),
             box("shopSideL", (0.25, d, h), L(-w / 2, 0, h / 2), facade),
             box("shopSideR", (0.25, d, h), L(w / 2, 0, h / 2), facade),
             box("shopFascia", (w + 0.4, 0.3, 0.9), L(0, -d / 2, h - 0.45), DARK),
             box("shopCounter", (w * 0.5, 0.7, 1.1), L(-w * 0.15, -d * 0.1, 0.85), DARK, bevel=0.04),
             box("shopCounterTop", (w * 0.52, 0.8, 0.08), L(-w * 0.15, -d * 0.1, 1.44), CHROME),
             box("shopLight", (w * 0.6, 0.15, 0.08), L(0, 0, h - 0.25), random.choice((NEON_CYAN, NEON_MAG, LAMP)))]
    for k in range(3):                                       # shelves on the back wall with goods
        sz = 1.0 + k * 0.85
        parts.append(box("shopShelf", (w * 0.8, 0.5, 0.06), L(0, d / 2 - 0.4, sz), CHROME))
        for j in range(6):
            parts.append(box("shopGoods", (0.35, 0.3, random.uniform(0.25, 0.5)), L(-w * 0.35 + j * w * 0.14, d / 2 - 0.4, sz + 0.2), random.choice(PRODUCT)))
    unit = join_into("City_Shop", parts)
    unit.location = (0, 0, 0)
    # the glass front with a doorway gap
    gw = 1.2
    for sx, ww in ((-1, (w - gw) / 2), (1, (w - gw) / 2)):
        box("City_ShopGlass", (ww, 0.08, h - 0.9), L(sx * (gw / 2 + ww / 2), -d / 2 + 0.05, (h - 0.9) / 2), GLASS_CAR)
    box("City_ShopDoorFrame", (gw + 0.2, 0.12, 0.12), L(0, -d / 2 + 0.05, h - 0.95), CHROME)
    sign_text(random.choice(SIGN_WORDS), *L(0, -d / 2 - 0.25, h - 0.45), heading, 0.55, random.choice(NEONS))
    # people: a keeper behind the counter and a customer browsing
    standing_blob(*L(-w * 0.15, d * 0.1, 0.2)[:2], heading + math.pi, z=0.3)
    if random.random() < 0.7:
        standing_blob(*L(w * 0.25, d * 0.2, 0.2)[:2], heading + random.uniform(-0.6, 0.6), z=0.3)
    if random.random() < 0.5:
        standing_blob(*L(random.uniform(-w * 0.3, w * 0.3), -d / 2 - 1.2, 0)[:2], heading + math.pi, z=0.2)


def lobby(x, y, pw, pd):
    """The ground floor of a podium: columns, glass all round, a lit ceiling, a
    reception desk, seats and a few citizens."""
    h = 3.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("City_LobbyColumn", (0.5, 0.5, h), (x + sx * (pw / 2 - 0.4), y + sy * (pd / 2 - 0.4), h / 2), CHROME)
    box("City_LobbyGlassX", (pw, 0.06, h - 0.3), (x, y - pd / 2, h / 2), GLASS_CAR)
    box("City_LobbyGlassX", (pw, 0.06, h - 0.3), (x, y + pd / 2, h / 2), GLASS_CAR)
    box("City_LobbyGlassY", (0.06, pd, h - 0.3), (x - pw / 2, y, h / 2), GLASS_CAR)
    box("City_LobbyGlassY", (0.06, pd, h - 0.3), (x + pw / 2, y, h / 2), GLASS_CAR)
    box("City_LobbyFloor", (pw, pd, 0.12), (x, y, 0.2), SHOP_FLOOR)
    box("City_LobbyCeiling", (pw * 0.7, pd * 0.7, 0.06), (x, y, h - 0.15), LAMP)
    box("City_LobbyDesk", (pw * 0.35, 0.9, 1.1), (x, y + pd * 0.2, 0.8), DARK, bevel=0.05)
    box("City_LobbyDeskTop", (pw * 0.37, 1.0, 0.06), (x, y + pd * 0.2, 1.38), CHROME)
    box("City_LobbyDeskLight", (pw * 0.33, 0.05, 0.08), (x, y + pd * 0.2 - 0.46, 0.6), random.choice(NEONS))
    for k in range(2):
        box("City_LobbySeat", (1.8, 0.6, 0.45), (x - pw * 0.3 + k * 0.0, y - pd * 0.2 + k * 1.2, 0.5), DARK, bevel=0.06)
    standing_blob(x, y + pd * 0.28, -math.pi / 2, z=0.26)
    for k in range(random.randint(1, 3)):
        standing_blob(x + random.uniform(-pw * 0.3, pw * 0.3), y + random.uniform(-pd * 0.3, pd * 0.05), random.uniform(0, 2 * math.pi), z=0.26)


n_shops = 0
for sx_, sy_ in SHOPS:
    shop(sx_, sy_)
    n_shops += 1
for lx, ly, lpw, lpd in LOBBIES:
    lobby(lx, ly, lpw, lpd)
# big neon names on some podium bands and tower tops
for x, y, d in random.sample(cells, min(40, len(cells))):
    heading = random.choice((0, math.pi / 2, math.pi, -math.pi / 2))
    R = Matrix.Rotation(heading, 3, "Z")
    off = R @ Vector((0, -6.2, 0))
    sign_text(random.choice(SIGN_WORDS), x + off.x, y + off.y, random.uniform(9, 16), heading, random.uniform(1.2, 2.2), random.choice(NEONS))

# ------------------------------------------------------------ crossings, traffic lights
STRIPE = plain("CityStripe", (0.9, 0.9, 0.9), rough=0.6)
for axis in ("x", "y"):
    for pos in (-62, -34, 34, 62):
        for k in range(7):
            off = -4.2 + k * 1.4
            size = (0.55, 1.0, 0.02) if axis == "x" else (1.0, 0.55, 0.02)
            loc = (pos, off, 0.13) if axis == "x" else (off, pos, 0.13)
            box("City_Crossing", size, loc, STRIPE)
        for s in (-1, 1):
            lx, ly = (pos + s * 3.2, s * 6.0) if axis == "x" else (s * 6.0, pos + s * 3.2)
            cylinder("City_LightPole", 0.1, 4.2, (lx, ly, 2.1), CHROME, verts=8)
            box("City_LightHead", (0.35, 0.35, 1.0), (lx, ly, 4.0), DARK)
            for i, m in enumerate((TAILLIGHT, NEON_ORANGE, NEON_CYAN)):
                box("City_LightLamp", (0.36, 0.12, 0.22), (lx, ly, 4.32 - i * 0.3), m if i == 2 else DARK)

# ------------------------------------------------------------ the monorail: an elevated loop with a train
RAIL_R, RAIL_Z = 62.0, 17.0
annulus("City_RailBed", RAIL_R - 1.4, RAIL_R + 1.4, RAIL_Z, CONCRETE, segs=128)
annulus("City_RailGlow", RAIL_R - 0.15, RAIL_R + 0.15, RAIL_Z + 0.05, NEON_CYAN, segs=128)
for k in range(36):
    a = 2 * math.pi * k / 36
    px, py = RAIL_R * math.cos(a), RAIL_R * math.sin(a)
    if abs(px) < 9 or abs(py) < 9:
        continue                                            # not on the avenues
    cylinder("City_RailPylon", 0.7, RAIL_Z, (px, py, RAIL_Z / 2), CONCRETE, verts=12)
    box("City_RailPylonCap", (3.6, 1.2, 0.5), (px, py, RAIL_Z - 0.3), DARK, rot=(0, 0, a))
for k in range(2):                                          # two stations
    a = math.radians(30 + 180 * k)
    px, py = RAIL_R * math.cos(a), RAIL_R * math.sin(a)
    box("City_Station", (10.0, 4.6, 0.4), (px, py, RAIL_Z + 0.2), CONCRETE_KERB, rot=(0, 0, a))
    box("City_StationRoof", (10.5, 5.2, 0.25), (px, py, RAIL_Z + 4.0), DARK, rot=(0, 0, a))
    for s in (-1, 1):
        box("City_StationPost", (0.3, 0.3, 3.8), (px - s * 4.5 * math.sin(a), py + s * 4.5 * math.cos(a), RAIL_Z + 2.1), CHROME)
    box("City_StationSign", (6.0, 0.1, 0.5), (px - 2.7 * math.sin(a), py + 2.7 * math.cos(a), RAIL_Z + 3.5), random.choice(NEONS), rot=(0, 0, a))
    for j in range(3):
        standing_blob(px + random.uniform(-3, 3) * math.cos(a) + 1.5 * math.sin(a), py + random.uniform(-3, 3) * math.sin(a) - 1.5 * math.cos(a), a, z=RAIL_Z + 0.4)


def make_train_car(v):
    pts = [(-4.0, 0.3), (4.0, 0.3), (4.5, 0.9), (4.4, 2.6), (3.9, 3.0), (-3.9, 3.0), (-4.4, 2.6), (-4.5, 0.9)]
    body = profile_body("traincar", pts, 2.6, FLYER_PAINT, glass_z=1.5, bevel=0.12, taper=0.02)
    parts = [body, box("trainGlow", (7.5, 1.8, 0.08), (0, 0, 0.28), NEON_CYAN), box("trainStripe", (8.6, 2.66, 0.12), (0, 0, 1.45), random.choice(NEONS))]
    for s in (-1, 1):
        parts.append(box("trainHead", (0.1, 0.6, 0.25), (s * 4.55, s * 0.6, 1.0), HEADLIGHT if s > 0 else TAILLIGHT))
    for px_ in (-2.5, 0.0, 2.5):
        for py_ in (-0.7, 0.7):
            parts += person(px_, py_, 0.9, random.choice(SKINS), random.choice(CLOTH), seated=True, scale=0.62)
    t = join_into("City_TrainProto%d" % v, parts)
    t.location = (0, 0, -50)
    return t


train_protos = [make_train_car(v) for v in range(2)]
for tp in train_protos:
    tp.hide_render = tp.hide_viewport = True
for k in range(2):                                          # two trains, opposite sides, four cars each
    a0 = math.pi * k
    for c in range(4):
        car = instance(train_protos[c % 2], "City_Train", (0.85, 0.85, 0.9))
        drive_circle(car, RAIL_R, RAIL_Z + 0.1, a0 - c * 9.4 / RAIL_R, 26.0, True, step=4)

# ------------------------------------------------------------ haze under the dome: depth and light shafts
haze_mat = bpy.data.materials.get("CityHaze") or bpy.data.materials.new("CityHaze")
haze_mat.use_nodes = True
nt = haze_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.0035
vol.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
vol.inputs["Anisotropy"].default_value = 0.3
nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
haze = box("City_Haze", (2 * R_WALL_IN, 2 * R_WALL_IN, 70.0), (0, 0, 35.0), haze_mat)
haze.display_type = "WIRE"

# drones: little lit spheres buzzing low over the streets
n_drones = 0
for k in range(24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, segments=12, ring_count=8, location=(0, 0, 0))
    dr = bpy.context.object
    dr.name = "City_Drone"
    dr.data.materials.append(CHROME)
    bpy.ops.object.shade_smooth()
    attach(dr)
    light = box("City_DroneLight", (0.2, 0.2, 0.2), (0, 0, -0.35), random.choice((TAILLIGHT, NEON_CYAN)))
    light.parent = dr
    light.location = (0, 0, -0.35)
    drive_circle(dr, random.uniform(20, 90), random.uniform(6, 14), random.uniform(0, 2 * math.pi), random.uniform(6, 12),
                 random.random() < 0.5, wobble=0.8, step=4)
    n_drones += 1

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
print("city built:", len(col.objects), "objects |", towers, "towers |", n_shops, "shops |", len(LOBBIES), "lobbies |", n_cars, "cars |", n_fly, "flyers |", n_people, "people |", n_drones, "drones",
      "| gate at %.0f deg" % math.degrees(GATE_ANGLE), "| dome r %.1f" % dome_r)
