"""Builds a Roblox-style scene: a 6-faced skybox cube with a procedural sky
(gradient + clouds + sun disc) and a 512x512 tiled baseplate. Run headless:

  blender --background --factory-startup --python build_scene.py -- <out_dir>
"""
import bpy, math, os, sys

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.getcwd()
os.makedirs(os.path.join(out_dir, "renders"), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.eevee.taa_render_samples = 64


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


# ---------------------------------------------------------------- baseplate
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -2))
bp = bpy.context.object
bp.name = "Baseplate"
bp.scale = (512, 512, 4)
bpy.ops.object.transform_apply(scale=True)

m, nt = new_mat("BaseplateMat")
tc = nt.nodes.new("ShaderNodeTexCoord")
checker = nt.nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 0.25            # 4-stud tiles
checker.inputs["Color1"].default_value = (0.94, 0.94, 0.95, 1)   # white tile
checker.inputs["Color2"].default_value = (0.86, 0.87, 0.88, 1)   # slightly off-white
brick = nt.nodes.new("ShaderNodeTexBrick")
brick.offset = 0.0                                       # straight grid, not staggered
brick.inputs["Scale"].default_value = 0.25
brick.inputs["Mortar Size"].default_value = 0.03
brick.inputs["Mortar Smooth"].default_value = 0.0
brick.inputs["Mortar"].default_value = (0.62, 0.63, 0.65, 1)      # light grey grout
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.55                      # glossy ceramic look
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Object"], checker.inputs["Vector"])
nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
nt.links.new(checker.outputs["Color"], brick.inputs["Color1"])
nt.links.new(checker.outputs["Color"], brick.inputs["Color2"])
nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
bp.data.materials.append(m)

# ------------------------------------------------------------------ skybox
SKY_R = 1500.0
bpy.ops.mesh.primitive_cube_add(size=SKY_R * 2, location=(0, 0, 0))
sky = bpy.context.object
sky.name = "Skybox"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.flip_normals()                              # faces point inward
bpy.ops.object.mode_set(mode="OBJECT")

SUN_DIR = (0.30, 0.85, 0.30)
sl = math.sqrt(sum(c * c for c in SUN_DIR))
SUN_DIR = tuple(c / sl for c in SUN_DIR)

m, nt = new_mat("SkyboxMat")
m.use_backface_culling = False
tc = nt.nodes.new("ShaderNodeTexCoord")
norm = nt.nodes.new("ShaderNodeVectorMath"); norm.operation = "NORMALIZE"
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
height = nt.nodes.new("ShaderNodeMapRange")              # z in [-1,1] -> [0,1]
height.inputs["From Min"].default_value = -1.0
height.inputs["From Max"].default_value = 1.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.42, 0.50, 0.58, 1)   # below horizon
e = cr.elements.new(0.50); e.color = (0.74, 0.86, 0.98, 1)                    # horizon haze
e = cr.elements.new(0.545); e.color = (0.36, 0.63, 0.97, 1)
cr.elements[-1].position = 1.0; cr.elements[-1].color = (0.08, 0.32, 0.86, 1)  # zenith

# clouds: noise on direction, only above horizon
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 2.5
noise.inputs["Detail"].default_value = 6.0
noise.inputs["Roughness"].default_value = 0.6
cloud_ramp = nt.nodes.new("ShaderNodeValToRGB")
cc = cloud_ramp.color_ramp
cc.elements[0].position = 0.50; cc.elements[0].color = (0, 0, 0, 1)
cc.elements[1].position = 0.64; cc.elements[1].color = (1, 1, 1, 1)
horizon_fade = nt.nodes.new("ShaderNodeMapRange")
horizon_fade.inputs["From Min"].default_value = 0.02
horizon_fade.inputs["From Max"].default_value = 0.15
cloud_mask = nt.nodes.new("ShaderNodeMath"); cloud_mask.operation = "MULTIPLY"
mix_clouds = nt.nodes.new("ShaderNodeMix"); mix_clouds.data_type = "RGBA"
mix_clouds.inputs["B"].default_value = (0.98, 0.98, 1.0, 1)

# sun disc: dot(dir, sun) thresholded
sunv = nt.nodes.new("ShaderNodeVectorMath"); sunv.operation = "DOT_PRODUCT"
sunv.inputs[1].default_value = SUN_DIR
sun_ramp = nt.nodes.new("ShaderNodeValToRGB")
sr = sun_ramp.color_ramp
sr.elements[0].position = 0.9990; sr.elements[0].color = (0, 0, 0, 1)
sr.elements[1].position = 0.9996; sr.elements[1].color = (1, 1, 1, 1)
# soft glow around the disc
glow_ramp = nt.nodes.new("ShaderNodeValToRGB")
gr = glow_ramp.color_ramp
gr.elements[0].position = 0.985; gr.elements[0].color = (0, 0, 0, 1)
gr.elements[1].position = 0.999; gr.elements[1].color = (0.45, 0.45, 0.45, 1)
mix_glow = nt.nodes.new("ShaderNodeMix"); mix_glow.data_type = "RGBA"
mix_glow.inputs["B"].default_value = (1.0, 0.98, 0.90, 1)
mix_sun = nt.nodes.new("ShaderNodeMix"); mix_sun.data_type = "RGBA"
mix_sun.inputs["B"].default_value = (1.0, 0.97, 0.85, 1)

emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Strength"].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputMaterial")

L = nt.links.new
L(tc.outputs["Object"], norm.inputs[0])
L(norm.outputs["Vector"], sep.inputs["Vector"])
L(sep.outputs["Z"], height.inputs["Value"])
L(height.outputs["Result"], ramp.inputs["Fac"])
L(norm.outputs["Vector"], noise.inputs["Vector"])
L(noise.outputs["Fac"], cloud_ramp.inputs["Fac"])
L(sep.outputs["Z"], horizon_fade.inputs["Value"])
L(cloud_ramp.outputs["Color"], cloud_mask.inputs[0])
L(horizon_fade.outputs["Result"], cloud_mask.inputs[1])
L(ramp.outputs["Color"], mix_clouds.inputs["A"])
L(cloud_mask.outputs["Value"], mix_clouds.inputs["Factor"])
L(norm.outputs["Vector"], sunv.inputs[0])
L(sunv.outputs["Value"], sun_ramp.inputs["Fac"])
L(sunv.outputs["Value"], glow_ramp.inputs["Fac"])
L(mix_clouds.outputs["Result"], mix_glow.inputs["A"])
L(glow_ramp.outputs["Color"], mix_glow.inputs["Factor"])
L(mix_glow.outputs["Result"], mix_sun.inputs["A"])
L(sun_ramp.outputs["Color"], mix_sun.inputs["Factor"])
L(mix_sun.outputs["Result"], emit.inputs["Color"])
L(emit.outputs["Emission"], out.inputs["Surface"])
sky.data.materials.append(m)

# ------------------------------------------------------------------ lights
bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
sun = bpy.context.object
sun.name = "Sun"
sun.data.energy = 3.0
sun.data.color = (1.0, 0.96, 0.88)
sun.data.angle = math.radians(1.5)
# a sun lamp shines along its local -Z; aim -Z at -SUN_DIR so light comes FROM the sun disc
sun.rotation_euler = (math.acos(SUN_DIR[2]), 0, math.atan2(SUN_DIR[1], SUN_DIR[0]) + math.pi / 2)

# world: a physical sky that matches the sun, so lighting and reflections agree
# with the skybox cube (which is what the camera actually sees)
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
for n in list(wnt.nodes):
    wnt.nodes.remove(n)
sky_tex = wnt.nodes.new("ShaderNodeTexSky")
sky_tex.sky_type = "MULTIPLE_SCATTERING"
sky_tex.sun_elevation = math.asin(SUN_DIR[2])
sky_tex.sun_rotation = math.atan2(SUN_DIR[0], SUN_DIR[1])
sky_tex.sun_size = math.radians(1.0)
sky_tex.sun_intensity = 0.3
# blend the sky toward a neutral warm grey so the ambient light doesn't turn
# the character's yellow green
neutral = wnt.nodes.new("ShaderNodeMix")
neutral.name = "NeutralMix"
neutral.data_type = "RGBA"
neutral.inputs["Factor"].default_value = 0.7
neutral.inputs["B"].default_value = (0.86, 0.86, 0.84, 1)
bg = wnt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.4
wout = wnt.nodes.new("ShaderNodeOutputWorld")
wnt.links.new(sky_tex.outputs["Color"], neutral.inputs["A"])
wnt.links.new(neutral.outputs["Result"], bg.inputs["Color"])
wnt.links.new(bg.outputs["Background"], wout.inputs["Surface"])
scene.view_settings.exposure = -0.35

# ------------------------------------------------------------------ camera
bpy.ops.object.camera_add(location=(-60, -120, 18))
cam = bpy.context.object
cam.name = "Camera"
cam.data.lens = 28
cam.data.clip_end = 5000
target = (10, 60, 30)
d = tuple(t - c for t, c in zip(target, cam.location))
dist_xy = math.hypot(d[0], d[1])
# camera looks along its local -Z; pitch from vertical, yaw from +X
cam.rotation_euler = (math.pi / 2 - math.atan2(-d[2], dist_xy), 0, math.atan2(d[1], d[0]) - math.pi / 2)
scene.camera = cam

# ------------------------------------------------------------------ output
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "slimsico.blend"))
scene.render.filepath = os.path.join(out_dir, "renders", "scene.png")
bpy.ops.render.render(write_still=True)
print("DONE ->", scene.render.filepath)
