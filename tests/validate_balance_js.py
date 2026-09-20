from pathlib import Path
import re
import subprocess
import tempfile
from test_toolchain import temporary_directory

root = Path(__file__).resolve().parents[1]
src = (root / "src/main.cpp").read_text(encoding="utf-8")
method = src.index("void MaybeCaptureAccountBalance()")
start = src.index('const std::string js = R"JS((()=>{try{', method)
end = src.index("const std::string params =", start)
segment = src[start:end]
chunks = list(re.finditer(r'R"JS\((.*?)\)JS"', segment, re.S))
assert len(chunks) == 2
javascript = chunks[0].group(1) + "test-run" + chunks[1].group(1)

with temporary_directory() as directory:
    directory = Path(directory)
    full = directory / "balance-probe.js"
    full.write_text(javascript, encoding="utf-8")
    subprocess.run(["node", "--check", str(full)], check=True)

    runtime = r'''
const emitted=[];
const originalLog=console.log;
console.log=value=>emitted.push(String(value));
const account={
  isConnected:true,childElementCount:0,parentElement:null,
  innerText:'MARJOME\n201,65 €',textContent:'MARJOME\n201,65 €',
  id:'',className:'',tagName:'DIV',
  getAttribute:()=>'',
  getBoundingClientRect:()=>({left:700,right:800,top:12,bottom:55,width:100,height:43})
};
globalThis.location={href:'https://betify.com/casino'};
globalThis.innerWidth=1200;
globalThis.document={querySelectorAll:()=>[account]};
globalThis.getComputedStyle=()=>({display:'block',visibility:'visible',opacity:'1'});
''' + javascript + r''';
const marker=emitted.find(x=>x.startsWith('__BAC_ACCOUNT_BALANCE__'));
if(!marker)throw new Error('compact account header not detected');
const payload=JSON.parse(marker.slice('__BAC_ACCOUNT_BALANCE__'.length));
if(payload.minorUnits!==20165||payload.currency!=='EUR'||payload.score<95)
  throw new Error(JSON.stringify(payload));
originalLog('compact Betify account-header detection OK');
'''
    runtime_path = directory / "header-runtime.js"
    runtime_path.write_text(runtime, encoding="utf-8")
    subprocess.run(["node", str(runtime_path)], check=True)

    parser_start = javascript.index("const norm=")
    parser_end = javascript.index("const semantic=", parser_start)
    parser = javascript[parser_start:parser_end]
    parser += r'''
const tests=[
  ['5.000,25 €',500025,'EUR'],
  ['EUR 1234.50',123450,'EUR'],
  ['$ 42.10',4210,'USD'],
  ['1 234,56 GBP',123456,'GBP']
];
for(const [text,minor,currency] of tests){
  const parsed=parseMoney(text);
  if(!parsed||parsed.minorUnits!==minor||parsed.currency!==currency)
    throw new Error(text+': '+JSON.stringify(parsed));
}
'''
    parser_path = directory / "money-parser.js"
    parser_path.write_text(parser, encoding="utf-8")
    subprocess.run(["node", str(parser_path)], check=True)

print("balance JavaScript syntax/parser OK")
