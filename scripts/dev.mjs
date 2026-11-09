#!/usr/bin/env node
import {randomBytes} from 'node:crypto';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const envPath=resolve(root,'.env');
if(!existsSync(envPath))writeFileSync(envPath,'DMEM_TOKEN='+randomBytes(24).toString('hex')+'\nDMEM_ADDR=127.0.0.1:3847\nDMEM_DATABASE=data/dmem.sqlite3\n',{mode:0o600,flag:'wx'});
const config={};
for(const line of readFileSync(envPath,'utf8').split(/\r?\n/)){const match=line.match(/^([A-Z][A-Z0-9_]*)=(.*)$/);if(match)config[match[1]]=match[2];}
const env={...process.env,...config};
// Explicit environment settings take precedence over the file.
for(const name of Object.keys(config))if(process.env[name]!==undefined)env[name]=process.env[name];
if(!env.DMEM_TOKEN||env.DMEM_TOKEN.length<16)throw new Error('DMEM_TOKEN must be at least 16 characters.');
function required(command,args,cwd=root){
 const result=spawnSync(command,args,{cwd,env,stdio:'inherit'});if(result.status!==0)process.exit(result.status??1);
}
if(!existsSync(resolve(root,'web/node_modules')))required('pnpm',['install','--frozen-lockfile'],resolve(root,'web'));
required('cargo',['build','-p','dmem-server']);
const children=[];let stopping=false;
function stop(code=0){
 if(stopping)return;stopping=true;
 for(const child of children)try{process.kill(-child.pid,'SIGTERM');}catch{}
 process.exitCode=code;
}
function start(command,args,cwd=root){
 const child=spawn(command,args,{cwd,env,stdio:'inherit',detached:true});children.push(child);
 child.on('error',()=>stop(1));child.on('exit',code=>{if(!stopping)stop(code??1);});return child;
}
const server=start(resolve(root,'target/debug/dmem-server'),[]);
const web=start('pnpm',['dev'],resolve(root,'web'));
console.log('My Document Memory: http://127.0.0.1:5174');
console.log('Connection token: DMEM_TOKEN in .env (never written to logs).');
console.log('Owned processes: server '+server.pid+', web '+web.pid);
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
