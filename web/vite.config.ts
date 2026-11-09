import {defineConfig,loadEnv} from 'vite';
import {svelte} from '@sveltejs/vite-plugin-svelte';
export default defineConfig(({mode})=>{
 const env=loadEnv(mode,'..','DMEM_');
 const target=env.DMEM_API_TARGET||'http://'+(env.DMEM_ADDR||'127.0.0.1:3847');
 return {plugins:[svelte()],server:{proxy:{'/v1':target,'/healthz':target}},preview:{proxy:{'/v1':target,'/healthz':target}}};
});
