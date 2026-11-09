<script lang="ts">
 let {kind}:{kind:'report'|'deck'|'worklog'}=$props();
 const boxes={report:'0 0 1000 1320',deck:'0 0 1200 900',worklog:'0 0 1000 1320'};
 const labels={
  report:'Weekly product report with a summary, progress metrics and next steps',
  deck:'Project kickoff presentation with a cover, customer problem and delivery plan',
  worklog:'Team worklog with completed work, decisions and upcoming tasks'
 };
</script>

<svg viewBox={boxes[kind]} role="img" aria-label={labels[kind]} xmlns="http://www.w3.org/2000/svg">
 <use href={'/examples/document-examples.svg#'+kind+'-art'} width="100%" height="100%"/>
</svg>

<style>
 svg{display:block;width:100%;height:auto}
</style>
