/** Render the native definitions with an installed compatible Presentation API. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import * as helpers from './native/helpers.mjs';
import {addDiagram} from './native/diagrams.mjs';
import {addStatFigure,validateStatData} from './native/statistical_figures.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2);
function option(name,fallback){const i=args.indexOf(name);if(i<0)return fallback;if(!args[i+1])throw new Error(`Missing value for ${name}`);return args[i+1];}
if(args.includes('--help')){
 console.log('node render_native.mjs [--lang en|zh|both] [--figures 2,3,4,5,6,7] [--output-dir PATH] [--artifact-module PATH] [--overwrite]\nRequires the compatible @oai/artifact-tool Presentation runtime; see README.md.');
 process.exit(0);
}
const language=option('--lang','en');
if(!['en','zh','both'].includes(language))throw new Error('--lang must be en, zh or both');
const numbers=option('--figures','2,3,4,5,6,7').split(',').map(Number);
if(!numbers.length||numbers.some(n=>![2,3,4,5,6,7].includes(n)))throw new Error('Native definitions cover Figures 2-7; use source/figure_01.py for Figure1.');
const output=path.resolve(option('--output-dir',path.join(HERE,'output','native')));
for(const name of ['png','native','source','data']){
 const target=path.join(HERE,name);
 if(output===target||output.startsWith(target+path.sep))throw new Error('Choose a generated-output directory, not a source/reference directory.');
}
const modulePath=option('--artifact-module',process.env.ARTIFACT_TOOL_MODULE||'@oai/artifact-tool');
let api;
try{api=await import(modulePath==='@oai/artifact-tool'?modulePath:pathToFileURL(path.resolve(modulePath)).href);}
catch(e){throw new Error('The native Presentation runtime could not be loaded. This is a private host dependency, not installed by requirements.txt. Provide --artifact-module pointing to a compatible installation. Original PNGs remain available in png/.',{cause:e});}
if(typeof api.Presentation?.create!=='function')throw new Error('The supplied module does not expose Presentation.create.');
validateStatData(helpers.contract);
for(const lang of language==='both'?['en','zh']:[language]){
 const presentation=api.Presentation.create({slideSize:{width:1600,height:1500}});
 const directory=path.join(output,lang);await fs.mkdir(directory,{recursive:true});
 for(const number of numbers){
  const filename=path.join(directory,`Figure_${String(number).padStart(2,'0')}_full.png`);
  if(!args.includes('--overwrite')){try{await fs.access(filename);throw new Error(`Output exists: ${filename}`);}catch(e){if(e.code!=='ENOENT')throw e;}}
  let slide;
  if(number===2||number===4){const result=await addDiagram(presentation,number,lang,helpers);slide=presentation.slides.items.find(s=>s.id===result.slideId);}
  else slide=await addStatFigure(presentation,number,lang,helpers);
  if(!slide)throw new Error(`Figure ${number} did not produce a slide`);
  const blob=await presentation.export({slide,format:'png',scale:2});
  await fs.writeFile(filename,new Uint8Array(await blob.arrayBuffer()));
  console.log(`${lang} Figure ${number}: ${filename}`);
 }
}
