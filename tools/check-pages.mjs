import {spawn} from 'node:child_process';
import {readdir} from 'node:fs/promises';
import path from 'node:path';
import {ROOT} from './build-pages.mjs';
const files=(await readdir(path.join(ROOT,'tests'))).filter(f=>f.endsWith('.test.mjs')).map(f=>'tests/'+f);
const child=spawn(process.execPath,['--test',...files],{cwd:ROOT,stdio:'inherit',windowsHide:true});
child.on('error',error=>{console.error(error.message);process.exitCode=1;});child.on('exit',code=>process.exitCode=code??1);
