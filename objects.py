"""BlenQ — object definitions.

The 15 fixed objects. Each one is built from 5-8 simple pieces
(cubes, cylinders, spheres, cones) in normal readable Blender
Python. One script line per piece, plus a short colour loop at the
end that colours pieces below a height split one colour and pieces
above it another colour. That keeps every script inside the model's
256-token limit while staying readable.

Sizes: small 0.8, medium 1.0, large 1.2 — every location and scale
is multiplied by the size factor when the script is generated.
Colours: each object has 3 colour choices; the first is the default.
"""
import copy

# piece: (primitive, location, scale, rotation or None)
# primitive is one of: cube, cylinder, sphere, cone

OBJECTS = {
    "sword": {
        "display": "Sword",
        "synonyms": ["sword", "longsword", "blade"],
        "split": 0.8,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "silver": (0.8, 0.8, 0.85),
            "gold": (0.85, 0.65, 0.2),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("cube", (0, 0, 1.6), (0.12, 0.04, 0.9), None),
            ("cone", (0, 0, 2.6), (0.12, 0.04, 0.2), None),
            ("cube", (0, 0, 0.7), (0.45, 0.08, 0.06), None),
            ("cylinder", (0, 0, 0.45), (0.07, 0.07, 0.25), None),
            ("sphere", (0, 0, 0.15), (0.09, 0.09, 0.09), None),
            ("sphere", (0, 0.08, 0.7), (0.06, 0.04, 0.06), None),
        ],
    },
    "shield": {
        "display": "Shield",
        "synonyms": ["shield", "buckler"],
        "split": 1.0,
        "accent": (0.85, 0.65, 0.2),
        "colours": {
            "red": (0.7, 0.1, 0.1),
            "blue": (0.1, 0.3, 0.8),
            "green": (0.1, 0.6, 0.2),
        },
        "pieces": [
            ("cube", (0, 0, 1.0), (0.7, 0.08, 0.5), None),
            ("sphere", (0, 0.1, 1.0), (0.18, 0.08, 0.18), None),
            ("cone", (0, 0, 1.6), (0.7, 0.08, 0.2), None),
            ("cone", (0, 0, 0.4), (0.7, 0.08, 0.2), (3.14, 0, 0)),
            ("cylinder", (0, -0.12, 1.0), (0.05, 0.05, 0.4), None),
            ("cube", (0, 0, 1.0), (0.75, 0.09, 0.1), None),
        ],
    },
    "axe": {
        "display": "Axe",
        "synonyms": ["axe", "hatchet"],
        "split": 0.8,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "silver": (0.8, 0.8, 0.85),
            "gold": (0.85, 0.65, 0.2),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("cylinder", (0, 0, 0.8), (0.06, 0.06, 0.8), None),
            ("cube", (0, 0, 1.6), (0.35, 0.08, 0.25), None),
            ("cube", (0.35, 0, 1.6), (0.2, 0.06, 0.3), None),
            ("sphere", (0, 0, 0.05), (0.08, 0.08, 0.08), None),
            ("cone", (0, 0, 1.9), (0.08, 0.08, 0.15), None),
        ],
    },
    "war hammer": {
        "display": "War hammer",
        "synonyms": ["war hammer", "hammer"],
        "split": 0.9,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "grey": (0.6, 0.6, 0.65),
            "gold": (0.85, 0.65, 0.2),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("cylinder", (0, 0, 0.9), (0.07, 0.07, 0.9), None),
            ("cube", (0, 0, 1.85), (0.5, 0.25, 0.25), None),
            ("cube", (0.55, 0, 1.85), (0.1, 0.2, 0.2), None),
            ("cone", (-0.55, 0, 1.85), (0.1, 0.1, 0.2), (0, 1.57, 0)),
            ("sphere", (0, 0, 0.05), (0.09, 0.09, 0.09), None),
        ],
    },
    "dagger": {
        "display": "Dagger",
        "synonyms": ["dagger", "knife", "dirk"],
        "split": 0.6,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "silver": (0.8, 0.8, 0.85),
            "gold": (0.85, 0.65, 0.2),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("cube", (0, 0, 1.1), (0.08, 0.03, 0.5), None),
            ("cone", (0, 0, 1.7), (0.08, 0.03, 0.15), None),
            ("cube", (0, 0, 0.6), (0.3, 0.06, 0.05), None),
            ("cylinder", (0, 0, 0.4), (0.05, 0.05, 0.2), None),
            ("sphere", (0, 0, 0.18), (0.06, 0.06, 0.06), None),
        ],
    },
    "helmet": {
        "display": "Helmet",
        "synonyms": ["helmet", "helm", "knight helmet"],
        "split": 1.0,
        "accent": (0.7, 0.1, 0.1),
        "colours": {
            "silver": (0.75, 0.75, 0.8),
            "gold": (0.85, 0.65, 0.2),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("sphere", (0, 0, 1.2), (0.5, 0.5, 0.45), None),
            ("cylinder", (0, 0, 0.9), (0.55, 0.55, 0.05), None),
            ("cube", (0, 0.48, 0.9), (0.08, 0.05, 0.35), None),
            ("cube", (0, 0, 1.68), (0.05, 0.35, 0.18), None),
            ("cube", (-0.42, 0.15, 0.8), (0.06, 0.25, 0.15), None),
            ("cube", (0.42, 0.15, 0.8), (0.06, 0.25, 0.15), None),
        ],
    },
    "crown": {
        "display": "Crown",
        "synonyms": ["crown", "royal crown"],
        "split": 0.3,
        "accent": (0.7, 0.1, 0.1),
        "colours": {
            "gold": (0.85, 0.65, 0.2),
            "silver": (0.8, 0.8, 0.85),
            "red": (0.7, 0.1, 0.1),
        },
        "pieces": [
            ("cylinder", (0, 0, 0.5), (0.5, 0.5, 0.25), None),
            ("cone", (0, 0.45, 0.85), (0.12, 0.12, 0.2), None),
            ("cone", (0.45, 0, 0.85), (0.12, 0.12, 0.2), None),
            ("cone", (0, -0.45, 0.85), (0.12, 0.12, 0.2), None),
            ("cone", (-0.45, 0, 0.85), (0.12, 0.12, 0.2), None),
            ("sphere", (0, 0.5, 0.5), (0.08, 0.05, 0.08), None),
        ],
    },
    "rocket": {
        "display": "Rocket",
        "synonyms": ["rocket", "space rocket", "spaceship"],
        "split": 0.6,
        "accent": (0.7, 0.1, 0.1),
        "colours": {
            "white": (0.9, 0.9, 0.9),
            "red": (0.7, 0.1, 0.1),
            "blue": (0.1, 0.3, 0.8),
        },
        "pieces": [
            ("cylinder", (0, 0, 1.2), (0.35, 0.35, 0.8), None),
            ("cone", (0, 0, 2.15), (0.35, 0.35, 0.35), None),
            ("cube", (0, 0.4, 0.5), (0.05, 0.2, 0.4), None),
            ("cube", (0.35, 0, 0.5), (0.2, 0.05, 0.4), None),
            ("cube", (-0.35, 0, 0.5), (0.2, 0.05, 0.4), None),
            ("sphere", (0, 0.36, 1.4), (0.12, 0.05, 0.12), None),
            ("cylinder", (0, 0, 0.3), (0.2, 0.2, 0.15), None),
            ("cone", (0, 0, 0.05), (0.15, 0.15, 0.2), (3.14, 0, 0)),
        ],
    },
    "car": {
        "display": "Car",
        "synonyms": ["car", "automobile", "vehicle"],
        "split": 0.4,
        "accent": (0.1, 0.1, 0.1),
        "colours": {
            "red": (0.7, 0.1, 0.1),
            "blue": (0.1, 0.3, 0.8),
            "yellow": (0.85, 0.75, 0.1),
        },
        "pieces": [
            ("cube", (0, 0, 0.5), (0.9, 0.4, 0.3), None),
            ("cube", (0, 0, 0.95), (0.55, 0.35, 0.25), None),
            ("cylinder", (0.6, 0.42, 0.25), (0.2, 0.2, 0.08), (1.57, 0, 0)),
            ("cylinder", (-0.6, 0.42, 0.25), (0.2, 0.2, 0.08), (1.57, 0, 0)),
            ("cylinder", (0.6, -0.42, 0.25), (0.2, 0.2, 0.08), (1.57, 0, 0)),
            ("cylinder", (-0.6, -0.42, 0.25), (0.2, 0.2, 0.08), (1.57, 0, 0)),
            ("sphere", (0.92, 0.25, 0.5), (0.06, 0.05, 0.06), None),
            ("sphere", (0.92, -0.25, 0.5), (0.06, 0.05, 0.06), None),
        ],
    },
    "boat": {
        "display": "Boat",
        "synonyms": ["boat", "ship", "sailboat"],
        "split": 1.0,
        "accent": (0.9, 0.9, 0.9),
        # Inverted: the hull (low) takes the named colour and the
        # sail (high) stays white — a brown boat has a brown hull,
        # not a brown sail.
        "invert": True,
        "colours": {
            "brown": (0.5, 0.3, 0.1),
            "red": (0.7, 0.1, 0.1),
            "blue": (0.1, 0.3, 0.8),
        },
        "pieces": [
            ("cube", (0, 0, 0.5), (0.9, 0.35, 0.3), None),
            ("cube", (0, 0, 0.85), (0.7, 0.3, 0.08), None),
            ("cylinder", (0, 0, 1.5), (0.05, 0.05, 0.7), None),
            ("cube", (0.25, 0, 1.5), (0.4, 0.03, 0.6), None),
            ("cube", (0.05, 0, 2.15), (0.15, 0.02, 0.1), None),
            ("cube", (-0.5, 0, 0.95), (0.25, 0.25, 0.15), None),
            # Pointed bow at the front (+X), lying on its side.
            ("cone", (0.95, 0, 0.5), (0.25, 0.25, 0.3), (0, 1.5708, 0)),
        ],
    },
    "castle tower": {
        "display": "Castle tower",
        "synonyms": ["castle tower", "tower", "castle"],
        "split": 0.8,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "grey": (0.6, 0.6, 0.6),
            "brown": (0.5, 0.3, 0.1),
            "white": (0.9, 0.9, 0.9),
        },
        "pieces": [
            ("cylinder", (0, 0, 1.0), (0.6, 0.6, 1.0), None),
            ("cylinder", (0, 0, 2.05), (0.7, 0.7, 0.1), None),
            ("cube", (0.55, 0, 2.2), (0.15, 0.15, 0.15), None),
            ("cube", (-0.55, 0, 2.2), (0.15, 0.15, 0.15), None),
            ("cube", (0, 0.55, 2.2), (0.15, 0.15, 0.15), None),
            ("cube", (0, -0.55, 2.2), (0.15, 0.15, 0.15), None),
            ("cube", (0, 0.6, 0.4), (0.25, 0.05, 0.4), None),
            ("cube", (0, 0.6, 1.4), (0.15, 0.05, 0.15), None),
        ],
    },
    "house": {
        "display": "House",
        "synonyms": ["house", "cottage", "home"],
        "split": 1.2,
        # Warm beige walls — plain white walls vanish against the
        # light backdrop in a render.
        "accent": (0.8, 0.7, 0.55),
        "colours": {
            "red": (0.7, 0.15, 0.1),
            "blue": (0.1, 0.3, 0.8),
            "yellow": (0.85, 0.75, 0.1),
        },
        "pieces": [
            ("cube", (0, 0, 0.6), (0.8, 0.6, 0.6), None),
            ("cone", (0, 0, 1.6), (0.9, 0.7, 0.5), (0, 0, 0.78)),
            ("cube", (0, 0.6, 0.35), (0.2, 0.05, 0.35), None),
            ("cube", (0.45, 0.6, 0.7), (0.2, 0.05, 0.2), None),
            ("cube", (-0.45, 0.6, 0.7), (0.2, 0.05, 0.2), None),
            ("cube", (0.5, 0, 1.5), (0.15, 0.15, 0.4), None),
        ],
    },
    "tree": {
        "display": "Tree",
        "synonyms": ["tree", "oak tree", "pine tree"],
        "split": 0.8,
        "accent": (0.4, 0.25, 0.1),
        "colours": {
            "green": (0.1, 0.6, 0.2),
            "orange": (0.85, 0.45, 0.1),
            "yellow": (0.85, 0.75, 0.1),
        },
        "pieces": [
            ("cylinder", (0, 0, 0.5), (0.15, 0.15, 0.5), None),
            ("sphere", (0, 0, 1.4), (0.6, 0.6, 0.6), None),
            ("sphere", (0.3, 0.2, 1.9), (0.4, 0.4, 0.4), None),
            ("sphere", (-0.3, -0.2, 1.9), (0.4, 0.4, 0.4), None),
            ("cylinder", (0, 0, 0.05), (0.5, 0.5, 0.05), None),
        ],
    },
    "robot": {
        "display": "Robot",
        "synonyms": ["robot", "android"],
        "split": 0.6,
        "accent": (0.7, 0.1, 0.1),
        "colours": {
            "grey": (0.6, 0.6, 0.65),
            "blue": (0.1, 0.3, 0.8),
            "red": (0.7, 0.1, 0.1),
        },
        "pieces": [
            ("cube", (0, 0, 1.0), (0.4, 0.3, 0.5), None),
            ("cube", (0, 0, 1.8), (0.35, 0.3, 0.3), None),
            ("sphere", (0.12, 0.3, 1.85), (0.05, 0.03, 0.05), None),
            ("sphere", (-0.12, 0.3, 1.85), (0.05, 0.03, 0.05), None),
            ("cylinder", (0.5, 0, 1.0), (0.08, 0.08, 0.35), None),
            ("cylinder", (-0.5, 0, 1.0), (0.08, 0.08, 0.35), None),
            ("cylinder", (0.18, 0, 0.3), (0.1, 0.1, 0.3), None),
            ("cylinder", (-0.18, 0, 0.3), (0.1, 0.1, 0.3), None),
        ],
    },
    "treasure chest": {
        "display": "Treasure chest",
        "synonyms": ["treasure chest", "chest", "loot chest"],
        "split": 0.7,
        "accent": (0.85, 0.65, 0.2),
        "colours": {
            "brown": (0.5, 0.3, 0.1),
            "red": (0.7, 0.1, 0.1),
            "black": (0.15, 0.15, 0.18),
        },
        "pieces": [
            ("cube", (0, 0, 0.35), (0.6, 0.4, 0.35), None),
            ("cube", (0, 0, 0.75), (0.6, 0.4, 0.15), None),
            ("cube", (0, 0.42, 0.5), (0.12, 0.05, 0.18), None),
            ("sphere", (0.3, 0, 0.85), (0.08, 0.08, 0.08), None),
            ("sphere", (-0.2, 0.1, 0.85), (0.08, 0.08, 0.08), None),
            ("cube", (0, 0, 0.7), (0.65, 0.42, 0.05), None),
        ],
    },
}

SIZES = {"small": 0.8, "medium": 1.0, "large": 1.2}
PRIMITIVES = {
    "cube": "primitive_cube_add",
    "cylinder": "primitive_cylinder_add",
    "sphere": "primitive_uv_sphere_add",
    "cone": "primitive_cone_add",
}


def _fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _vec(vals, size):
    return "(" + ", ".join(_fmt(v * size) for v in vals) + ")"


def build_script(obj_name, size_name="medium", colour_name=None):
    """Return the readable Blender Python script for one object.

    One line per piece, then a short colour loop. No file access,
    no imports beyond bpy, no hidden behaviour.
    """
    obj = OBJECTS[obj_name]
    size = SIZES[size_name]
    if colour_name is None:
        colour_name = next(iter(obj["colours"]))
    main = obj["colours"][colour_name]
    accent = obj["accent"]
    split = obj["split"] * size
    lines = [
        "import bpy",
        "bpy.ops.object.select_all(action='SELECT')",
        "bpy.ops.object.delete()",
    ]
    for prim, loc, scl, rot in obj["pieces"]:
        call = (
            f"bpy.ops.mesh.{PRIMITIVES[prim]}"
            f"(location={_vec(loc, size)}, scale={_vec(scl, size)}"
        )
        if prim == "cone" and obj_name == "house":
            # 4-sided cone for the roof needs vertices=4; the rotation
            # below turns it 45 degrees so it lines up with the base.
            call += ", vertices=4"
        if rot is not None:
            call += f", rotation={_vec(rot, 1)}"
        call += ")"
        lines.append(call)
    # One line, no indent needed: a colour is picked per object by
    # height, so the script stays flat and readable. Normally the
    # low pieces take the accent colour and the high pieces the
    # named colour; "invert" swaps that (the boat's hull takes the
    # named colour and its sail stays white).
    low, high = ((main, accent) if obj.get("invert")
                 else (accent, main))
    lines.append(
        "for o in bpy.context.scene.objects: o.color=("
        + ", ".join(_fmt(v) for v in low)
        + ", 1) if o.location.z < "
        + _fmt(split)
        + " else("
        + ", ".join(_fmt(v) for v in high)
        + ", 1)"
    )
    return "\n".join(lines)


def object_names():
    return list(OBJECTS)


def piece_count(obj_name):
    return len(OBJECTS[obj_name]["pieces"])
