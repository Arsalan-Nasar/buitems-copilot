// static/script.js — BUITEMS Copilot interface logic

const chatInner = document.getElementById('chatInner');
const chatArea  = document.getElementById('chat');
const inp = document.getElementById('inp');
const MK = "/static/markhor.png";

function clearWelcome(){ const w=document.getElementById('welcome'); if(w) w.remove(); }
function scrollDown(){ chatArea.scrollTop = chatArea.scrollHeight; }

// ----- user message -----
function userRow(text){
  clearWelcome();
  const r=document.createElement('div'); r.className='row user';
  r.innerHTML = `<div class="avatar user">You</div><div class="msg"><div class="bubble"></div></div>`;
  r.querySelector('.bubble').textContent = text;
  chatInner.appendChild(r); scrollDown();
}

// ----- bot typing placeholder -----
function botTyping(){
  const r=document.createElement('div'); r.className='row bot';
  r.innerHTML = `<div class="avatar bot"><img src="${MK}"></div><div class="msg"><div class="bubble"><div class="typing"><i></i><i></i><i></i></div></div></div>`;
  chatInner.appendChild(r); scrollDown();
  return r.querySelector('.bubble');
}

// ----- send a message to the engine -----
async function ask(text){
  if(!text || !text.trim()) return;
  userRow(text);
  const bubble = botTyping();
  try{
    const res = await fetch('/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    bubble.innerHTML = data.html || escapeHtml(data.reply || 'Sorry, something went wrong.');
    attachDownload(bubble);
  }catch(err){
    bubble.textContent = 'Connection error. Please try again.';
  }
  scrollDown();
}

function escapeHtml(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML.replace(/\n/g,'<br>'); }

// ----- PNG download (permanent fix: charts download directly, cards render branded) -----
function attachDownload(bubble){
  const btn = bubble.querySelector('.dl-png');
  if(!btn) return;
  btn.addEventListener('click', ()=>{
    const card = bubble.querySelector('.result-card');
    if(!card) return;

    // CASE 1 — result has a chart image: download the image directly (full quality, never cut)
    const chartImg = card.querySelector('img');
    if(chartImg){
      const link = document.createElement('a');
      link.download = 'buitems-gpa-trend.png';
      link.href = chartImg.src;
      link.click();
      return;
    }

    // CASE 2 — text result card: render a clean branded card to PNG
    if(typeof html2canvas==='undefined') return;
    const wrap = document.createElement('div');
    wrap.style.cssText = 'position:fixed;left:-9999px;top:0;width:460px;background:#fff;padding:22px;font-family:Georgia,serif;border-radius:14px;';
    wrap.innerHTML =
      '<div style="display:flex;align-items:center;gap:9px;padding-bottom:14px;border-bottom:2px solid #eef3f7;margin-bottom:14px;">' +
        '<img src="' + MK + '" style="width:34px;height:34px;border-radius:50%;background:#13344e;object-fit:cover;">' +
        '<div style="font-size:16px;font-weight:700;color:#13344e;">BUITEMS <span style="color:#2b6ca3;font-weight:400;">Copilot</span></div>' +
      '</div>' +
      card.outerHTML +
      '<div style="margin-top:16px;padding-top:12px;border-top:1px solid #eef3f7;text-align:center;font-size:10px;color:#8a9aa8;letter-spacing:1px;">via BUITEMS Copilot · by ZIRA Technologies</div>';
    const innerBtn = wrap.querySelector('.dl'); if(innerBtn) innerBtn.remove();
    document.body.appendChild(wrap);
    html2canvas(wrap, {scale:2, backgroundColor:'#ffffff', logging:false}).then(canvas=>{
      const link = document.createElement('a');
      link.download = 'buitems-copilot-result.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
      document.body.removeChild(wrap);
    });
  });
}

// ----- send button + enter -----
document.getElementById('send').addEventListener('click', ()=>{ ask(inp.value); inp.value=''; });
inp.addEventListener('keydown', e=>{ if(e.key==='Enter'){ ask(inp.value); inp.value=''; }});

// ----- quick chips (data-q) -----
document.querySelectorAll('[data-q]').forEach(el=>{
  el.addEventListener('click', e=>{ e.preventDefault(); ask(el.getAttribute('data-q')); });
});