using UnrealBuildTool;

public class UE57MCPNative : ModuleRules
{
    public UE57MCPNative(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] {
            "UnrealEd", "KismetCompiler", "BlueprintGraph", "Kismet", "UMG", "UMGEditor",
            "SlateCore", "Json", "AssetTools", "AssetRegistry"
        });
    }
}
