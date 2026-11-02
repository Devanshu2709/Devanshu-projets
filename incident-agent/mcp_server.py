"""Minimal local stdio MCP server: search runbooks and investigate dummy incidents."""
import json
import os
import sys
from agent import SCENARIOS, investigate
from rag import retrieve

TOOLS=[
 {'name':'search_runbooks','description':'Search local incident runbooks. No cloud access.','inputSchema':{'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False}},
 {'name':'investigate_dummy_incident','description':'Investigate a built-in simulated incident and save a local report. No cloud changes or messaging.','inputSchema':{'type':'object','properties':{'scenario':{'type':'string','enum':list(SCENARIOS)}},'required':['scenario'],'additionalProperties':False}},
]

def handle(message, state):
    if not isinstance(message,dict) or message.get('jsonrpc')!='2.0':return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Invalid request'}}
    method=message.get('method'); request_id=message.get('id')
    params=message.get('params',{})
    def response(value):return {'jsonrpc':'2.0','id':request_id,'result':value}
    def error(code,text):return {'jsonrpc':'2.0','id':request_id,'error':{'code':code,'message':text}}
    if method=='notifications/initialized':
        if state.get('initialized'):state['ready']=True
        return None
    if 'id' not in message:return None
    if not isinstance(params,dict):return error(-32602,'Invalid params')
    if method=='initialize':
        state['initialized']=True
        return response({'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'sentinelflow-ai','version':'0.2.0'}})
    if method=='ping':return response({})
    if not state.get('ready'):return error(-32000,'Initialize first')
    if method=='tools/list':return response({'tools':TOOLS})
    if method!='tools/call':return error(-32601,'Method not found')
    name=params.get('name');args=params.get('arguments',{})
    if not isinstance(args,dict):return error(-32602,'Invalid arguments')
    try:
        if name=='search_runbooks':
            if set(args)!={'query'}:return error(-32602,'Provide query only')
            value=retrieve(args['query'])
        elif name=='investigate_dummy_incident':
            if set(args)!={'scenario'} or args['scenario'] not in SCENARIOS:return error(-32602,'Invalid scenario')
            value,path=investigate(args['scenario'],model=os.getenv('OLLAMA_MODEL'))
            value['report_path']=str(path/'report.html')
        else:return error(-32602,'Unknown tool')
        return response({'content':[{'type':'text','text':json.dumps(value)}],'isError':False})
    except Exception:
        return response({'content':[{'type':'text','text':'Tool failed; check local configuration.'}],'isError':True})

def main():
    state={}
    for line in sys.stdin:
        try:result=handle(json.loads(line),state)
        except (ValueError,TypeError):result={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}
        if result is not None:print(json.dumps(result),flush=True)

if __name__=='__main__':main()
