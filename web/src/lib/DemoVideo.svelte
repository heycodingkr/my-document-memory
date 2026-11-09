<script lang="ts">
 import type {LandingLocale} from './landing-copy';
 let {locale='en'}:{locale?:LandingLocale}=$props();
 const copy={
  en:{kicker:'WATCH THE DEMO · 2 MIN',title:'One memory. Better documents.',description:'See reusable formats, shared writing guidance, and community contributions in action.',language:'English narration and on-screen captions.',player:'My Document Memory: two-minute English demo',download:'Download the demo video'},
  ko:{kicker:'2분 데모 영상',title:'하나의 메모리로, 더 나은 문서를.',description:'문서 양식과 작성 기준을 재사용하고, 공유와 기여로 이어지는 과정을 확인하세요.',language:'영어 내레이션과 영어 화면 자막이 포함되어 있습니다.',player:'My Document Memory 2분 영어 데모 영상',download:'데모 영상 다운로드'}
 };
 const t=$derived(copy[locale]);
</script>

<section id="product-demo" aria-labelledby="product-demo-title">
 <div class="demo-heading">
  <div><span class="demo-kicker">{t.kicker}</span><h2 id="product-demo-title">{t.title}</h2></div>
  <p>{t.description}</p>
 </div>
 <div class="player-frame">
  <video controls playsinline preload="none" width="1920" height="1080" poster="/media/mdm-demo-120s.en-poster.jpg" aria-label={t.player} aria-describedby="product-demo-language">
   <source src="/media/mdm-demo-120s.en.mp4" type="video/mp4"/>
   <track kind="captions" src="/media/mdm-demo-120s.en.vtt" srclang="en" label="English"/>
   <a href="/media/mdm-demo-120s.en.mp4">{t.download}</a>
  </video>
 </div>
 <p class="demo-language" id="product-demo-language">{t.language}</p>
</section>

<style>
 section{padding:18px 0 48px;scroll-margin-top:24px}
 .demo-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:28px;margin-bottom:24px}
 .demo-kicker{font-size:10px;letter-spacing:.12em;color:#6e845e}
 h2{font-size:34px;line-height:1.35;letter-spacing:-.045em;font-weight:500;margin:13px 0 0;color:#284c36}
 .demo-heading p{max-width:390px;font-size:13px;line-height:1.85;color:#64756b;margin:0}
 .player-frame{max-width:min(100%,calc((100svh - 220px) * 16 / 9));margin-inline:auto;border:1px solid #d5dfcc;border-radius:12px;overflow:hidden;background:#122c22;box-shadow:0 16px 44px #243c2f0d}
 video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#122c22}
 .demo-language{font-size:11px;line-height:1.8;color:#718168;margin:12px 0 0}
 @media(max-width:580px){section{padding:10px 0 30px}.demo-heading{display:block;margin-bottom:18px}h2{font-size:28px;margin:11px 0 13px}.demo-heading p{font-size:12px}.demo-language{font-size:10px}.player-frame{border-radius:8px}}
</style>
