/* Educational colour calculations. XYZ uses Y=1; CAM16 alone uses Y=100.
 * Sources and data licences: experiments/data/README.md and each lab page. */
(function (root) {
  'use strict';
  const clamp = (x, lo=0, hi=1) => Math.min(hi, Math.max(lo, x));
  const mul = (m, v) => m.map(row => row.reduce((s,x,i) => s+x*v[i],0));
  const mix = (a,b,t) => a.map((x,i) => x*(1-t)+b[i]*t);
  const decode = x => x <= .04045 ? x/12.92 : ((x+.055)/1.055)**2.4;
  const encode = x => x <= .0031308 ? 12.92*x : 1.055*x**(1/2.4)-.055;
  const RGB_XYZ = [[.4123907993,.3575843394,.1804807884],[.2126390059,.7151686788,.0721923154],[.0193308187,.1191947798,.9505321522]];
  const XYZ_RGB = [[3.2409699419,-1.5373831776,-.4986107603],[-.9692436363,1.8759675015,.0415550574],[.0556300797,-.2039769589,1.0569715142]];
  const D65 = [.9504559271,1,1.0890577508];
  const rgbXYZ = rgb => mul(RGB_XYZ,rgb.map(decode));
  const xyzRGB = xyz => mul(XYZ_RGB,xyz).map(encode);
  const inGamut = rgb => rgb.every(x => x >= -1e-6 && x <= 1+1e-6);
  const css = rgb => 'rgb('+rgb.map(x=>Math.round(clamp(x)*255)).join(',')+')';
  const hex = rgb => '#'+rgb.map(x=>Math.round(clamp(x)*255).toString(16).padStart(2,'0')).join('');
  const fromHex = h => [1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255);
  function xyzLab(xyz, white=D65) {
    const f = xyz.map((x,i)=>x/white[i]).map(t=>t>216/24389?Math.cbrt(t):(24389/27*t+16)/116);
    return [116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])];
  }
  function labXYZ(lab, white=D65) {
    const y=(lab[0]+16)/116, f=[y+lab[1]/500,y,y-lab[2]/200];
    return f.map((t,i)=>white[i]*(t>6/29?t**3:(116*t-16)/(24389/27)));
  }
  function rgbOK(rgb) {
    const lms=mul([[.4122214708,.5363325363,.0514459929],[.2119034982,.6806995451,.1073969566],[.0883024619,.2817188376,.6299787005]],rgb.map(decode)).map(Math.cbrt);
    return mul([[.2104542553,.793617785,-.0040720468],[1.9779984951,-2.428592205,.4505937099],[.0259040371,.7827717662,-.808675766]],lms);
  }
  function okRGB(lab) {
    const lms=mul([[1,.3963377774,.2158037573],[1,-.1055613458,-.0638541728],[1,-.0894841775,-1.291485548]],lab).map(x=>x**3);
    return mul([[4.0767416621,-3.3077115913,.2309699292],[-1.2684380046,2.6097574011,-.3413193965],[-.0041960863,-.7034186147,1.707614701]],lms).map(encode);
  }
  const delta76=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
  function delta00(lab1,lab2) {
    const rad=Math.PI/180, deg=180/Math.PI;
    const [L1,a1,b1]=lab1,[L2,a2,b2]=lab2;
    const Cbar=(Math.hypot(a1,b1)+Math.hypot(a2,b2))/2;
    const G=.5*(1-Math.sqrt(Cbar**7/(Cbar**7+25**7)));
    const ap1=(1+G)*a1,ap2=(1+G)*a2,C1=Math.hypot(ap1,b1),C2=Math.hypot(ap2,b2);
    const hue=(a,b)=>Math.hypot(a,b)<1e-14?0:(Math.atan2(b,a)*deg+360)%360;
    const h1=hue(ap1,b1),h2=hue(ap2,b2),dL=L2-L1,dC=C2-C1;
    let dh=h2-h1;
    if(C1*C2===0) dh=0; else if(dh>180) dh-=360; else if(dh< -180) dh+=360;
    const dH=2*Math.sqrt(C1*C2)*Math.sin(dh*rad/2),L=(L1+L2)/2,C=(C1+C2)/2;
    let h=h1+h2;
    if(C1*C2!==0) h=Math.abs(h1-h2)<=180?h/2:(h<360?(h+360)/2:(h-360)/2);
    const T=1-.17*Math.cos((h-30)*rad)+.24*Math.cos(2*h*rad)+.32*Math.cos((3*h+6)*rad)-.20*Math.cos((4*h-63)*rad);
    const SL=1+.015*(L-50)**2/Math.sqrt(20+(L-50)**2),SC=1+.045*C,SH=1+.015*C*T;
    const RT=-2*Math.sqrt(C**7/(C**7+25**7))*Math.sin(60*Math.exp(-(((h-275)/25)**2))*rad);
    return Math.sqrt((dL/SL)**2+(dC/SC)**2+(dH/SH)**2+RT*dC/SC*dH/SH);
  }
  // Bradford adaptation, used only to illustrate media-white adaptation.
  function adapt(xyz, source, target) {
    const M=[[.8951,.2664,-.1614],[-.7502,1.7135,.0367],[.0389,-.0685,1.0296]];
    const I=[[.9869929,-.1470543,.1599627],[.4323053,.5183603,.0492912],[-.0085287,.0400428,.9684867]];
    const s=mul(M,source),t=mul(M,target);
    return mul(I,mul(M,xyz).map((v,i)=>v*t[i]/s[i]));
  }
  function cam16(xyz, white=[95.05,100,108.88], LA=64, Yb=20, surround='average') {
    const [F,c,Nc]=({average:[1,.69,1],dim:[.9,.59,.9],dark:[.8,.525,.8]})[surround];
    const M=[[.401288,.650173,-.051461],[-.250268,1.204414,.045854],[-.002079,.048952,.953127]];
    const rgbw=mul(M,white),D=clamp(F*(1-Math.exp((-LA-42)/92)/3.6));
    const k=1/(5*LA+1),FL=.2*k**4*5*LA+.1*(1-k**4)**2*Math.cbrt(5*LA);
    const n=Yb/white[1],z=1.48+Math.sqrt(n),Nbb=.725*n**(-.2);
    const response=v=>mul(M,v).map((x,i)=>{
      const rc=x*(D*white[1]/rgbw[i]+1-D),p=(FL*Math.abs(rc)/100)**.42;
      return Math.sign(rc)*400*p/(p+27.13)+.1;
    });
    const ach=r=>(2*r[0]+r[1]+r[2]/20-.305)*Nbb;
    const Aw=ach(response(white)),r=response(xyz),A=Math.max(0,ach(r));
    const a=r[0]-12*r[1]/11+r[2]/11,b=(r[0]+r[1]-2*r[2])/9;
    const hr=Math.atan2(b,a),h=(hr*180/Math.PI+360)%360,J=100*(A/Aw)**(c*z);
    const et=(Math.cos(hr+2)+3.8)/4;
    const t=(50000/13)*Nc*Nbb*et*Math.hypot(a,b)/(r[0]+r[1]+21*r[2]/20);
    const C=Math.max(0,t)**.9*(1.64-.29**n)**.73*Math.sqrt(J/100),Mcol=C*FL**.25;
    const Q=4/c*Math.sqrt(J/100)*(Aw+4)*FL**.25;
    return {J,Q,C,M:Mcol,s:Q>0?100*Math.sqrt(Mcol/Q):0,h,D};
  }
  const gaussian=(w,peak,width)=>Math.exp(-.5*((w-peak)/width)**2);
  const planck=(w,T)=>1/(w**5*Math.expm1(1.438776877e7/(w*T)));
  function integrate(spd, cmf, reflectance=null) {
    return [0,1,2].map(j=>cmf.reduce((s,row,i)=>s+spd[i]*(reflectance?reflectance[i]:1)*row[j+1]*5,0));
  }
  function normalizeSPD(spd,cmf) {
    const Y=integrate(spd,cmf)[1]; return spd.map(x=>x/Y);
  }
  function solve3(m,b) {
    const a=m.map((r,i)=>[...r,b[i]]);
    for(let j=0;j<3;j++) {
      let p=j; for(let i=j+1;i<3;i++) if(Math.abs(a[i][j])>Math.abs(a[p][j]))p=i;
      [a[j],a[p]]=[a[p],a[j]];
      if(Math.abs(a[j][j])<1e-15)throw Error('Singular matrix');
      const d=a[j][j]; a[j]=a[j].map(x=>x/d);
      for(let i=0;i<3;i++)if(i!==j){const f=a[i][j];a[i]=a[i].map((x,k)=>x-f*a[j][k]);}
    }
    return a.map(r=>r[3]);
  }
  function matchedLights(cmf,T=6500) {
    const broad=normalizeSPD(cmf.map(r=>planck(r[0],T)),cmf);
    const bands=[450,540,610].map(p=>cmf.map(r=>gaussian(r[0],p,12)));
    const xyz=bands.map(b=>integrate(b,cmf));
    const weights=solve3([0,1,2].map(i=>xyz.map(x=>x[i])),integrate(broad,cmf));
    if(weights.some(x=>x<0))throw Error('Unphysical negative light weight');
    return {broad,narrow:cmf.map((_,i)=>bands.reduce((s,b,j)=>s+b[i]*weights[j],0)),weights};
  }
  // Air / lossless film / air, Fresnel coefficients and Airy interference.
  function filmReflectance(wavelength, thickness, n, angle) {
    const theta=angle*Math.PI/180,c0=Math.cos(theta),c1=Math.sqrt(1-(Math.sin(theta)/n)**2);
    const phase=4*Math.PI*n*thickness*c1/wavelength;
    const rs=(c0-n*c1)/(c0+n*c1),rp=(n*c0-c1)/(n*c0+c1);
    const airy=r=>{const R=r*r;return 2*R*(1-Math.cos(phase))/(1+R*R-2*R*Math.cos(phase));};
    return (airy(rs)+airy(rp))/2;
  }
  const dotArea=(a,gain)=>clamp(a+gain*4*a*(1-a));
  const halftoneReflectance=(a,n=1)=>((1-a)+a*.03**(1/n))**n;
  const api={clamp,mul,mix,decode,encode,D65,rgbXYZ,xyzRGB,xyzLab,labXYZ,rgbOK,okRGB,inGamut,css,hex,fromHex,delta76,delta00,adapt,cam16,gaussian,planck,integrate,normalizeSPD,matchedLights,filmReflectance,dotArea,halftoneReflectance};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ColorMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);
