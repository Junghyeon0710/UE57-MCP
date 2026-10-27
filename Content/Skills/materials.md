# Edit materials through UE 5.7

Use `ue57.material.create_material` and `add_expression`. Expression class names must exist in the current editor. Inspect each expression's properties through `ue57.object` before assigning values.

Connect expressions with actual input/output names. Material properties use the live `MaterialProperty` enum, for example `MP_BASE_COLOR`. Recompile after changing graph connections and save the material. A submitted compile request is not a complete shader diagnostic result; inspect the editor log for material errors.

Material functions, instances, parameters and additional expression APIs are available through `MaterialEditingLibrary`; inspect the live API with `ue57.unreal_api.describe_type`. This implementation does not bundle the historical backport's Material Graph DSL.
