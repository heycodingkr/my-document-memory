import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./tests',outputDir:process.env.DMEM_E2E_OUTPUT_DIR||'test-results',fullyParallel:false,workers:1,retries:0,
 use:{baseURL:process.env.DMEM_E2E_URL||'http://127.0.0.1:43847',viewport:{width:1440,height:1100},trace:'retain-on-failure'},
 reporter:'list',timeout:30000
});
