# Edit UE 5.7 Blueprints

Create an Actor Blueprint with `ue57.blueprint.create_blueprint`. Read `get_graph` before changing a graph; it returns actual node names, GUIDs, pin directions, defaults and links. Graph editing needs the optional `UE57MCPNative` plugin, compiled against the installed UE 5.7 engine.

`add_call_node` takes a reflected function path. Use the created node's returned name in `set_pin_default` and `connect_pins`. Connections must join an output to an input and pass the graph schema. Invalid names or incompatible pins return errors.

Compile with `compile_blueprint`, inspect the status, and save using `ue57.asset.save_asset`. A graph edit alone is not proof of a valid compiled Blueprint. Broader available Blueprint APIs can be discovered through `ue57.unreal_api`; this plugin does not provide Epic's UE 5.8 tool names.
