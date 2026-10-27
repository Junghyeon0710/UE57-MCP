"""5.8에서 추출한 Skill 지침을 5.7 플러그인 에셋으로 생성하고 저장한다."""
import unreal,json,os
from pathlib import Path
root=Path(os.environ['UE57_MCP_ASSET_WORK']).resolve()
assert Path(unreal.Paths.get_project_file_path()).resolve()==root/'host57/UE57MCPHost.uproject'
source=json.loads((root/'source58-export.json').read_text(encoding='utf-8'))
# 명령릿 초기 검색이 끝나기 전에도 기존 플러그인 에셋을 정확히 찾는다.
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(['/PCGToolset/','/ChaosClothAssetToolset/'],force_rescan=True)
saved=[]
for skill in source['skills']:
    path=skill['path'];name=skill['name']
    assert path.startswith('/PCGToolset/Skills/')
    exists=unreal.EditorAssetLibrary.does_asset_exist(path)
    args=({'skillPath':path+'.'+name+'_C'} if exists else {'folderPath':path.rsplit('/',1)[0],'assetName':name})
    args.update(description=skill['description'],details={'instructions':skill['instructions']})
    result=unreal.ToolsetRegistry.execute_tool('ToolsetRegistry.AgentSkillToolset','UpdateSkill' if exists else 'CreateSkill',json.dumps(args))
    assert not result.error,result.error
    assert json.loads(result.value)['returnValue']
    assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False),path
    saved.append(path)
(root/'pcg-skills-saved.json').write_text(json.dumps({'saved':saved,'count':len(saved)},indent=2),encoding='utf-8')

"""5.8에서 추출한 변환 템플릿을 5.7 Dataflow 노드로 다시 만든다."""
import unreal,json,traceback
from pathlib import Path
root=Path(os.environ['UE57_MCP_ASSET_WORK']).resolve()
assert Path(unreal.Paths.get_project_file_path()).resolve()==root/'host57/UE57MCPHost.uproject'
source=json.loads((root/'source58-export.json').read_text(encoding='utf-8'))
report={'nodes':{},'property_differences':{},'connections':0}
group='DataflowAgent.DataflowAgentToolset'
def call(tool,**args):
    r=unreal.ToolsetRegistry.execute_tool(group,tool,json.dumps(args))
    if r.error:raise RuntimeError(r.error)
    v=json.loads(r.value).get('returnValue')
    return json.loads(v) if isinstance(v,str) and v.startswith(('{','[')) else v
try:
    existing_path='/ChaosClothAssetToolset/DF_LegacyClothingAssetTemplate.DF_LegacyClothingAssetTemplate'
    if unreal.EditorAssetLibrary.does_asset_exist(existing_path):
        graph=call('GetGraphStructure',graph={'refPath':existing_path})
        expected={n['name'] for n in source['cloth_graph']['nodes'] if n['name']!='StripUserAttributes'}
        assert {n['name'] for n in graph['nodes']}==expected, 'Existing template nodes differ'
        assert len(graph['connections'])==36, 'Existing template connections differ'
        report['nodes']={n['name']:n for n in graph['nodes']}
        report['connections']=len(graph['connections'])
    else:
        path=call('CreateGraph',name='DF_LegacyClothingAssetTemplate',path='/ChaosClothAssetToolset')
        graph={'refPath':path}
        for var in source['cloth_variables']:
            type_name=var['valueTypeName'] if var['type']=='Struct' else 'Object:'+var['valueTypeName']
            assert call('AddVariable',graph=graph,name=var['name'],type=type_name)
        for node in source['cloth_graph']['nodes']:
            # 5.8의 저장 크기 최적화 노드는 5.7의 기본 보존 동작을 유지하도록 우회한다.
            if node['name']=='StripUserAttributes':continue
            ref=call('AddNode',graph=graph,typeName=node['type'],nodeName=node['name'],jsonParams='',x=node['posX'],y=node['posY'])
            assert ref,node['name']
            obj=unreal.load_object(None,ref['refPath'])
            differences=unreal.MCP57DataflowImportLibrary.import_node_properties(obj,json.dumps(node['details']['properties']))
            if differences:report['property_differences'][node['name']]=list(differences)
            report['nodes'][node['name']]=ref
        connections=source['cloth_graph']['connections']
        upstream=next(c for c in connections if c['toNode']=='StripUserAttributes')
        for c in connections:
            if c['toNode']=='StripUserAttributes':continue
            from_name=c['fromNode'];from_pin=c['fromPin']
            if from_name=='StripUserAttributes':from_name=upstream['fromNode'];from_pin=upstream['fromPin']
            assert call('ConnectNodePins',fromNode=report['nodes'][from_name],fromPin=from_pin,toNode=report['nodes'][c['toNode']],toPin=c['toPin']),c
            report['connections']+=1
        assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False)
        report['path']=path
        report['graph']=call('GetGraphStructure',graph=graph)
except Exception:report['error']=traceback.format_exc()
(root/'cloth-template-57.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

if report.get("error"): raise RuntimeError(report["error"])
(root/'assets57-report.json').write_text(json.dumps({'skill_count':len(saved),'cloth_node_count':len(report['nodes']),'cloth_connections':report['connections'],'property_differences':report['property_differences']},indent=2),encoding='utf-8')
