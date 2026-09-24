const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const C=require('../experiments/color-math.js');
let checks=0;
function near(a,b,tol=1e-6){assert.ok(Math.abs(a-b)<tol,`${a} != ${b}`);checks++;}
for(const rgb of [[0,0,0],[1,1,1],[.2,.6,.8],[1,0,.3]]){
 C.xyzRGB(C.rgbXYZ(rgb)).forEach((x,i)=>near(x,rgb[i]));
 C.okRGB(C.rgbOK(rgb)).forEach((x,i)=>near(x,rgb[i],2e-6));
 C.labXYZ(C.xyzLab(C.rgbXYZ(rgb))).forEach((x,i)=>near(x,C.rgbXYZ(rgb)[i]));
}
near(C.encode(.5)*255,187.5160306784,1e-8);
near(C.decode(.5),.214041140482,1e-10);
// Sharma, Wu & Dalal (2005), supplementary test pairs 1–6 and neutral case.
for(const [a,b,expected] of [
 [[50,2.6772,-79.7751],[50,0,-82.7485],2.0425],
 [[50,3.1571,-77.2803],[50,0,-82.7485],2.8615],
 [[50,2.8361,-74.0200],[50,0,-82.7485],3.4412],
 [[50,-1.3802,-84.2814],[50,0,-82.7485],1],
 [[50,-1.1848,-84.8006],[50,0,-82.7485],1],
 [[50,-.9009,-85.5211],[50,0,-82.7485],1],
 [[50,0,0],[50,-1,2],2.3669]
]){near(C.delta00(a,b),expected,5e-5);near(C.delta00(b,a),expected,5e-5);}
near(C.delta00([0,0,0],[0,0,0]),0);
const cam=C.cam16([19.01,20,21.78],[95.05,100,108.88],318.31,20);
near(cam.J,41.7312079051);near(cam.C,.1033557387);near(cam.h,217.0679597674);
near(cam.Q,195.3717089928);near(cam.M,.1074367723);
for(const x of Object.values(C.cam16([0,0,0])))assert.ok(Number.isFinite(x));
const cmfs={};
for(const [name,hash] of [['1931_2deg','17cca777db64b17170f06f67ce9d3ab7'],['1964_10deg','6140e032f9326d88c5a0959b29b4d8f3']]){
 const raw=fs.readFileSync(`experiments/data/CIE_xyz_${name}.csv`);
 assert.equal(crypto.createHash('md5').update(raw).digest('hex'),hash);
 cmfs[name]=raw.toString().trim().split(/\r?\n/).map(r=>r.split(',').map(Number)).filter(r=>r[0]>=380&&r[0]<=780&&r[0]%5===0).map(r=>r.map((v,i)=>i===3&&r[0]>=560&&name==='1964_10deg'?0:v));
 assert.equal(cmfs[name].length,81);assert.ok(cmfs[name].flat().every(Number.isFinite));
}
for(const cmf of Object.values(cmfs))for(const T of [4000,5000,6500,8000]){
 const {broad,narrow}=C.matchedLights(cmf,T);
 assert.ok(narrow.every(v=>v>=0));
 C.integrate(broad,cmf).forEach((x,i)=>near(x,C.integrate(narrow,cmf)[i],1e-10));
}
for(let w=380;w<=780;w+=5)for(const a of [0,30,75])for(const n of [1.1,1.5,2.2]){
 near(C.filmReflectance(w,0,n,a),0);
 for(const d of [100,350,1200]){const R=C.filmReflectance(w,d,n,a);assert.ok(R>=0&&R<=1);}
}
near(C.dotArea(0,.2),0);near(C.dotArea(1,.2),1);
near(C.halftoneReflectance(0,2),1);near(C.halftoneReflectance(1,2),.03);
console.log(`Colour math: ${checks} numeric comparisons, reference fixtures, data hashes and physical bounds passed.`);
