"""5.7의 공개 API와 직접 작성한 편집 도구를 MCP에 등록한다."""
import fnmatch
import json
from pathlib import Path
from .protocol import Registry

# 실제 에디터에 로드된 타입만 검색하며, 누락된 플러그인의 기능을 지원한다고 표시하지 않는다.
DOMAINS={
    "animation":["Anim*","Animation*","Skeleton*"],
    "sequencer":["LevelSequence*","MovieScene*","Sequencer*"],
    "control_rig":["ControlRig*","RigVM*","RigHierarchy*"],
    "niagara":["Niagara*"],
    "pcg":["PCG*"],
    "dataflow":["Dataflow*"],
    "cloth":["ChaosCloth*","Clothing*"],
    "mvvm":["MVVM*"],
    "behavior_tree":["BehaviorTree*","Blackboard*","BT*"],
    "state_tree":["StateTree*"],
    "gameplay_abilities":["AbilitySystem*","GameplayAbility*","GameplayEffect*"],
    "gameplay_tags":["GameplayTag*"],
    "game_features":["GameFeature*"],
    "conversation":["Conversation*"],
    "data_registry":["DataRegistry*"],
    "metahuman":["MetaHuman*"],
    "physics":["Physics*","Body*","Constraint*","Chaos*"],
    "mesh":["StaticMesh*","SkeletalMesh*","Skeletal*","Mesh*"],
    "texture":["Texture*","RenderTarget*"],
    "tables":["DataTable*","CurveTable*","StringTable*","DataTableFunctionLibrary"],
    "landscape":["Landscape*"],
    "camera":["Camera*","CineCamera*","GameplayCamera*"],
    "level":["LevelEditor*","Level*","World*","EditorLevel*"],
    "input":["Input*","EnhancedInput*"],
    "audio":["Audio*","Sound*","MetaSound*"],
    "slate":["Slate*","Widget*","EditorUtility*"],
    "automation":["Automation*","FunctionalTest*"],
    "plugins":["Plugin*","ProjectDescriptor*"],
    "settings":["EditorSettings*","DeveloperSettings*","ProjectSettings*","EditorLoadingSaving*"],
}

def create_registry(runtime):
    """도구 모음별 구현을 바인딩하고 실재하는 API 타입을 함께 노출한다."""
    registry=Registry();ue=runtime.ue
    tool=registry.register
    encode=runtime.encode;decode=runtime.decode
    def subsystem(name):return ue.get_editor_subsystem(runtime.api_type(name))

    @tool("ue57.editor","Get engine version, project and the live tool count.",True)
    def status():
        return {"implementation":"original-ue57","engine":ue.SystemLibrary.get_engine_version(),"project":ue.Paths.get_project_file_path(),
                "native_bridge":hasattr(ue,"UE57MCPNativeLibrary"),**registry.catalog()}

    @tool("ue57.editor","Execute Python in the editor main thread. Assign result for structured output.")
    def execute_python(code:str):return runtime.execute_python(code)

    @tool("ue57.editor","Execute an Unreal editor console command.")
    def console_command(command:str):
        world=subsystem("UnrealEditorSubsystem").get_editor_world()
        ue.SystemLibrary.execute_console_command(world,command)
        return {"submitted":True,"command":command}

    @tool("ue57.editor","Read the editor viewport camera location and rotation.",True)
    def get_viewport():return encode(ue.EditorLevelLibrary.get_level_viewport_camera_info())

    @tool("ue57.editor","Set the editor viewport camera using tagged Vector and Rotator values.")
    def set_viewport(location:dict,rotation:dict):
        ue.EditorLevelLibrary.set_level_viewport_camera_info(decode(location),decode(rotation))
        return get_viewport()

    @tool("ue57.unreal_api","Find actual API names in this running UE 5.7 editor.",True)
    def list_types(pattern:str="*",limit:int=200):return runtime.type_names(pattern,limit)

    @tool("ue57.unreal_api","Inspect actual methods and documentation before invoking an API.",True)
    def describe_type(name:str,pattern:str="*",limit:int=80):return runtime.describe(name,pattern,limit)

    @tool("ue57.unreal_api","Invoke a public Unreal API class, object or subsystem method using tagged arguments.")
    def invoke(target,method:str,args:list=None,kwargs:dict=None):return runtime.invoke(target,method,args,kwargs)

    @tool("ue57.object","Discover reflected property names and values before editing an object.",True)
    def list_properties(target):return runtime.properties(target)

    @tool("ue57.object","Read named editor properties using the exact discovered names.",True)
    def get_properties(target,names:list):return runtime.read_properties(target,names)

    @tool("ue57.object","Set editor properties in a transaction; restore prior values if assignment fails.")
    def set_properties(target,values:dict):return runtime.write_properties(target,values)

    @tool("ue57.object","Invoke a public method on an existing object reference.")
    def call_method(target,method:str,args:list=None,kwargs:dict=None):return runtime.invoke(target,method,args,kwargs)

    @tool("ue57.actor","List actors by label or object name. Supports wildcard patterns.",True)
    def list_actors(pattern:str="*",limit:int=200):
        return encode([actor for actor in subsystem("EditorActorSubsystem").get_all_level_actors()
            if fnmatch.fnmatchcase(actor.get_actor_label().lower(),pattern.lower()) or fnmatch.fnmatchcase(actor.get_name().lower(),pattern.lower())][:max(1,min(limit,2000))])

    @tool("ue57.actor","Read the current actor selection.",True)
    def selected_actors():return encode(subsystem("EditorActorSubsystem").get_selected_level_actors())

    @tool("ue57.actor","Replace the current actor selection with object references.")
    def select_actors(actors:list):
        subsystem("EditorActorSubsystem").set_selected_level_actors(decode(actors));return selected_actors()

    @tool("ue57.actor","Spawn an actor from a discovered class and optional Vector/Rotator values.")
    def spawn_actor(actor_class,location:dict=None,rotation:dict=None,label:str=""):
        actor=subsystem("EditorActorSubsystem").spawn_actor_from_class(decode(actor_class),decode(location) if location else ue.Vector(),decode(rotation) if rotation else ue.Rotator())
        if actor is None:raise RuntimeError("Actor creation failed")
        if label:actor.set_actor_label(label)
        return encode(actor)

    @tool("ue57.actor","Duplicate an actor in the current editor world.")
    def duplicate_actor(actor):
        copy=subsystem("EditorActorSubsystem").duplicate_actor(decode(actor))
        if copy is None:raise RuntimeError("Actor duplication failed")
        return encode(copy)

    @tool("ue57.actor","Destroy the specified actor in the editor world.")
    def delete_actor(actor):
        if not subsystem("EditorActorSubsystem").destroy_actor(decode(actor)):raise RuntimeError("Actor deletion failed")
        return {"deleted":True}

    @tool("ue57.actor","Read actor location, rotation and scale.",True)
    def get_transform(actor):
        obj=decode(actor)
        return {"location":encode(obj.get_actor_location()),"rotation":encode(obj.get_actor_rotation()),"scale":encode(obj.get_actor_scale3d())}

    @tool("ue57.actor","Set actor location, rotation and scale using tagged values.")
    def set_transform(actor,location:dict=None,rotation:dict=None,scale:dict=None):
        obj=decode(actor)
        with ue.ScopedEditorTransaction("UE57 MCP: actor transform"):
            obj.modify()
            if location is not None:obj.set_actor_location(decode(location),False,True)
            if rotation is not None:obj.set_actor_rotation(decode(rotation),True)
            if scale is not None:obj.set_actor_scale3d(decode(scale))
        return get_transform(actor)

    @tool("ue57.asset","Find asset paths under a content root using a wildcard name filter.",True)
    def find_assets(root:str="/Game",pattern:str="*",limit:int=200):
        paths=ue.EditorAssetLibrary.list_assets(root,recursive=True,include_folder=False)
        return [path for path in paths if fnmatch.fnmatchcase(path.rsplit("/",1)[-1].lower(),pattern.lower())][:max(1,min(limit,5000))]

    @tool("ue57.asset","Load an asset and return its object reference.",True)
    def load_asset(path:str):
        obj=ue.EditorAssetLibrary.load_asset(path)
        if obj is None:raise ValueError("Asset not found: "+path)
        return encode(obj)

    @tool("ue57.asset","Save an existing loaded asset.")
    def save_asset(asset):
        if not ue.EditorAssetLibrary.save_loaded_asset(decode(asset),only_if_is_dirty=False):raise RuntimeError("Asset save failed")
        return {"saved":True}

    @tool("ue57.asset","Duplicate an asset to a new package path.")
    def duplicate_asset(source:str,destination:str):
        if ue.EditorAssetLibrary.does_asset_exist(destination):raise ValueError("Destination asset already exists")
        result=ue.EditorAssetLibrary.duplicate_asset(source,destination)
        if result is None:raise RuntimeError("Asset duplication failed")
        return encode(result)

    @tool("ue57.asset","Rename or move an asset to a new package path.")
    def rename_asset(source:str,destination:str):
        if ue.EditorAssetLibrary.does_asset_exist(destination):raise ValueError("Destination asset already exists")
        if not ue.EditorAssetLibrary.rename_asset(source,destination):raise RuntimeError("Asset rename failed")
        return {"renamed":True,"destination":destination}

    @tool("ue57.asset","Delete an asset. Review references before calling this destructive operation.")
    def delete_asset(path:str):
        if not ue.EditorAssetLibrary.delete_asset(path):raise RuntimeError("Asset deletion failed")
        return {"deleted":True}

    @tool("ue57.asset","Create a new asset with an actual Unreal class and factory.")
    def create_asset(name:str,package_path:str,asset_class:str,factory_class:str):
        destination=package_path.rstrip("/")+"/"+name
        if ue.EditorAssetLibrary.does_asset_exist(destination):raise ValueError("Asset already exists")
        factory=runtime.api_type(factory_class)()
        obj=ue.AssetToolsHelpers.get_asset_tools().create_asset(name,package_path,runtime.api_type(asset_class),factory)
        if obj is None:raise RuntimeError("Asset creation failed")
        return encode(obj)

    @tool("ue57.asset","Read asset metadata tags.",True)
    def get_metadata(asset):return encode(ue.EditorAssetLibrary.get_metadata_tag_values(decode(asset)))

    @tool("ue57.asset","Set a metadata tag on an asset.")
    def set_metadata(asset,key:str,value:str):
        ue.EditorAssetLibrary.set_metadata_tag(decode(asset),key,value);return get_metadata(asset)

    @tool("ue57.blueprint","Create an Actor Blueprint using the UE 5.7 BlueprintFactory.")
    def create_blueprint(name:str,package_path:str,parent_class:str="Actor"):
        if ue.EditorAssetLibrary.does_asset_exist(package_path.rstrip("/")+"/"+name):raise ValueError("Asset already exists")
        factory=ue.BlueprintFactory();factory.set_editor_property("parent_class",runtime.api_type(parent_class))
        obj=ue.AssetToolsHelpers.get_asset_tools().create_asset(name,package_path,ue.Blueprint,factory)
        if obj is None:raise RuntimeError("Blueprint creation failed")
        return encode(obj)

    @tool("ue57.blueprint","Compile a Blueprint and return its status.")
    def compile_blueprint(blueprint):
        obj=decode(blueprint)
        if hasattr(ue,"UE57MCPNativeLibrary"):return runtime.native("blueprint.compile",{"asset":obj.get_path_name()})
        ue.BlueprintEditorLibrary.compile_blueprint(obj)
        return {"submitted":True,"diagnostics_available":False,"note":"Use the native bridge or inspect the editor log for compile errors"}

    @tool("ue57.blueprint","Read graphs, nodes and pins through the optional native bridge.",True)
    def get_graph(blueprint,graph:str="EventGraph"):
        return runtime.native("blueprint.graph",{"asset":decode(blueprint).get_path_name(),"graph":graph})

    @tool("ue57.blueprint","Add a public reflected function call node through the native bridge.")
    def add_call_node(blueprint,function_path:str,graph:str="EventGraph",x:int=0,y:int=0):
        return runtime.native("blueprint.add_call",{"asset":decode(blueprint).get_path_name(),"graph":graph,"function":function_path,"x":x,"y":y})

    @tool("ue57.blueprint","Connect named pins on graph nodes through the native bridge.")
    def connect_pins(blueprint,source_node:str,source_pin:str,target_node:str,target_pin:str,graph:str="EventGraph"):
        return runtime.native("blueprint.connect",{"asset":decode(blueprint).get_path_name(),"graph":graph,"source_node":source_node,"source_pin":source_pin,"target_node":target_node,"target_pin":target_pin})

    @tool("ue57.blueprint","Set a graph pin default value through the native bridge.")
    def set_pin_default(blueprint,node:str,pin:str,value:str,graph:str="EventGraph"):
        return runtime.native("blueprint.pin_default",{"asset":decode(blueprint).get_path_name(),"graph":graph,"node":node,"pin":pin,"value":value})

    @tool("ue57.widget","Create a Widget Blueprint asset through the optional native bridge.")
    def create_widget_blueprint(name:str,package_path:str):return runtime.native("widget.create",{"name":name,"package_path":package_path})

    @tool("ue57.widget","Read the Widget Blueprint tree and widget object references.",True)
    def get_widget_tree(blueprint):return runtime.native("widget.tree",{"asset":decode(blueprint).get_path_name()})

    @tool("ue57.widget","Add a widget to a named parent, or create the root when parent is empty.")
    def add_widget(blueprint,widget_class:str,name:str,parent:str=""):
        return runtime.native("widget.add",{"asset":decode(blueprint).get_path_name(),"class":widget_class,"name":name,"parent":parent})

    @tool("ue57.widget","Remove a named widget from a Widget Blueprint.")
    def remove_widget(blueprint,name:str):return runtime.native("widget.remove",{"asset":decode(blueprint).get_path_name(),"name":name})

    @tool("ue57.widget","Move a widget to a different panel within the same Widget Blueprint.")
    def move_widget(blueprint,name:str,parent:str):return runtime.native("widget.move",{"asset":decode(blueprint).get_path_name(),"name":name,"parent":parent})

    @tool("ue57.material","Create a material asset.")
    def create_material(name:str,package_path:str):return create_asset(name,package_path,"Material","MaterialFactoryNew")

    @tool("ue57.material","Create a material expression at graph coordinates.")
    def add_expression(material,expression_class:str,x:int=0,y:int=0):
        obj=ue.MaterialEditingLibrary.create_material_expression(decode(material),runtime.api_type(expression_class),x,y)
        if obj is None:raise RuntimeError("Material expression creation failed")
        return encode(obj)

    @tool("ue57.material","Connect a material expression output to another expression's input.")
    def connect_expressions(source,source_output:str,target,target_input:str):
        if not ue.MaterialEditingLibrary.connect_material_expressions(decode(source),source_output,decode(target),target_input):raise RuntimeError("Expression connection failed")
        return {"connected":True}

    @tool("ue57.material","Connect an expression to a material property, such as MP_BASE_COLOR.")
    def connect_material_property(expression,output:str,property_name:str):
        property_value=getattr(ue.MaterialProperty,property_name)
        if not ue.MaterialEditingLibrary.connect_material_property(decode(expression),output,property_value):raise RuntimeError("Material property connection failed")
        return {"connected":True}

    @tool("ue57.material","Recompile a material after graph edits.")
    def recompile_material(material):
        ue.MaterialEditingLibrary.recompile_material(decode(material));return {"submitted":True}

    @tool("ue57.skills","List the plugin's bundled editor workflow instructions.",True)
    def list_skills():
        root=Path(__file__).resolve().parents[2]/"Skills"
        return [{"name":path.stem,"summary":path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ")} for path in sorted(root.glob("*.md"))]

    @tool("ue57.skills","Read a named bundled workflow skill.",True)
    def read_skill(name:str):
        if not name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in name):raise ValueError("Invalid skill name")
        path=Path(__file__).resolve().parents[2]/"Skills"/(name+".md")
        if not path.is_file():raise ValueError("Unknown skill")
        return path.read_text(encoding="utf-8")

    for domain,patterns in DOMAINS.items():
        register_domain(registry,runtime,domain,patterns)
    from .semantic import register_semantic
    register_semantic(registry,runtime)
    return registry

def register_domain(registry,runtime,domain,patterns):
    """분야별로 실제 5.7 타입을 탐색하고 동일한 공개 API 호출 규약을 적용한다."""
    def list_types(pattern:str="*",limit:int=200):
        return [name for name in dir(runtime.ue) if not name.startswith("_") and fnmatch.fnmatchcase(name.lower(),pattern.lower())
                and any(fnmatch.fnmatchcase(name,p) for p in patterns)][:max(1,min(limit,2000))]
    def describe_type(name:str,pattern:str="*",limit:int=80):
        if not any(fnmatch.fnmatchcase(name,p) for p in patterns):raise ValueError("Use ue57.unreal_api for types outside this domain")
        return runtime.describe(name,pattern,limit)
    def invoke(target,method:str,args:list=None,kwargs:dict=None):return runtime.invoke(target,method,args,kwargs)
    prefix="ue57."+domain
    registry.add(prefix,"list_types",list_types,"Discover available "+domain+" types in this editor. An empty list means the required plugin is not loaded.",True)
    registry.add(prefix,"describe_type",describe_type,"Read actual "+domain+" API members and signatures.",True)
    registry.add(prefix,"invoke",invoke,"Invoke a discovered UE 5.7 API. Use tagged object, subsystem, enum and struct arguments.")
