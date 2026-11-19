"""BlenQ — Blender-side job script. Runs INSIDE Blender.

Modes:
  validate: read a JSON list of {id, object, script, expected},
    run each script in a clean scene, and write a JSON list of
    {id, ok, count, error} for each one.
  render: read one script file, build the model, add a camera and
    a light, and render a 512x512 picture to the output path.

Run it with: blender --background --python blender_job.py --
  --mode validate --input in.json --output out.json
"""
import argparse
import json
import sys

import bpy


def _clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)


def _mesh_count():
    return len([o for o in bpy.context.scene.objects if o.type == "MESH"])


def _run_script(script):
    _clear()
    code = compile(script, "<blenq-script>", "exec")
    exec(code, {"__name__": "__main__"})
    return _mesh_count()


def _add_camera_and_light():
    import mathutils
    # Turn each object's viewport colour into a real material, so
    # the colour shows in the render as well as in the viewport.
    mats = {}
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        key = tuple(round(v, 2) for v in o.color[:3])
        if key not in mats:
            mat = bpy.data.materials.new(name="BlenQMat")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = (
                key[0], key[1], key[2], 1)
            bsdf.inputs["Roughness"].default_value = 0.5
            mats[key] = mat
        o.data.materials.clear()
        o.data.materials.append(mats[key])
    bpy.ops.object.light_add(type="SUN", location=(5, 5, 8))
    sun = bpy.context.active_object
    sun.data.energy = 4.0
    bpy.ops.object.light_add(type="POINT", location=(3, 3, 4))
    fill = bpy.context.active_object
    fill.data.energy = 200.0
    bpy.ops.object.camera_add(location=(3.8, 3.8, 2.8))
    cam = bpy.context.active_object
    direction = mathutils.Vector((0, 0, 1.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.62, 0.62, 0.66, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0


def do_validate(inp, outp):
    with open(inp) as f:
        jobs = json.load(f)
    results = []
    for job in jobs:
        try:
            count = _run_script(job["script"])
            ok = count == job["expected"]
            results.append({
                "id": job["id"],
                "ok": ok,
                "count": count,
                "error": None if ok else (
                    f"expected {job['expected']} mesh objects, "
                    f"got {count}"
                ),
            })
        except Exception as e:  # noqa: BLE001 - report, do not stop
            results.append({
                "id": job["id"], "ok": False, "count": 0,
                "error": f"{type(e).__name__}: {e}",
            })
    with open(outp, "w") as f:
        json.dump(results, f)


def do_render(inp, outp):
    with open(inp) as f:
        script = f.read()
    _run_script(script)
    _add_camera_and_light()
    scene = bpy.context.scene
    # Blender 4.2-4.4 calls it BLENDER_EEVEE_NEXT; Blender 5.0+
    # renamed it back to BLENDER_EEVEE. Try the new name first.
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except Exception:
            continue
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.filepath = outp
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("validate", "render"))
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    if args.mode == "validate":
        do_validate(args.input, args.output)
    else:
        do_render(args.input, args.output)


main()
