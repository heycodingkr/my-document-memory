<script lang="ts">
 import {landingCopy,type LandingLocale} from './landing-copy';
 let {kind,locale='en'}:{kind:'report'|'deck'|'worklog';locale?:LandingLocale}=$props();
 const boxes={report:'0 0 1000 1320',deck:'0 0 1200 900',worklog:'0 0 1000 1320'};
 const label=$derived(landingCopy[locale].preview[kind]);
</script>

<svg viewBox={boxes[kind]} role="img" aria-label={label} xmlns="http://www.w3.org/2000/svg">
 <use href={'/examples/document-examples.svg#'+kind+'-art'} width="100%" height="100%"/>
</svg>

<style>
 svg{display:block;width:100%;height:auto}
</style>
