// static/script.js — BUITEMS Copilot interface logic

// ---------- custom cursor ----------
const cur = document.getElementById('cur'), ring = document.getElementById('ring');
let rx=0, ry=0, mx=0, my=0;
addEventListener('mousemove', e => { mx=e.clientX; my=e.clientY; cur.style.left=mx+'px'; cur.style.top=my+'px'; });
(function loop(){ rx+=(mx-rx)*.2; ry+=(my-ry)*.2; ring.style.left=rx+'px'; ring.style.top=ry+'px'; requestAnimationFrame(loop); })();
function bindHover(el){
  el.addEventListener('mouseenter', ()=>{ ring.style.width='44px'; ring.style.height='44px'; ring.style.borderColor='rgba(43,108,163,.8)'; cur.style.background='#13344e'; });
  el.addEventListener('mouseleave', ()=>{ ring.style.width='32px'; ring.style.height='32px'; ring.style.borderColor='rgba(43,108,163,.4)'; cur.style.background='#2b6ca3'; });
}
document.querySelectorAll('a,button,span,input,.f').forEach(bindHover);

// ---------- scroll reveal ----------
const io = new IntersectionObserver(es => es.forEach((e,i)=>{ if(e.isIntersecting){ setTimeout(()=>e.target.classList.add('in'), i*90); io.unobserve(e.target);} }), {threshold:.18});
document.querySelectorAll('.f,.team').forEach(x=>io.observe(x));

// ---------- tiny markdown -> html (tables, bold, headings, images) ----------
function mdToHtml(md){
  let lines = md.split('\n');
  let html = '', inTable = false;
  for(let i=0;i<lines.length;i++){
    let line = lines[i];
    // image: ![alt](url)
    let img = line.match(/!\[.*?\]\((.*?)\)/);
    if(img){ html += `<img src="${img[1]}" alt="">`; continue; }
    // table row
    if(/^\s*\|/.test(line)){
      let cells = line.split('|').slice(1,-1).map(c=>c.trim());
      // separator row like |---|---|
      if(cells.every(c=>/^-+$/.test(c))) continue;
      if(!inTable){ html += '<table>'; inTable = true;
        html += '<tr>' + cells.map(c=>`<th>${inline(c)}</th>`).join('') + '</tr>';
      } else {
        html += '<tr>' + cells.map(c=>`<td>${inline(c)}</td>`).join('') + '</tr>';
      }
      continue;
    } else if(inTable){ html += '</table>'; inTable = false; }
    // headings ## or ###
    if(/^#{1,3}\s/.test(line)){ html += `<h3>${inline(line.replace(/^#+\s/,''))}</h3>`; continue; }
    if(line.trim()===''){ html += '<br>'; continue; }
    html += `<div>${inline(line)}</div>`;
  }
  if(inTable) html += '</table>';
  return html;
}
function inline(s){
  return s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
          .replace(/_(.+?)_/g,'<em>$1</em>');
}

// ---------- chat ----------
const stream = document.getElementById('stream');
const inp = document.getElementById('inp');

function addQ(text){
  const b = document.createElement('div');
  b.className = 'bubble q';
  b.textContent = text;
  stream.appendChild(b);
  stream.scrollTop = stream.scrollHeight;
}
function addTyping(){
  const w = document.createElement('div');
  w.className = 'bubble a';
  w.innerHTML = '<div class="typing"><i></i><i></i><i></i></div>';
  stream.appendChild(w);
  stream.scrollTop = stream.scrollHeight;
  return w;
}

async function ask(text){
  if(!text || !text.trim()) return;
  addQ(text);
  const typing = addTyping();
  try{
    const res = await fetch('/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    typing.innerHTML = mdToHtml(data.reply || 'Sorry, something went wrong.');
  }catch(err){
    typing.innerHTML = 'Connection error. Please try again.';
  }
  stream.scrollTop = stream.scrollHeight;
}

// send button + enter key
document.getElementById('send').addEventListener('click', ()=>{ ask(inp.value); inp.value=''; });
inp.addEventListener('keydown', e=>{ if(e.key==='Enter'){ ask(inp.value); inp.value=''; } });

// nav links + suggestion chips (data-q)
document.querySelectorAll('[data-q]').forEach(el=>{
  el.addEventListener('click', e=>{ e.preventDefault(); ask(el.getAttribute('data-q')); });
});

// friendly opening message
window.addEventListener('load', ()=>{
  setTimeout(()=>{
    const w = document.createElement('div');
    w.className = 'bubble a';
    w.innerHTML = mdToHtml("**Welcome.** Ask me about your results, CGPA, fees, attendance or schedule — in English or Roman Urdu. Try one of the suggestions below.");
    stream.appendChild(w);
  }, 500);
});