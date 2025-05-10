import bpy
import bmesh
import random
import math

# --- Parámetros del Script ---
# Estas son variables globales que puedes modificar para cambiar el resultado de la ciudad generada.

# --- Configuraciones del Terreno ---
grid_size = 20
x_subdivisions = 20
y_subdivisions = 30
terrain_height_scale = 0.0 # Si es 0.0, el terreno será plano.
terrain_wave_frequency = 0.0 # Frecuencia de las "ondas" del terreno.

# --- Configuraciones de Edificios ---
building_min_height = 1
building_max_height = 7.0
street_width_factor = 0.5 # Factor (0.0 a 1.0) para el ancho de las calles.
building_embed_depth = 0.1 # Profundidad que los edificios se "entierran" en el terreno.

# --- Funciones Auxiliares ---

def clear_scene():
    """
    Limpia la escena actual eliminando todos los objetos de tipo MESH
    e intenta eliminar colecciones vacías.
    """
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    
    if bpy.context.selected_objects:
        bpy.ops.object.delete()

    collections_to_remove = []
    for collection in bpy.data.collections:
        if not collection.objects:
            is_scene_collection_child = collection.name in bpy.context.scene.collection.children
            can_be_removed = True
            # No borra la colección maestra de la escena actual.
            if collection == bpy.context.scene.collection:
                can_be_removed = False
            # Aquí se podrían añadir más condiciones para preservar colecciones específicas.

            if can_be_removed:
                if is_scene_collection_child:
                    bpy.context.scene.collection.children.unlink(collection)
                if collection.users == 0:
                    collections_to_remove.append(collection)

    for coll in collections_to_remove:
        bpy.data.collections.remove(coll)
    # Se eliminó: print("Objetos de malla existentes limpiados...")

def create_terrain(name="Terrain"):
    """
    Crea un objeto Grid y modifica la Z de sus vértices para representar un terreno.
    """
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=x_subdivisions,
        y_subdivisions=y_subdivisions,
        size=grid_size,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 0)
    )
    terrain_obj = bpy.context.active_object
    terrain_obj.name = name
    mesh = terrain_obj.data

    # Se eliminó: print(f"Cuadrícula creada con {len(mesh.vertices)} vértices.")

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()

    for vert in bm.verts:
        # Cálculo de la altura del terreno basado en ondas sinusoidales.
        # Si terrain_wave_frequency es 0, los offsets serán 0, resultando en z1=0, z2=1, z3=sin(1), z4=1.
        offset_x = vert.co.x * terrain_wave_frequency
        offset_y = vert.co.y * terrain_wave_frequency
        z1 = math.sin(offset_x)
        z2 = math.cos(offset_y)
        z3 = math.sin(offset_x * 0.5 + 1.0) # Introduce más variación
        z4 = math.cos(offset_y * 0.5)
        # Si terrain_height_scale es 0.0, vert.co.z será 0.0 (terreno plano).
        vert.co.z = (z1 * z2 + z3 * z4) * terrain_height_scale / 2.0

    bmesh.update_edit_mesh(mesh)
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Se eliminó: print("Terreno deformado usando funciones matemáticas.")
    return terrain_obj

def create_buildings(terrain_obj):
    """
    Crea edificios (cubos) en cada vértice del terreno, adaptándose a su altura.
    """
    if not terrain_obj or not terrain_obj.data:
        print("Error: Objeto terreno no encontrado o sin datos de malla.")
        return

    mesh = terrain_obj.data
    vertices = mesh.vertices

    if x_subdivisions == 0 or y_subdivisions == 0:
        print("Error: Las subdivisiones no pueden ser cero.")
        return
        
    cell_width_x = grid_size / x_subdivisions
    cell_width_y = grid_size / y_subdivisions

    building_size_x = cell_width_x * (1.0 - street_width_factor)
    building_size_y = cell_width_y * (1.0 - street_width_factor)
    
    # Se eliminaron prints de dimensiones de celda y edificio.

    building_collection_name = "Buildings"
    if building_collection_name in bpy.data.collections:
        building_collection = bpy.data.collections[building_collection_name]
    else:
        building_collection = bpy.data.collections.new(building_collection_name)
        bpy.context.scene.collection.children.link(building_collection)

    building_count = 0
    for vert_idx, vert in enumerate(vertices):
        world_co = terrain_obj.matrix_world @ vert.co # Coordenada global del vértice.
        terrain_z_at_vertex = world_co.z

        building_height = random.uniform(building_min_height, building_max_height)
        # La base del edificio se hunde ligeramente en el terreno.
        base_z = terrain_z_at_vertex - building_embed_depth
        center_z = base_z + (building_height / 2)
        location_x = world_co.x
        location_y = world_co.y

        bpy.ops.mesh.primitive_cube_add(
            size=1,
            enter_editmode=False,
            align='WORLD',
            location=(location_x, location_y, center_z)
        )
        building_obj = bpy.context.active_object
        building_obj.name = f"Building_{building_count:03d}"
        building_count += 1
        building_obj.dimensions = (building_size_x, building_size_y, building_height)
        
        # Asegura que el edificio esté solo en la colección "Buildings".
        original_collections = [coll for coll in building_obj.users_collection]
        for coll in original_collections:
            coll.objects.unlink(building_obj)
        building_collection.objects.link(building_obj)

        # Se eliminó el print de progreso de creación de edificios.
    # Se eliminó: print(f"Creados {building_count} edificios.")

def setup_scene():
    """
    Configura luz, cámara, motor de render y materiales básicos.
    """
    bpy.ops.object.select_all(action='DESELECT')
    # Limpia luces y cámaras existentes.
    objects_to_delete = [obj for obj in bpy.data.objects if obj.type in ('LIGHT', 'CAMERA')]
    if objects_to_delete:
        for obj_type in ('LIGHT', 'CAMERA'):
            bpy.ops.object.select_by_type(type=obj_type)
            if bpy.context.selected_objects: # Solo borra si hay algo seleccionado de ese tipo
                bpy.ops.object.delete(use_global=False)
        bpy.ops.object.select_all(action='DESELECT') # Deseleccionar después de borrar
    # Se eliminaron prints de luces/cámaras eliminadas para mayor limpieza.

    # --- Creación de Luz Solar ---
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_data.energy = 4
    light_data.angle = math.radians(5) # Ángulo del sol para sombras (originalmente 0.1 que es ~5.7 grados)
    light_object = bpy.data.objects.new(name="SunLightObj", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_object)
    light_object.location = (grid_size * 0.8, -grid_size * 0.8, grid_size * 1.2)
    light_object.rotation_euler = (math.radians(45), math.radians(5), math.radians(-45))

    # --- Creación de Cámara ---
    cam_data = bpy.data.cameras.new(name="SceneCamera")
    cam_object = bpy.data.objects.new(name="SceneCameraObj", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_object)
    bpy.context.scene.camera = cam_object # Establece como cámara activa.
    
    cam_object.location = (grid_size * 1.2, -grid_size * 1.2, grid_size * 0.9)
    cam_object.rotation_euler = (math.radians(60), 0, math.radians(-45))

    # Se eliminó: print("Escena configurada con luz y cámara.")

    # --- Configuración del Motor de Render (Cycles) ---
    bpy.context.scene.render.engine = 'CYCLES'
    try:
        bpy.context.scene.cycles.device = 'GPU'
        # Re-verifica porque a veces se establece pero no es efectivo
        if bpy.context.scene.cycles.device != 'GPU': 
            print("GPU no establecida efectivamente o no disponible, usando CPU.")
            bpy.context.scene.cycles.device = 'CPU'
        else:
            print("Dispositivo de Cycles establecido en GPU.")
    except Exception as e:
        print(f"No se pudo establecer Cycles en GPU ({e}), usando CPU.")
        bpy.context.scene.cycles.device = 'CPU'

    bpy.context.scene.cycles.samples = 128 # Muestras para el render final.
    if hasattr(bpy.context.scene.cycles, 'adaptive_min_samples'): # Para versiones nuevas de Blender.
        bpy.context.scene.cycles.adaptive_min_samples = 64
    bpy.context.scene.cycles.use_denoising = True
    
    # --- Creación y Asignación de Materiales ---
    # Material para el Terreno
    terrain_mat_name = "TerrainMaterial"
    if terrain_mat_name in bpy.data.materials:
        terrain_mat = bpy.data.materials[terrain_mat_name]
    else:
        terrain_mat = bpy.data.materials.new(name=terrain_mat_name)
        terrain_mat.use_nodes = True
        bsdf = terrain_mat.node_tree.nodes.get('Principled BSDF')
        if not bsdf:
            bsdf = terrain_mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.15, 0.2, 0.1, 1) # Verde/marrón oscuro.
            bsdf.inputs['Roughness'].default_value = 0.9
    
    terrain = bpy.data.objects.get("Terrain")
    if terrain:
        if terrain.data.materials:
            terrain.data.materials[0] = terrain_mat
        else:
            terrain.data.materials.append(terrain_mat)

    # Material para los Edificios
    building_mat_name = "BuildingMaterial"
    if building_mat_name in bpy.data.materials:
        building_mat = bpy.data.materials[building_mat_name]
    else:
        building_mat = bpy.data.materials.new(name=building_mat_name)
        building_mat.use_nodes = True
        bsdf_building = building_mat.node_tree.nodes.get('Principled BSDF')
        if not bsdf_building:
            bsdf_building = building_mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        if bsdf_building:
            bsdf_building.inputs['Base Color'].default_value = (0.7, 0.7, 0.72, 1) # Gris claro.
            bsdf_building.inputs['Roughness'].default_value = 0.7
            bsdf_building.inputs['Metallic'].default_value = 0.0 
    
    buildings_collection = bpy.data.collections.get("Buildings")
    if buildings_collection:
        for obj in buildings_collection.objects:
            if obj.type == 'MESH':
                if obj.data.materials:
                    obj.data.materials[0] = building_mat
                else:
                    obj.data.materials.append(building_mat)

# --- Ejecución Principal del Script ---

if __name__ == "__main__":
    clear_scene()
    terrain_object = create_terrain()
    if terrain_object:
        create_buildings(terrain_object)
    setup_scene()
