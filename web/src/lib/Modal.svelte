<script lang="ts">
 import {onMount,type Snippet} from 'svelte';
 let {title,onclose,children,error=''}:{title:string;onclose:()=>void;children:Snippet;error?:string}=$props();
 let dialog:HTMLDialogElement;
 onMount(()=>{dialog.showModal();});
</script>
<dialog bind:this={dialog} onclose={onclose} aria-label={title}>
 <header class="modal-heading"><h2>{title}</h2><button class="icon-button" aria-label="Close" onclick={()=>dialog.close()}>✕</button></header>
 {#if error}<div class="alert" role="alert">{error}</div>{/if}
 {@render children()}
</dialog>
