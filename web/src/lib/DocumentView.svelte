<script lang="ts">
 import type {Content} from './types';
 let {title,content}:{title:string;content:Content}=$props();
</script>
<article class="document-view">
 <h1>{title}</h1>
 {#each content.blocks as b}
  {#if b.type==='heading'}<h2>{b.text}</h2>
  {:else if b.type==='paragraph'}<p>{b.text}</p>
  {:else if b.type==='quote'}<blockquote>{b.text}{#if b.citation}<small>Source excerpt · {b.citation.span_id}</small>{/if}</blockquote>
  {:else if b.type==='list'}<ul>{#each b.items as item}<li>{item}</li>{/each}</ul>
  {:else if b.type==='table'}<table><tbody>{#each b.rows as row}<tr>{#each row as cell}<td>{cell}</td>{/each}</tr>{/each}</tbody></table>{/if}
 {/each}
 {#each content.slides as slide}<section class="print-slide"><h2>{slide.title}</h2><p>{slide.body}</p></section>{/each}
</article>
