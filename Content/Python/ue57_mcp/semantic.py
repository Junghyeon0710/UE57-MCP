"""사용자가 지정한 모델 API로 메타데이터를 색인하고 검색한다."""
import json
import math
import os
from pathlib import Path
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

def cosine(left,right):
    """차원이 같은 유효 벡터의 코사인 유사도를 계산한다."""
    if len(left)!=len(right):raise ValueError("Embedding dimensions differ; rebuild the index")
    denominator=math.sqrt(sum(x*x for x in left)*sum(x*x for x in right))
    return sum(x*y for x,y in zip(left,right))/denominator if denominator else 0.0

def valid_vector(vector):
    return isinstance(vector,list) and bool(vector) and all(isinstance(x,(int,float)) and math.isfinite(x) for x in vector)

class SearchIndex:
    """모델 요청을 별도 스레드에서 처리하며 색인과 작업 상태를 보관한다."""
    def __init__(self,directory):
        self.directory=Path(directory);self.lock=threading.RLock();self.jobs={}
        self.config=self.read("semantic-settings.json",{})
        self.index=self.read("semantic-index.json",{"entries":[],"model":None})
    def read(self,name,fallback):
        path=self.directory/name
        return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else fallback
    def write(self,name,value):
        self.directory.mkdir(parents=True,exist_ok=True)
        target=self.directory/name;temporary=target.with_name(target.name+".partial")
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        os.replace(temporary,target)
    def configure(self,embedding_url,embedding_model,dimensions=0,caption_url="",caption_model=""):
        for value in [embedding_url,caption_url]:
            if not value:continue
            parsed=urllib.parse.urlsplit(value)
            if parsed.scheme not in {"http","https"} or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError("Use an HTTP(S) model base URL without embedded credentials")
        if not embedding_model or not embedding_url:raise ValueError("Embedding URL and model are required")
        if dimensions<0:raise ValueError("Dimensions must be zero (model default) or positive")
        with self.lock:
            if any(job["state"]=="running" for job in self.jobs.values()):raise ValueError("Wait for the current model job before reconfiguring")
            self.config={"embedding_url":embedding_url.rstrip("/"),"embedding_model":embedding_model,"dimensions":dimensions,
                         "caption_url":caption_url.rstrip("/"),"caption_model":caption_model}
            self.write("semantic-settings.json",self.config)
        return {"configured":True,"reindex_required":bool(self.index["entries"])}
    def request(self,base,suffix,body,key_name):
        data=json.dumps(body).encode();headers={"Content-Type":"application/json"}
        key=os.environ.get(key_name)
        request=urllib.request.Request(base+suffix,data,headers)
        if key:request.add_unredirected_header("Authorization","Bearer "+key)
        try:
            with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
        except urllib.error.HTTPError as error:raise RuntimeError(f"Model API returned HTTP {error.code}") from None
        except urllib.error.URLError:raise RuntimeError("Model endpoint is unreachable") from None
    def embed(self,text,config):
        if not config.get("embedding_url"):raise ValueError("Configure an embedding endpoint before indexing/searching")
        body={"model":config["embedding_model"],"input":[text]}
        if config.get("dimensions"):body["dimensions"]=config["dimensions"]
        data=self.request(config["embedding_url"],"/embeddings",body,"UE57_MCP_EMBEDDING_KEY")
        vector=data["data"][0]["embedding"]
        if not valid_vector(vector):raise ValueError("Model returned an invalid embedding")
        if config.get("dimensions") and len(vector)!=config["dimensions"]:raise ValueError("Embedding dimension differs from configuration")
        return vector
    def describe(self,item,config):
        text=json.dumps(item,ensure_ascii=False)
        if not config.get("caption_url") or not config.get("caption_model"):return text
        response=self.request(config["caption_url"],"/chat/completions",{"model":config["caption_model"],"messages":[
            {"role":"system","content":"Describe this Unreal asset from its supplied metadata. Do not invent unseen visual details. Return a concise plain text description."},
            {"role":"user","content":text}]},"UE57_MCP_CAPTION_KEY")
        caption=response["choices"][0]["message"]["content"]
        if not isinstance(caption,str) or not caption.strip():raise ValueError("Captioning model returned no text")
        return text+"\n"+caption[:8000]
    def start_job(self,kind,function):
        with self.lock:
            if any(job["state"]=="running" for job in self.jobs.values()):raise ValueError("Another semantic job is running")
            if len(self.jobs)>=50:self.jobs.pop(next(iter(self.jobs)))
            identifier=uuid.uuid4().hex
            self.jobs[identifier]={"id":identifier,"kind":kind,"state":"running","completed":0,"started":time.time()}
        def run():
            try:
                result=function(identifier)
                with self.lock:self.jobs[identifier].update(state="completed",result=result)
            except Exception as error:
                with self.lock:self.jobs[identifier].update(state="failed",error=str(error))
        threading.Thread(target=run,name="UE57-MCP-model",daemon=True).start()
        return {"job_id":identifier,"state":"running"}
    def start_index(self,items):
        config=dict(self.config)
        if not config.get("embedding_url"):raise ValueError("Configure an embedding endpoint first")
        def run(identifier):
            entries=[];dimension=None
            for item in items:
                text=self.describe(item,config);vector=self.embed(text,config)
                if dimension is not None and len(vector)!=dimension:raise ValueError("Model changed embedding dimensions during indexing")
                dimension=len(vector)
                entries.append({**item,"text":text,"vector":vector})
                with self.lock:self.jobs[identifier]["completed"]=len(entries)
            value={"model":config["embedding_model"],"base_url":config["embedding_url"],"dimension":dimension,"entries":entries}
            with self.lock:self.write("semantic-index.json",value);self.index=value
            return {"indexed":len(entries),"dimension":dimension}
        return self.start_job("index",run)
    def ranked(self,vector,entries,top_k,exclude=None):
        if not 1<=top_k<=100:raise ValueError("top_k must be 1..100")
        scored=[{key:value for key,value in item.items() if key!="vector"}|{"score":cosine(vector,item["vector"])}
                for item in entries if item["path"]!=exclude]
        return sorted(scored,key=lambda item:item["score"],reverse=True)[:top_k]
    def search(self,query,top_k):
        config=dict(self.config)
        with self.lock:index=self.index
        if not index["entries"]:raise ValueError("The semantic index is empty")
        if index["model"]!=config.get("embedding_model") or index.get("base_url")!=config.get("embedding_url"):
            raise ValueError("Model settings changed; rebuild the semantic index")
        return self.start_job("search",lambda _:self.ranked(self.embed(query,config),index["entries"],top_k))
    def job_status(self,identifier):
        with self.lock:
            if identifier not in self.jobs:raise ValueError("Unknown semantic job")
            return dict(self.jobs[identifier])

def register_semantic(registry,runtime):
    """에셋 메타데이터 수집만 메인 스레드에서 실행하고 모델 작업은 비동기로 등록한다."""
    index=SearchIndex(runtime.saved);tool=registry.register
    @tool("ue57.semantic_search","Configure OpenAI-compatible model base URLs. API keys are read from local environment variables.")
    def configure(embedding_url:str,embedding_model:str,dimensions:int=0,caption_url:str="",caption_model:str=""):
        return index.configure(embedding_url,embedding_model,dimensions,caption_url,caption_model)
    @tool("ue57.semantic_search","Read index/model status without exposing credentials.",True)
    def status():
        with index.lock:return {"configured":bool(index.config.get("embedding_url")),"settings":dict(index.config),"indexed_assets":len(index.index["entries"]),"index_model":index.index["model"]}
    @tool("ue57.semantic_search","Start metadata-based semantic indexing. This sends the selected asset metadata to your configured model service.")
    def index_assets(root:str="/Game",max_assets:int=200):
        if not 1<=max_assets<=10000:raise ValueError("max_assets must be 1..10000")
        ue=runtime.ue;items=[]
        paths=ue.EditorAssetLibrary.list_assets(root,recursive=True,include_folder=False)[:max_assets]
        for path in paths:
            data=ue.EditorAssetLibrary.find_asset_data(path)
            items.append({"path":path,"name":str(data.asset_name),"class":str(data.asset_class_path)})
        return index.start_index(items)
    @tool("ue57.semantic_search","Start a semantic query; poll get_job for its result.",True)
    def search(query:str,top_k:int=10):return index.search(query,top_k)
    @tool("ue57.semantic_search","Read progress/results for an asynchronous semantic index or search job.",True)
    def get_job(job_id:str):return index.job_status(job_id)
    @tool("ue57.semantic_search","Find similar indexed assets using a stored vector; no model request is needed.",True)
    def find_similar(asset_path:str,top_k:int=10):
        with index.lock:entries=list(index.index["entries"])
        source=next((item for item in entries if item["path"]==asset_path),None)
        if source is None:raise ValueError("Asset is not indexed")
        return index.ranked(source["vector"],entries,top_k,asset_path)
    @tool("ue57.semantic_search","Remove the local semantic index. Existing asset files are not changed.")
    def clear_index():
        with index.lock:
            if any(job["state"]=="running" for job in index.jobs.values()):raise ValueError("A semantic job is running")
            value={"entries":[],"model":None};index.write("semantic-index.json",value);index.index=value
        return {"cleared":True}
