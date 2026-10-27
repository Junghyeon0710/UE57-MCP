# Toolsets

The full backport registers **55 toolsets and 858 tools**. This is the same catalog as the existing full UE 5.7 port. Counts describe registered tools; they do not imply every UE 5.8-only engine feature exists in UE 5.7. See [compatibility](compatibility.md).

| Toolset | Tools |
| --- | ---: |
| `ToolsetRegistry.AgentSkillToolset` | 4 |
| `AutomationTestToolset.AutomationTestToolset` | 7 |
| `ConfigSettingsToolset.ConfigSettingsToolset` | 8 |
| `ChaosClothAssetToolset.ChaosClothAssetToolset` | 6 |
| `DataflowAgent.DataflowAgentToolset` | 22 |
| `DataRegistryToolset.DataRegistryTools` | 7 |
| `GameFeaturesToolset.GameFeaturesToolset` | 7 |
| `EditorToolset.EditorAppToolset` | 22 |
| `EditorToolset.LogsToolset` | 4 |
| `EditorToolset.BlueprintTools` | 53 |
| `EditorToolset.CurveTableTools` | 9 |
| `EditorToolset.MaterialInstanceTools` | 13 |
| `GameplayTagsToolset.GameplayTagsToolset` | 6 |
| `GASToolsets.GameplayCueToolset` | 8 |
| `GASToolsets.AttributeSetToolset` | 2 |
| `GASToolsets.AbilitySystemInspectorToolset` | 4 |
| `LiveCodingToolset.LiveCodingToolset` | 1 |
| `PCGToolset.PCGToolset` | 31 |
| `PCGToolset.PCGSpatialToolset` | 1 |
| `PhysicsToolsets.PhysicsAssetToolset` | 17 |
| `MVVMToolset.MVVMToolset` | 9 |
| `NiagaraToolsets.NiagaraToolset_Info` | 1 |
| `NiagaraToolsets.NiagaraToolset_Component` | 1 |
| `NiagaraToolsets.NiagaraToolset_Blueprint` | 2 |
| `NiagaraToolsets.NiagaraToolset_System` | 46 |
| `NiagaraToolsets.NiagaraToolset_Assets` | 3 |
| `SemanticSearchToolset.SemanticSearchToolset` | 2 |
| `PluginToolset.PluginToolset` | 17 |
| `WorldConditionsToolset.WorldConditionTools` | 2 |
| `SlateInspectorToolset.SlateInspectorToolset` | 14 |
| `UMGToolSet.UMGToolSet` | 23 |
| `state_tree_toolset.toolsets.state_tree.StateTreeTools` | 9 |
| `metahuman_toolset.metahuman.MetaHumanToolset` | 9 |
| `editor_toolset.toolsets.actor.ActorTools` | 17 |
| `editor_toolset.toolsets.asset.AssetTools` | 21 |
| `editor_toolset.toolsets.data_asset.DataAssetTools` | 1 |
| `editor_toolset.toolsets.data_table.DataTableTools` | 10 |
| `editor_toolset.toolsets.material.MaterialTools` | 28 |
| `editor_toolset.toolsets.object.ObjectTools` | 6 |
| `editor_toolset.toolsets.primitive.PrimitiveTools` | 4 |
| `editor_toolset.toolsets.scene.SceneTools` | 20 |
| `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools` | 22 |
| `editor_toolset.toolsets.static_mesh.StaticMeshTools` | 16 |
| `editor_toolset.toolsets.string_table.StringTableTools` | 8 |
| `editor_toolset.toolsets.texture.TextureTools` | 2 |
| `conversation_toolset.toolsets.conversation.ConversationTools` | 7 |
| `animation_toolset.toolsets.controlrig.ControlRigTools` | 44 |
| `animation_toolset.toolsets.sequencer.SequencerTools` | 140 |
| `animation_toolset.toolsets.keyframing.SequencerKeyframingTools` | 22 |
| `animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools` | 72 |
| `animation_toolset.toolsets.outliner.SequencerOutlinerTools` | 18 |
| `animation_toolset.toolsets.conditions.SequencerConditionTools` | 9 |
| `animation_toolset.toolsets.custom_bindings.SequencerCustomBindingTools` | 8 |
| `animation_toolset.toolsets.import_export.SequencerImportExportTools` | 6 |
| `aimodule_toolset.toolsets.behavior_tree.BehaviorTreeTools` | 7 |

The complete callable names are in [tool-catalog.json](tool-catalog.json). `scripts/verify.py` compares the live editor against every name, not only the totals. Discover argument schemas from the running editor.
