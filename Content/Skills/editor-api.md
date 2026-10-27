# Discover and use UE 5.7 editor APIs

Read `ue57.unreal_api.list_types` and `describe_type` before invoking an unfamiliar API. Domain toolsets filter the same live API catalog. Empty results mean the relevant editor plugin is not loaded; they do not imply a working substitute.

`invoke` accepts a class name such as `EditorAssetLibrary`, an object reference, or `{"$subsystem":"EditorActorSubsystem"}`. Supply positional `args` and named `kwargs` from the actual method documentation.

Tagged values cross the JSON boundary:

- Object: `{"$ref":"/Game/Materials/M_Test.M_Test"}`; reuse references returned by tools.
- Class: `{"$class":"StaticMeshActor"}` or a Blueprint generated-class path.
- Struct: `{"$struct":"Vector","x":100,"y":0,"z":50}`.
- Enum: `{"$enum":"CollisionEnabled","value":"QUERY_ONLY"}`.

All engine calls run on the editor main thread. Serialize dependent mutations. Inspect returned values, compile and save modified assets when the task calls for it. The API tool can call arbitrary editor functions; it is not a sandbox.
