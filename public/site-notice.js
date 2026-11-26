export const siteNotices=[
 {lang:'vi',text:'EssenceLab được tạo ra chỉ để học tập, nghiên cứu và giải trí phi lợi nhuận; không phục vụ bất kỳ mục đích thương mại nào. Đây là dự án độc lập của người hâm mộ, không phải trang web chính thức của Identity V. Hình ảnh, âm thanh và nhãn hiệu thuộc về các chủ sở hữu tương ứng.'},
 {lang:'en',text:'EssenceLab is created solely for learning, research and non-profit entertainment, with no commercial purpose. This is an independent fan project, not an official Identity V website. Images, audio and trademarks belong to their respective owners.'},
 {lang:'zh-Hans',text:'EssenceLab 仅用于学习、研究和非营利性娱乐，不用于任何商业目的。本项目为独立的同人项目，并非《第五人格》官方网站。图片、音频及商标的权利归各自权利人所有。'}
];

export function installSiteNotice(){
 const button=document.getElementById('site-info-button'),banner=document.getElementById('site-info-banner'),text=document.getElementById('site-info-text');
 let index=0,reducedTimer;
 function showMessage(){
  const message=siteNotices[index];text.lang=message.lang;text.textContent=message.text;
  text.style.animation='none';
  const width=banner.querySelector('.site-info-window').clientWidth;
  text.style.setProperty('--notice-start',width+'px');
  text.style.setProperty('--notice-duration',Math.max(12,(text.scrollWidth+width)/48)+'s');
  void text.offsetWidth;text.style.animation='';
  clearTimeout(reducedTimer);
  if(matchMedia('(prefers-reduced-motion:reduce)').matches)reducedTimer=setTimeout(nextMessage,18000);
 }
 function nextMessage(){if(!banner.hidden){index=(index+1)%siteNotices.length;showMessage();}}
 function close(){clearTimeout(reducedTimer);banner.hidden=true;button.setAttribute('aria-expanded','false');}
 button.addEventListener('click',()=>{if(!banner.hidden){close();return;}index=0;banner.hidden=false;button.setAttribute('aria-expanded','true');showMessage();});
 text.addEventListener('animationend',nextMessage);
 document.getElementById('site-info-close').addEventListener('click',close);
 document.addEventListener('keydown',event=>{if(event.key==='Escape')close();});
 document.addEventListener('pointerdown',event=>{if(!banner.hidden&&!banner.contains(event.target)&&!button.contains(event.target))close();});
}
