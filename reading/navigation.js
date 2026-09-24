(() => {
  'use strict';
  const config=JSON.parse(document.getElementById('reading-config').textContent);
  if(config.mode==='cover'){
    // Compatibility for existing /ko/#spaces, /#fig-prism, /#coda links.
    const forward=()=>{
      let anchor;try{anchor=decodeURIComponent(location.hash.slice(1));}catch{return;}
      const target=Object.hasOwn(config.anchors,anchor)?config.anchors[anchor]:null;
      if(target)location.replace(target+location.hash);
    };
    forward();window.addEventListener('hashchange',forward);return;
  }
  const menus=[...document.querySelectorAll('.reading-menu')];
  for(const menu of menus){
    menu.addEventListener('toggle',()=>{
      if(menu.open)for(const other of menus)if(other!==menu)other.open=false;
    });
    menu.addEventListener('click',event=>{
      const link=event.target.closest('a');if(!link)return;
      const href=link.getAttribute('href');menu.open=false;
      if(href.startsWith('#')){
        const target=document.getElementById(href.slice(1));
        if(target){target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}
      }
    });
  }
  document.addEventListener('click',event=>{for(const menu of menus)if(!menu.contains(event.target))menu.open=false;});
  document.addEventListener('keydown',event=>{
    if(event.key!=='Escape')return;
    const open=menus.find(menu=>menu.open);
    if(open){open.open=false;open.querySelector('summary').focus();}
  });
  const entries=[...document.querySelectorAll('[data-reading-anchor]')];
  const targets=entries.map(link=>document.getElementById(link.dataset.readingAnchor));
  const sections=[...document.querySelectorAll('.chapter[id]')];
  const switchLink=document.getElementById('reading-chapter-switch');
  let pending=false;
  function update(){
    pending=false;
    const bar=document.getElementById('reading-tools'),line=bar.getBoundingClientRect().bottom+35;
    document.documentElement.style.setProperty('--reading-offset',line+'px');
    if(entries.length){
      let active=0;
      // Fractional font/layout pixels must not select the preceding section
      // when the browser has landed exactly on a fragment's scroll margin.
      targets.forEach((el,i)=>{if(el&&el.getBoundingClientRect().top<=line+2)active=i;});
      entries.forEach((link,i)=>{if(i===active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
      document.getElementById('reading-position').textContent=`${active+1} / ${entries.length}`;
    }
    if(switchLink){
      let active=config.chapters[0];
      sections.forEach(el=>{if(el.getBoundingClientRect().top<=line+2&&config.chapters.includes(el.id))active=el.id;});
      switchLink.href=config.root+active+'/';
    }
  }
  const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(update);}};
  window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);
  window.addEventListener('hashchange',schedule);window.addEventListener('load',schedule);
  update();
})();
