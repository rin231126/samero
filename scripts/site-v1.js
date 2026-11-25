'use strict';
const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
const film=$('#film');
function playFilm(){film.muted=false;film.play().catch(()=>{$('#video-status').textContent=document.body.dataset.videoError;});}
$('#watch').addEventListener('click',playFilm);
$('#play').addEventListener('click',playFilm);
film.addEventListener('error',()=>{$('#video-status').textContent=document.body.dataset.videoError;});
film.querySelector('source').addEventListener('error',()=>{$('#video-status').textContent=document.body.dataset.videoError;});
$('#mascot').addEventListener('click',()=>{const b=$('#mascot'),open=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(open));$('#mascot-img').src=open?'assets/open.png':'assets/normal.png';});
$$('.tab').forEach(b=>b.addEventListener('click',()=>{$$('.tab').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));const img=$('#demo-img');img.src=b.dataset.image;img.alt=b.dataset.caption;$('#demo-caption').textContent=b.dataset.caption;}));
function theme(k){document.body.dataset.theme=k;$$('.theme').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.theme===k)));}
$$('.theme').forEach(b=>b.addEventListener('click',()=>{theme(b.dataset.theme);try{localStorage.setItem('samero-site-theme',b.dataset.theme);}catch{}}));
try{const saved=localStorage.getItem('samero-site-theme');if($$('.theme').some(b=>b.dataset.theme===saved))theme(saved);}catch{}
$('#copy').addEventListener('click',async()=>{const h=$('#hash');try{await navigator.clipboard.writeText(h.textContent.trim());$('#copy-result').textContent=document.body.dataset.copySuccess;}catch{const r=document.createRange();r.selectNodeContents(h);const s=window.getSelection();s.removeAllRanges();s.addRange(r);$('#copy-result').textContent=document.body.dataset.copyFallback;}});
$$('.mobile a').forEach(a=>a.addEventListener('click',()=>$('.mobile').open=false));
