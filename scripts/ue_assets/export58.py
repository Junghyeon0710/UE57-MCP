"""원본 에셋은 저장하지 않고 5.7 재생성에 필요한 데이터만 추출한다."""
import json, traceback, os
from pathlib import Path
import unreal
root=Path(os.environ['UE57_MCP_ASSET_WORK'])
report={'skills':[]}
try:
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(['/PCGToolset/'],force_rescan=True)
    for data in registry.get_assets_by_path('/PCGToolset',recursive=True):
        if not str(data.asset_name).startswith('Skill_'): continue
        path=str(data.package_name)
        cls=unreal.load_class(None,path+'.'+str(data.asset_name)+'_C')
        if cls:
            cdo=unreal.get_default_object(cls)
            report['skills'].append({'name':str(data.asset_name),'path':path,'description':cdo.get_editor_property('description'),'instructions':cdo.get_editor_property('instructions')})
    def call(name,args):
        result=unreal.ToolsetRegistry.execute_tool('DataflowAgent.DataflowAgentToolset',name,json.dumps(args))
        if result.get_editor_property('error'): raise RuntimeError(result.get_editor_property('error'))
        value=json.loads(result.get_editor_property('value'))
        if isinstance(value,dict) and 'returnValue' in value:value=value['returnValue']
        return json.loads(value) if isinstance(value,str) and value.startswith(('{','[')) else value
    path='/ChaosClothAsset/DF_LegacyClothingAssetTemplate.DF_LegacyClothingAssetTemplate'
    graph=unreal.load_asset(path)
    report['cloth_graph']=call('GetGraphStructure',{'graph':{'refPath':path}})
    report['cloth_variables']=call('ListVariables',{'graph':{'refPath':path}})
    for node in report['cloth_graph']['nodes']:
        node['details']=call('GetNodeInfo',{'node':{'refPath':path+':'+node['name']}})
except Exception:
    report['error']=traceback.format_exc()
(root/'source58-export.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')

if report.get("error"): raise RuntimeError(report["error"])
