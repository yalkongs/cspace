/* No network, animation loop or dependencies: all data is embedded at build time. */
(() => {
 'use strict';
 const C=ColorMath, config=JSON.parse(document.getElementById('lab-config').textContent);
 const ko=config.lang==='ko',t=(en,kr)=>ko?kr:en;
 const data=JSON.parse(document.getElementById('observer-data').textContent),cmf=data.two;
 const controls=document.getElementById('controls'),result=document.getElementById('results');
 const fmt=(x,n=3)=>Number(x).toFixed(n),vec=(a,n=3)=>a.map(x=>fmt(x,n)).join(', ');
 let update=()=>{};
 function range(id,en,kr,min,max,value,step=1,unit=''){
  controls.insertAdjacentHTML('beforeend',`<label class="control" for="${id}"><span class="control-line"><span>${t(en,kr)}</span><output id="${id}-value" for="${id}">${value}${unit}</output></span><input id="${id}" type="range" min="${min}" max="${max}" value="${value}" step="${step}" data-unit="${unit}"></label>`);
 }
 function color(id,en,kr,value){controls.insertAdjacentHTML('beforeend',`<label class="control" for="${id}">${t(en,kr)}<input id="${id}" type="color" value="${value}"></label>`);}
 function select(id,en,kr,options){controls.insertAdjacentHTML('beforeend',`<label class="control" for="${id}">${t(en,kr)}<select id="${id}">${options.map(([v,e,k])=>`<option value="${v}">${t(e,k)}</option>`).join('')}</select></label>`);}
 const val=id=>document.getElementById(id).value,num=id=>+val(id);
 const clipped=t('sRGB preview clipped','sRGB 근사색 클리핑');
 function patch(name,rgb,detail=''){
  return `<div class="swatch"><div class="patch" style="background:${C.css(rgb)}" role="img" aria-label="${name}: ${C.hex(rgb)}"></div><strong>${name}</strong><small>${detail||C.hex(rgb)}</small>${C.inGamut(rgb)?'':`<small class="gamut">⚠ ${clipped}</small>`}</div>`;
 }
 function gradient(colors){return `<div class="gradient" role="img" aria-label="${t('Colour progression','색의 변화')}" style="background:linear-gradient(to right,${colors.map(C.css).join(',')})"></div>`;}
 const inks=['#9b483e','#38695b','#3b5791','#67513e'];
 function plot(series,labels,x0=380,x1=780,xLabel='nm',fixedMax=null){
  const max=fixedMax||Math.max(1e-12,...series.flat()),W=580,H=205,left=44,right=564,top=16,bottom=168;
  let s=`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${labels.join(', ')}; ${x0}–${x1} ${xLabel}"><title>${labels.join(', ')}</title>`;
  for(let i=0;i<=4;i++){const y=bottom-(bottom-top)*i/4;s+=`<path d="M${left} ${y}H${right}" stroke="#cbc7bd"/><text x="2" y="${y+4}">${fmt(max*i/4,max>3?1:2)}</text>`;}
  series.forEach((ys,j)=>{const points=ys.map((v,i)=>`${left+i*(right-left)/(ys.length-1)},${bottom-v/max*(bottom-top)}`).join(' ');s+=`<polyline points="${points}" fill="none" stroke="${inks[j%4]}" stroke-width="2.5" ${j%2?'stroke-dasharray="7 3"':''}/>`;});
  for(let i=0;i<=4;i++)s+=`<text text-anchor="middle" x="${left+i*(right-left)/4}" y="190">${fmt(x0+(x1-x0)*i/4,0)}</text>`;
  return s+`<text text-anchor="end" x="${right}" y="204">${xLabel}</text></svg><div class="legend">${labels.map((l,i)=>`<span style="--stroke:${inks[i%4]}">${l}${i%2?t(' (dashed)',' (점선)'):''}</span>`).join('')}</div>`;
 }
 function observation(en,kr){return `<p class="observation">${t(en,kr)}</p>`;}
 const spectrumRGB=(xyz,white)=>C.xyzRGB(C.adapt(xyz,white,C.D65));
 const methods=[(a,b,p)=>C.mix(a,b,p),(a,b,p)=>C.mix(a.map(C.decode),b.map(C.decode),p).map(C.encode),(a,b,p)=>C.okRGB(C.mix(C.rgbOK(a),C.rgbOK(b),p))];
 switch(config.slug){
 case 'xyz': {
  range('peak','Peak wavelength','중심 파장',400,700,530,5,' nm');range('width','Spectral width (σ)','대역 폭 (σ)',5,100,15,1,' nm');
  select('observer','Standard observer','표준 관찰자',[['two','1931 · 2°','1931 · 2°'],['ten','1964 · 10°','1964 · 10°']]);
  for(const [id,en,kr] of [['red','Red code','빨강 코드'],['green','Green code','초록 코드'],['blue','Blue code','파랑 코드']])range(id,en,kr,0,255,id==='green'?150:40);
  update=()=>{
   const spd=cmf.map(r=>C.gaussian(r[0],num('peak'),num('width'))),xyz=C.integrate(spd,cmf),scale=.25/xyz[1];
   const normalized=spd.map(x=>x*scale),target=xyz.map(x=>x*scale),selected=C.integrate(normalized,data[val('observer')]);
   const rgb=['red','green','blue'].map(id=>num(id)/255),matched=C.rgbXYZ(rgb),sum=selected.reduce((a,b)=>a+b);
   const required=C.xyzRGB(target).map(C.decode);
   result.innerHTML=`<h2>${t('Target and your RGB match (2° preview)','시험광과 RGB 맞추기 (2° 미리보기)')}</h2><div class="swatches">${patch(t('Spectral target','시험광'),C.xyzRGB(target))}${patch(t('Your match','나의 혼합'),rgb)}</div><div class="readout">${t('Selected observer XYZ','선택 관찰자 XYZ')}: ${vec(selected)}\nxyY: ${vec([selected[0]/sum,selected[1]/sum,selected[1]])}\n${t('Required linear sRGB (2°)','필요한 선형 sRGB (2°)')}: ${vec(required)}\n${t('Your XYZ (2°)','나의 XYZ (2°)')}: ${vec(matched)}\n${t('XYZ Euclidean mismatch (not ΔE)','XYZ 유클리드 오차 (ΔE 아님)')}: ${fmt(C.delta76(target,matched),4)}</div>${plot([spd,...[1,2,3].map(j=>data[val('observer')].map(r=>r[j]))],[t('SPD (peak=1)','SPD (최댓값=1)'),'x̄','ȳ','z̄'])}${observation(required.some(x=>x<0)?'A negative primary is required. Positive RGB controls cannot reach this target.':'Compare the numerical XYZ mismatch, not just the clipped patches.',required.some(x=>x<0)?'음의 원색이 필요합니다. 양의 RGB 조절만으로 이 목표에 도달할 수 없습니다.':'클리핑된 색 패치뿐 아니라 XYZ 수치 오차를 비교하세요.')}`;
  };break;
 }
 case 'gamma': {
  color('first','First colour','첫 번째 색','#000000');color('second','Second colour','두 번째 색','#ffffff');range('ratio','Second colour','두 번째 색 비율',0,100,50,1,'%');
  update=()=>{const a=C.fromHex(val('first')),b=C.fromHex(val('second')),p=num('ratio')/100,names=['sRGB',t('Linear light','선형광'),'OKLab'];
   const rows=methods.map(f=>Array.from({length:41},(_,i)=>f(a,b,i/40))),current=methods.map(f=>f(a,b,p));
   result.innerHTML=`<div class="swatches">${current.map((r,i)=>patch(names[i],r,`${vec(r.map(x=>C.clamp(x)*255),0)} · Y=${fmt(C.rgbXYZ(r.map(x=>C.clamp(x)))[1])}`)).join('')}</div>${rows.map((r,i)=>`<div class="label">${names[i]}</div>${gradient(r)}`).join('')}${plot(rows.map(r=>r.map(rgb=>C.rgbXYZ(rgb.map(x=>C.clamp(x)))[1])),names,0,100,'%',1)}${observation('Solid/dashed curves compare displayed relative luminance. Linear light is the energy average; OKLab is a perceptual interpolation.','실선·점선은 표시색의 상대 휘도입니다. 선형광은 빛의 에너지 평균, OKLab은 지각적 보간입니다.')}`;
  };break;
 }
 case 'delta-e': {
  range('lightness','Base L*','기준 L*',25,75,55);range('chroma','Base C*','기준 C*',0,45,30);range('hue','Base hue','기준 색상각',0,360,45,1,'°');range('distance','Displacement ΔE76','변위 ΔE76',0,20,8,.5);range('direction','a*b* displacement angle','a*b* 변위 방향',0,360,0,1,'°');
  update=()=>{const h=num('hue')*Math.PI/180,d=num('direction')*Math.PI/180,dist=num('distance'),a=num('chroma')*Math.cos(h),b=num('chroma')*Math.sin(h);
   const bases=[[num('lightness'),a,b],[num('lightness')-20,a,b],[num('lightness'),a*.25,b*.25]],names=[t('Base pair','기준 쌍'),t('Darker pair','어두운 쌍'),t('Lower-chroma pair','낮은 크로마 쌍')];
   result.innerHTML=bases.map((base,i)=>{const next=[base[0],base[1]+dist*Math.cos(d),base[2]+dist*Math.sin(d)];return `<h2>${names[i]} · ΔE76 ${fmt(C.delta76(base,next),2)} / ΔE00 ${fmt(C.delta00(base,next),2)}</h2><div class="swatches">${patch('A',C.xyzRGB(C.labXYZ(base)),`Lab: ${vec(base,1)}`)}${patch('B',C.xyzRGB(C.labXYZ(next)),`Lab: ${vec(next,1)}`)}</div>`;}).join('')+observation('The Lab displacement is identical in every pair; the CIEDE2000 weighting depends on its location.','세 쌍의 Lab 변위는 같습니다. CIEDE2000의 가중치는 색 공간 안의 위치에 따라 달라집니다.');
  };break;
 }
 case 'rendering': {
  range('narrow','Narrow-band contribution','좁은 대역 비중',0,100,100,1,'%');range('temperature','Reference Planck spectrum','기준 플랑크 스펙트럼',4000,8000,6500,100,' K');
  update=()=>{const {broad,narrow}=C.matchedLights(cmf,num('temperature')),light=C.mix(broad,narrow,num('narrow')/100),white=C.integrate(broad,cmf),white2=C.integrate(light,cmf);
   const samples=[cmf.map(()=>.5),...[[440,22],[500,35],[550,18],[610,35],[670,30]].map(([p,w])=>cmf.map(r=>.06+.80*C.gaussian(r[0],p,w)))];
   const pairs=samples.map(r=>[C.integrate(broad,cmf,r),C.integrate(light,cmf,r)]),diff=pairs.map(([a,b])=>C.delta00(C.xyzLab(a,white),C.xyzLab(b,white)));
   result.innerHTML=`<div class="readout">${t('White XYZ mismatch','백색 XYZ 오차')}: ${C.delta76(white,white2).toExponential(2)}\n${t('Sample mean ΔE00 (NOT Ra / Rf)','표본 평균 ΔE00 (Ra / Rf 아님)')}: ${fmt(diff.reduce((s,x)=>s+x)/diff.length,2)}</div>${plot([broad,light],[t('Broad reference SPD','넓은 기준 SPD'),t('Test SPD','시험 SPD')])}<div class="swatches">${patch(t('Reference white','기준 백색'),spectrumRGB(white,white))}${patch(t('Test white','시험 백색'),spectrumRGB(white2,white))}</div>${pairs.map(([a,b],i)=>`<h2>${t('Synthetic sample','가상 표본')} ${i+1} · ΔE00 ${fmt(diff[i],2)}</h2><div class="swatches">${patch(t('Reference','기준'),spectrumRGB(a,white))}${patch(t('Test','시험'),spectrumRGB(b,white))}</div>`).join('')}${plot(samples.slice(1,4),[t('Sample 2 reflectance','표본 2 반사율'),t('Sample 3 reflectance','표본 3 반사율'),t('Sample 4 reflectance','표본 4 반사율')],380,780,'nm',1)}${observation('The neutral sample stays matched; selective reflectances expose differences hidden by the matching white point.','중성 표본은 계속 일치합니다. 특정 파장을 선택하는 반사율은 같은 백색점에 가려진 스펙트럼 차이를 드러냅니다.')}`;
  };break;
 }
 case 'gamut-mapping': {
  range('lightness','Source L*','원본 L*',20,90,65);range('chroma','Source C*','원본 C*',0,100,70);range('hue','Source hue','원본 색상각',0,360,40,1,'°');range('limit','Model chroma limit','모형 크로마 한계',10,100,40);range('paper','Paper warmth','종이 백색의 따뜻함',0,100,60,1,'%');
  update=()=>{const h=num('hue')*Math.PI/180,L=num('lightness'),limit=num('limit'),white=C.mix(C.D65,[.96422,1,.82521],num('paper')/100);
   const source=c=>C.labXYZ([L,c*Math.cos(h),c*Math.sin(h)]);
   const clipXYZ=xyz=>{let lab=C.xyzLab(xyz,white),ch=Math.hypot(lab[1],lab[2]),s=ch>limit?limit/ch:1;return C.labXYZ([C.clamp(lab[0],0,100),lab[1]*s,lab[2]*s],white);};
   const render=(c,type)=>{const xyz=source(c);if(type==='absolute')return clipXYZ(xyz);return C.adapt(source(type==='relative'?Math.min(c,limit):c*limit/100),C.D65,white);};
   const names=[t('Source','원본'),t('Relative example','상대 예시'),t('Absolute example','절대 예시'),t('Perceptual example','지각적 예시')],types=['relative','absolute','perceptual'];
   result.innerHTML=`<div class="swatches">${patch(names[0],C.xyzRGB(source(num('chroma'))))}${types.map((type,i)=>patch(names[i+1],C.xyzRGB(render(num('chroma'),type)))).join('')}</div><h2>${t('What happens to source white?','원본 백색은 어떻게 되는가?')}</h2><div class="swatches">${patch(t('Paper / relative white','종이 / 상대 백색'),C.xyzRGB(white))}${patch(t('Absolute source white','절대 원본 백색'),C.xyzRGB(clipXYZ(C.D65)))}</div>${types.map((type,i)=>`<div class="label">${names[i+1]} · C* 0–100</div>${gradient(Array.from({length:31},(_,j)=>C.xyzRGB(render(j*100/30,type))))}`).join('')}${plot([Array.from({length:101},(_,c)=>Math.min(c,limit)),Array.from({length:101},(_,c)=>c*limit/100)],[t('Relative chroma clipping','상대 크로마 클리핑'),t('Example compression','예시 압축')],0,100,'C*',100)}${observation('Clipping merges high-chroma colours; compression changes even colours already inside the target. Paper-white adaptation is a separate decision.','클리핑은 높은 크로마의 차이를 합치고, 압축은 출력 색역 안에 있던 색도 바꿉니다. 종이 백색에 대한 순응은 별도의 결정입니다.')}`;
  };break;
 }
 case 'appearance': {
  color('stimulus','Fixed stimulus (sRGB)','고정 자극 (sRGB)','#b36c52');range('adaptation','Adaptation luminance L_A','적응 휘도 L_A',1,500,64,1,' cd/m²');range('background','Background Y_b','배경 Y_b',1,80,20);
  select('surround','Surround','주변 조건',[['average','Average','평균'],['dim','Dim','어두움'],['dark','Dark','암흑']]);select('white','Reference white','기준 백색',[['D65','D65','D65'],['D50','D50','D50']]);
  update=()=>{const rgb=C.fromHex(val('stimulus')),xyz=C.rgbXYZ(rgb).map(x=>x*100),white=val('white')==='D65'?[95.05,100,108.88]:[96.422,100,82.521];
   const ref=C.cam16(xyz),cur=C.cam16(xyz,white,num('adaptation'),num('background'),val('surround'));
   const labels=[['J',t('Lightness','명도')],['Q',t('Brightness','밝기')],['C',t('Chroma','크로마')],['M',t('Colourfulness','색채감')],['s',t('Saturation','채도')],['h',t('Hue angle','색상각')]];
   result.innerHTML=`<div class="swatches">${patch(t('Unchanged physical RGB','변하지 않는 실제 RGB'),rgb,`XYZ (Yw=100): ${vec(xyz,2)}`)}</div><table class="metrics"><thead><tr><th>${t('Correlate','외관 속성')}</th><th>${t('Default','기본 조건')}</th><th>${t('Current','현재 조건')}</th></tr></thead><tbody>${labels.map(([k,l])=>`<tr><th scope="row">${k} · ${l}</th><td>${fmt(ref[k],2)}</td><td>${fmt(cur[k],2)}</td></tr>`).join('')}</tbody></table><div class="readout">${t('Degree of adaptation D','순응도 D')}: ${fmt(cur.D)}\n${t('Default: D65, L_A=64, Y_b=20, average surround','기본: D65, L_A=64, Y_b=20, 평균 주변')}</div>${observation('Only predicted appearance correlates change. The display patch does not simulate physical viewing conditions.','변하는 것은 외관 속성의 예측값입니다. 색 패치는 실제 관찰 환경을 시뮬레이션하지 않습니다.')}`;
  };break;
 }
 case 'halftone': {
  range('coverage','Nominal coverage','명목 면적률',0,100,50,1,'%');range('zoom','Dot spacing / magnification','점 간격 / 확대율',4,48,16,1,' px');range('gain','Physical gain at midtone','중간톤의 물리적 게인',0,20,0,1,'%p');range('optical','Optical parameter n','광학 매개변수 n',1,3,1,.1);select('second','Second screen (moiré only)','두 번째 망점 (모아레 관찰용)',[['off','Off','끄기'],['on','On','켜기']]);range('angle','Second screen angle','두 번째 망점 각도',0,90,5,1,'°');
  update=()=>{const a=C.dotArea(num('coverage')/100,num('gain')/100),R=C.halftoneReflectance(a,num('optical')),r=C.encode(R);
   result.innerHTML=`<canvas id="dots" width="640" height="340" role="img" aria-label="${t('Halftone screen','망점 화면')}; ${fmt(a*100,1)}%"></canvas><div class="swatches">${patch(t('Single-screen predicted mean','단일 망점 예측 평균'),[r,r,r],`R = ${fmt(R)} · ${t('effective area','실효 면적')} ${fmt(a*100,1)}%`)}</div><div class="readout">${t('Geometry: square AM dots; average: Yule–Nielsen model','기하: 사각 AM 망점 / 평균: Yule–Nielsen 모형')}</div>${observation('Zoom changes dot spacing, not area coverage. A second rotated grid can form large-scale moiré patterns; it is excluded from the single-screen mean.','확대율은 점 간격만 바꾸고 면적률은 바꾸지 않습니다. 두 번째 격자를 회전하면 큰 모아레 무늬가 나타날 수 있으며, 이는 단일 망점 평균 계산에서 제외됩니다.')}`;
   const ctx=document.getElementById('dots').getContext('2d'),space=num('zoom'),size=space*Math.sqrt(a);ctx.fillStyle='#fff';ctx.fillRect(0,0,640,340);
   const draw=(angle,alpha)=>{ctx.save();ctx.translate(320,170);ctx.rotate(angle*Math.PI/180);ctx.fillStyle=`rgba(48,48,48,${alpha})`;for(let x=-700;x<=700;x+=space)for(let y=-700;y<=700;y+=space)ctx.fillRect(x-size/2,y-size/2,size,size);ctx.restore();};
   draw(0,1);if(val('second')==='on')draw(num('angle'),.6);
  };break;
 }
 case 'thin-film': {
  range('thickness','Film thickness','막 두께',0,1200,350,5,' nm');range('index','Refractive index n','굴절률 n',1.1,2.2,1.5,.01);range('angle','Incidence angle in air','공기 중 입사각',0,75,0,1,'°');
  const light=C.normalizeSPD(cmf.map(r=>C.planck(r[0],6500)),cmf),white=C.integrate(light,cmf);
  update=()=>{const n=num('index'),angle=num('angle'),spectrum=d=>cmf.map(r=>C.filmReflectance(r[0],d,n,angle));
   const R=spectrum(num('thickness')),xyz=C.integrate(light,cmf,R),rgb=spectrumRGB(xyz,white);
   result.innerHTML=`<div class="swatches">${patch(t('Reflected light','반사광'),rgb,`Y = ${fmt(xyz[1],4)}`)}${patch(t('Incident white reference','입사 백색 기준'),spectrumRGB(white,white))}</div>${plot([R],[t('Unpolarized reflectance','비편광 반사율')],380,780,'nm',1)}<h2>${t('Thickness sweep · 0–1200 nm','두께 변화 · 0–1200 nm')}</h2>${gradient(Array.from({length:121},(_,i)=>spectrumRGB(C.integrate(light,cmf,spectrum(i*10)),white)))}<div class="readout">${t('Mean spectral reflectance','분광 반사율 산술 평균')}: ${fmt(R.reduce((a,b)=>a+b)/R.length)}\n${t('Fixed illumination; no per-colour brightness normalization','고정 조명 / 색별 밝기 재정규화 없음')}</div>${observation('The colour comes from wavelength-dependent interference, not a rotating colour wheel. A zero-thickness layer has zero reflection in this air–film–air model.','색상환을 회전한 것이 아니라 파장별 간섭으로 색이 생깁니다. 공기–막–공기 모형에서 두께 0인 층은 반사하지 않습니다.')}`;
  };break;
 }
 default: throw new Error('Unknown experiment');
 }
 controls.insertAdjacentHTML('beforeend',`<button type="reset">${t('Reset experiment','실험 초기화')}</button>`);
 function refresh(){for(const input of controls.querySelectorAll('input[type=range]'))document.getElementById(input.id+'-value').textContent=input.value+input.dataset.unit;update();}
 controls.addEventListener('input',refresh);
 controls.addEventListener('reset',()=>{requestAnimationFrame(refresh);});
 refresh();
})();
