<script lang="ts">
 let {service}:{service:string}=$props();
 const marks:Record<string,string>={
  docs:'google-docs.png',slides:'google-slides.png',naver:'naver-blog.png',
  notion:'notion.ico',medium:'medium.ico',codex:'openai-codex.ico',claude:'claude.ico',arise:'arise.png'
 };
 const source=$derived(marks[service]);
</script>

{#if source}<img class="service-logo" src={'/brands/'+source} alt="" aria-hidden="true" width="28" height="28" decoding="async"/>{/if}

<style>
 .service-logo{display:inline-block;flex:none;width:28px;height:28px;object-fit:contain;vertical-align:middle}
</style>
