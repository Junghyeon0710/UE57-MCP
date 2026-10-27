# Author Widget Blueprints

Widget tree tools require `UE57MCPNative`. Create the asset with `ue57.widget.create_widget_blueprint`. Add a root panel first with an empty `parent`, then add children using actual panel widget names.

`get_widget_tree` returns widget and slot object references. Discover properties with `ue57.object.list_properties`, then use `set_properties` with the exact names and tagged struct/enum values. Layout values belong to the returned slot, not always to the widget itself. Read the slot's live properties rather than guessing its type.

Compile the Widget Blueprint after structural edits. Save the asset once the tree and compilation status are correct. `move_widget` creates the destination panel's slot; inspect and configure its layout again. Preserve bindings/animations deliberately when restructuring an existing widget. This bridge does not claim automatic migration of every UMG/MVVM reference.
