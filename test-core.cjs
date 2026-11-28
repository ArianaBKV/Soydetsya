const assert=require('node:assert/strict'); const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'); const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8'); const source=html.match(/<script id="core-script">([\s\S]*?)<\/script>/)[1]; const sandbox={module:{exports:{}}}; vm.runInNewContext(source,sandbox); const {model}=sandbox.module.exports; const b={p0:2000,p1:1800,r:20,c:1100,q0:100,extra:0,stock:200};
const tests=[['ниже',{lo:110,hi:140},'below',148],['пересечение',{lo:120,hi:170},'cross',148],['выше',{lo:160,hi:190},'above',148],['на пороге',{lo:148,hi:148},'above',148],['без диапазона',{lo:null,hi:null},'missing',148],['недостаток запасов',{lo:160,hi:190,stock:147},'below',148],['нулевой доход с единицы',{lo:100,hi:200,p1:1375},'below',null],['отрицательный доход с единицы',{lo:100,hi:200,p1:1000},'below',null],['доп. расходы',{lo:150,hi:160,extra:1000},'above',150],['нет спроса и недостаточный запас',{lo:null,hi:null,stock:140},'below',148],['неверный диапазон',{lo:170,hi:120},'error'],['отрицательная ставка',{lo:100,hi:200,r:-1},'error'],['база неположительна',{lo:100,hi:200,p0:1000},'error'],['одна граница отсутствует',{lo:100,hi:null},'error'],['точное равенство',{p0:1500,p1:1400,c:800,q0:80,extra:1600,lo:105,hi:105},'above',105]];
for(const [n,x,k,t] of tests){let m=model({...b,...x});assert.equal(m.error?'error':m.kind,k,n);if(t!==undefined)assert.equal(m.need,t,n);console.log(n+': OK');}
// Independent enumeration oracle: bounded integer scenarios, seeded deterministic data.
let seed=246813579; const rnd=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
for(let j=0;j<1000;j++){
 const x={p0:100+rnd(1901),p1:1+rnd(2000),r:rnd(81),c:rnd(600),q0:1+rnd(100),extra:rnd(500),stock:rnd(121),lo:rnd(101),hi:0};x.hi=x.lo+rnd(41);
 const m=model(x);const u=p=>BigInt(p)*BigInt(100-x.r)-BigInt(100*x.c),u0=u(x.p0),u1=u(x.p1),base=u0*BigInt(x.q0),F=BigInt(x.extra*100);
 if(base<=0n){assert.ok(m.error,`case ${j}: base`);continue;}
 const need=u1>0n?Number((base+F+u1-1n)/u1):null;
 let min=null,max=null;for(let D=x.lo;D<=x.hi;D++){const v=u1*BigInt(Math.min(D,x.stock))-F;min=min===null||v<min?v:min;max=max===null||v>max?v:max;}
 assert.equal(m.base,Number(base),`case ${j}: base`);assert.equal(m.m1,Number(u1),`case ${j}: unit`);assert.equal(m.need,need,`case ${j}: threshold`);assert.equal(m.low,Number(min),`case ${j}: min`);assert.equal(m.high,Number(max),`case ${j}: max`);assert.equal(m.kind,min>=base?'above':max<base?'below':'cross',`case ${j}: category`);
 if(need!==null){assert.ok(u1*BigInt(need)-F>=base);assert.ok(u1*BigInt(need-1)-F<base);}
}
console.log('1 000 дополнительных детерминированных наборов: OK (BigInt и прямой перебор спроса)');
