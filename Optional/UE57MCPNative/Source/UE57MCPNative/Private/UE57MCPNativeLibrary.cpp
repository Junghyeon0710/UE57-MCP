// Copyright 2026 Junghyeon0710. SPDX-License-Identifier: Apache-2.0

#include "UE57MCPNativeLibrary.h"
#include "AssetToolsModule.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/PanelSlot.h"
#include "Components/PanelWidget.h"
#include "Dom/JsonObject.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraphSchema_K2.h"
#include "Engine/Blueprint.h"
#include "WidgetBlueprintFactory.h"
#include "K2Node_CallFunction.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/CompilerResultsLog.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Logging/TokenizedMessage.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "WidgetBlueprint.h"

namespace
{
    using FJson = TSharedPtr<FJsonObject>;

    FString Text(const FJson& Value, const TCHAR* Key)
    {
        FString Result;
        Value->TryGetStringField(Key, Result);
        return Result;
    }

    FString Encode(const FJson& Value)
    {
        FString Output;
        FJsonSerializer::Serialize(Value.ToSharedRef(), TJsonWriterFactory<>::Create(&Output));
        return Output;
    }

    FJson Failure(const FString& Message)
    {
        FJson Result = MakeShared<FJsonObject>();
        Result->SetBoolField(TEXT("ok"), false);
        Result->SetStringField(TEXT("error"), Message);
        return Result;
    }

    FJson Reference(UObject* Object)
    {
        FJson Result = MakeShared<FJsonObject>();
        if (Object)
        {
            Result->SetStringField(TEXT("$ref"), Object->GetPathName());
            Result->SetStringField(TEXT("$type"), Object->GetClass()->GetName());
        }
        return Result;
    }

    FJson Success()
    {
        FJson Result = MakeShared<FJsonObject>();
        Result->SetBoolField(TEXT("ok"), true);
        return Result;
    }

    UEdGraph* FindGraph(UBlueprint* Blueprint, const FString& Name)
    {
        TArray<UEdGraph*> Graphs;
        Blueprint->GetAllGraphs(Graphs);
        for (UEdGraph* Graph : Graphs)
        {
            if (Graph && Graph->GetName() == Name) { return Graph; }
        }
        return nullptr;
    }

    UEdGraphNode* FindNode(UEdGraph* Graph, const FString& Name)
    {
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            if (Node && (Node->GetName() == Name || Node->NodeGuid.ToString() == Name)) { return Node; }
        }
        return nullptr;
    }

    FJson GraphOperation(const FString& Operation, const FJson& Args)
    {
        UBlueprint* Blueprint = LoadObject<UBlueprint>(nullptr, *Text(Args, TEXT("asset")));
        if (!Blueprint) { return Failure(TEXT("Blueprint asset was not found")); }
        if (Operation == TEXT("blueprint.compile"))
        {
            FCompilerResultsLog Log;
            FKismetEditorUtilities::CompileBlueprint(Blueprint, EBlueprintCompileOptions::None, &Log);
            FJson Result = Success();
            Result->SetBoolField(TEXT("ok"), Log.NumErrors == 0);
            Result->SetBoolField(TEXT("compiled"), Log.NumErrors == 0);
            Result->SetNumberField(TEXT("error_count"), Log.NumErrors);
            Result->SetNumberField(TEXT("warning_count"), Log.NumWarnings);
            FString Diagnostics;
            for (const TSharedRef<FTokenizedMessage>& Message : Log.Messages)
            {
                Diagnostics += Message->ToText().ToString() + TEXT("\n");
            }
            Result->SetStringField(TEXT("diagnostics"), Diagnostics);
            if (Log.NumErrors) { Result->SetStringField(TEXT("error"), TEXT("Blueprint compilation failed: ") + Diagnostics); }
            return Result;
        }
        UEdGraph* Graph = FindGraph(Blueprint, Text(Args, TEXT("graph")));
        if (!Graph) { return Failure(TEXT("Graph was not found; use its actual object name")); }
        if (Operation == TEXT("blueprint.graph"))
        {
            TArray<TSharedPtr<FJsonValue>> Nodes;
            for (UEdGraphNode* Node : Graph->Nodes)
            {
                if (!Node) { continue; }
                FJson Data = Reference(Node);
                Data->SetStringField(TEXT("name"), Node->GetName());
                Data->SetStringField(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
                Data->SetStringField(TEXT("guid"), Node->NodeGuid.ToString());
                Data->SetNumberField(TEXT("x"), Node->NodePosX);
                Data->SetNumberField(TEXT("y"), Node->NodePosY);
                TArray<TSharedPtr<FJsonValue>> Pins;
                for (UEdGraphPin* Pin : Node->Pins)
                {
                    if (!Pin) { continue; }
                    FJson Item = MakeShared<FJsonObject>();
                    Item->SetStringField(TEXT("name"), Pin->PinName.ToString());
                    Item->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
                    Item->SetStringField(TEXT("category"), Pin->PinType.PinCategory.ToString());
                    Item->SetStringField(TEXT("default"), Pin->DefaultValue);
                    TArray<TSharedPtr<FJsonValue>> Links;
                    for (UEdGraphPin* Linked : Pin->LinkedTo)
                    {
                        FJson Link = MakeShared<FJsonObject>();
                        Link->SetStringField(TEXT("node"), Linked->GetOwningNode()->GetName());
                        Link->SetStringField(TEXT("pin"), Linked->PinName.ToString());
                        Links.Add(MakeShared<FJsonValueObject>(Link));
                    }
                    Item->SetArrayField(TEXT("links"), Links);
                    Pins.Add(MakeShared<FJsonValueObject>(Item));
                }
                Data->SetArrayField(TEXT("pins"), Pins);
                Nodes.Add(MakeShared<FJsonValueObject>(Data));
            }
            FJson Result = Success();
            Result->SetArrayField(TEXT("nodes"), Nodes);
            return Result;
        }

        const FScopedTransaction Transaction(NSLOCTEXT("UE57MCP", "GraphEdit", "UE57 MCP graph edit"));
        Blueprint->Modify(); Graph->Modify();
        if (Operation == TEXT("blueprint.add_call"))
        {
            UFunction* Function = FindObject<UFunction>(nullptr, *Text(Args, TEXT("function")));
            if (!Function)
            {
                const FString Path = Text(Args, TEXT("function"));
                int32 Separator = INDEX_NONE;
                if (!Path.FindLastChar(TEXT(':'), Separator)) { Path.FindLastChar(TEXT('.'), Separator); }
                if (Separator != INDEX_NONE)
                {
                    UClass* Owner = LoadObject<UClass>(nullptr, *Path.Left(Separator));
                    if (Owner) { Function = Owner->FindFunctionByName(FName(*Path.Mid(Separator + 1))); }
                }
            }
            if (!Function) { return Failure(TEXT("Reflected function path was not found")); }
            if (!Function->HasAnyFunctionFlags(FUNC_BlueprintCallable | FUNC_BlueprintPure)) { return Failure(TEXT("Function is not callable from a Blueprint graph")); }
            UK2Node_CallFunction* Node = NewObject<UK2Node_CallFunction>(Graph, NAME_None, RF_Transactional);
            Node->SetFromFunction(Function);
            Node->CreateNewGuid();
            double X = 0; double Y = 0;
            Args->TryGetNumberField(TEXT("x"), X); Args->TryGetNumberField(TEXT("y"), Y);
            Node->NodePosX = static_cast<int32>(X);
            Node->NodePosY = static_cast<int32>(Y);
            Graph->AddNode(Node, true, false);
            Node->PostPlacedNewNode(); Node->AllocateDefaultPins();
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            FJson Result = Success();
            Result->SetObjectField(TEXT("node"), Reference(Node));
            Result->SetStringField(TEXT("name"), Node->GetName());
            return Result;
        }
        if (Operation == TEXT("blueprint.connect"))
        {
            UEdGraphNode* Source = FindNode(Graph, Text(Args, TEXT("source_node")));
            UEdGraphNode* Target = FindNode(Graph, Text(Args, TEXT("target_node")));
            UEdGraphPin* From = Source ? Source->FindPin(FName(*Text(Args, TEXT("source_pin"))), EGPD_Output) : nullptr;
            UEdGraphPin* To = Target ? Target->FindPin(FName(*Text(Args, TEXT("target_pin"))), EGPD_Input) : nullptr;
            if (!From || !To) { return Failure(TEXT("Source output or target input pin was not found")); }
            Source->Modify(); Target->Modify();
            if (!Graph->GetSchema()->TryCreateConnection(From, To)) { return Failure(TEXT("Schema rejected the pin connection")); }
            FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
            return Success();
        }
        if (Operation == TEXT("blueprint.pin_default"))
        {
            UEdGraphNode* Node = FindNode(Graph, Text(Args, TEXT("node")));
            UEdGraphPin* Pin = Node ? Node->FindPin(FName(*Text(Args, TEXT("pin"))), EGPD_Input) : nullptr;
            if (!Pin) { return Failure(TEXT("Input pin was not found")); }
            const FString Value = Text(Args, TEXT("value"));
            const FString Error = Graph->GetSchema()->IsPinDefaultValid(Pin, Value, Pin->DefaultObject, Pin->DefaultTextValue);
            if (!Error.IsEmpty()) { return Failure(Error); }
            Node->Modify();
            Graph->GetSchema()->TrySetDefaultValue(*Pin, Value);
            FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
            return Success();
        }
        return Failure(TEXT("Unknown Blueprint operation"));
    }

    FJson WidgetOperation(const FString& Operation, const FJson& Args)
    {
        if (Operation == TEXT("widget.create"))
        {
            const FString Package = Text(Args, TEXT("package_path")) + TEXT("/") + Text(Args, TEXT("name"));
            if (!FPackageName::IsValidLongPackageName(Package) || FindPackage(nullptr, *Package) || FPackageName::DoesPackageExist(Package))
            {
                return Failure(TEXT("Asset path is invalid or already exists"));
            }
            UWidgetBlueprintFactory* Factory = NewObject<UWidgetBlueprintFactory>();
            Factory->ParentClass = UUserWidget::StaticClass();
            IAssetTools& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get();
            UObject* Asset = Tools.CreateAsset(Text(Args, TEXT("name")), Text(Args, TEXT("package_path")), UWidgetBlueprint::StaticClass(), Factory);
            if (!Asset) { return Failure(TEXT("Widget Blueprint creation failed")); }
            FJson Result = Success(); Result->SetObjectField(TEXT("asset"), Reference(Asset)); return Result;
        }
        UWidgetBlueprint* Blueprint = LoadObject<UWidgetBlueprint>(nullptr, *Text(Args, TEXT("asset")));
        if (!Blueprint || !Blueprint->WidgetTree) { return Failure(TEXT("Widget Blueprint or tree was not found")); }
        UWidgetTree* Tree = Blueprint->WidgetTree;
        if (Operation == TEXT("widget.tree"))
        {
            TArray<UWidget*> Widgets; Tree->GetAllWidgets(Widgets);
            TArray<TSharedPtr<FJsonValue>> Items;
            for (UWidget* Widget : Widgets)
            {
                FJson Item = Reference(Widget); Item->SetStringField(TEXT("name"), Widget->GetName());
                Item->SetStringField(TEXT("parent"), Widget->GetParent() ? Widget->GetParent()->GetName() : TEXT(""));
                if (Widget->Slot) { Item->SetObjectField(TEXT("slot"), Reference(Widget->Slot)); }
                Items.Add(MakeShared<FJsonValueObject>(Item));
            }
            FJson Result = Success(); Result->SetArrayField(TEXT("widgets"), Items);
            Result->SetObjectField(TEXT("root"), Reference(Tree->RootWidget)); return Result;
        }
        const FScopedTransaction Transaction(NSLOCTEXT("UE57MCP", "WidgetEdit", "UE57 MCP widget edit"));
        Blueprint->Modify(); Tree->Modify();
        const FName Name(*Text(Args, TEXT("name")));
        FText NameError;
        if (!FName::IsValidXName(Name, INVALID_OBJECTNAME_CHARACTERS, &NameError)) { return Failure(NameError.ToString()); }
        UWidget* Widget = Tree->FindWidget(Name);
        if (Operation == TEXT("widget.add"))
        {
            if (Widget || Name.IsNone() || FindObjectFast<UObject>(Tree, Name)) { return Failure(TEXT("Widget name is empty or already exists")); }
            UClass* Class = FindFirstObject<UClass>(*Text(Args, TEXT("class")), EFindFirstObjectOptions::ExactClass);
            if (!Class || !Class->IsChildOf(UWidget::StaticClass()) || Class->HasAnyClassFlags(CLASS_Abstract)) { return Failure(TEXT("Concrete widget class was not found")); }
            const FString ParentName = Text(Args, TEXT("parent"));
            UPanelWidget* Parent = ParentName.IsEmpty() ? nullptr : Cast<UPanelWidget>(Tree->FindWidget(FName(*ParentName)));
            if (ParentName.IsEmpty() && Tree->RootWidget) { return Failure(TEXT("The tree already has a root widget; choose a parent panel")); }
            if (!ParentName.IsEmpty() && !Parent) { return Failure(TEXT("Parent panel was not found")); }
            Widget = Tree->ConstructWidget<UWidget>(Class, Name);
            if (Parent) { Parent->Modify(); if (!Parent->AddChild(Widget)) { Tree->RemoveWidget(Widget); return Failure(TEXT("Panel rejected the child widget")); } }
            else { Tree->RootWidget = Widget; }
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            FJson Result = Success(); Result->SetObjectField(TEXT("widget"), Reference(Widget));
            if (Widget->Slot) { Result->SetObjectField(TEXT("slot"), Reference(Widget->Slot)); }
            return Result;
        }
        if (!Widget) { return Failure(TEXT("Widget was not found")); }
        Widget->Modify();
        if (Operation == TEXT("widget.remove"))
        {
            if (!Tree->RemoveWidget(Widget)) { return Failure(TEXT("Widget removal failed")); }
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint); return Success();
        }
        if (Operation == TEXT("widget.move"))
        {
            UPanelWidget* Parent = Cast<UPanelWidget>(Tree->FindWidget(FName(*Text(Args, TEXT("parent")))));
            if (!Parent || Parent == Widget) { return Failure(TEXT("Target panel is invalid")); }
            for (UPanelWidget* Ancestor = Parent; Ancestor; Ancestor = Ancestor->GetParent())
            {
                if (Ancestor == Widget) { return Failure(TEXT("Moving the widget would create a cycle")); }
            }
            if (Tree->RootWidget == Widget) { return Failure(TEXT("The root cannot be moved under its own tree")); }
            UPanelWidget* Previous = Widget->GetParent();
            if (Previous) { Previous->Modify(); }
            Parent->Modify();
            if (!Parent->AddChild(Widget)) { return Failure(TEXT("Target panel rejected the child")); }
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            return Success();
        }
        return Failure(TEXT("Unknown widget operation"));
    }
}

FString UUE57MCPNativeLibrary::Execute(const FString& Operation, const FString& ArgumentsJson)
{
    if (!IsInGameThread()) { return Encode(Failure(TEXT("Editor operations must run on the main thread"))); }
    FJson Args;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ArgumentsJson), Args) || !Args)
    {
        return Encode(Failure(TEXT("Arguments must be a JSON object")));
    }
    if (Operation.StartsWith(TEXT("blueprint."))) { return Encode(GraphOperation(Operation, Args)); }
    if (Operation.StartsWith(TEXT("widget."))) { return Encode(WidgetOperation(Operation, Args)); }
    return Encode(Failure(TEXT("Unknown native operation")));
}
