(function(){
  'use strict';
  // Optional manual light/dark switch; without a stored choice the system setting applies.
  var root=document.documentElement,key='pnh-theme',stored=null;
  try{stored=localStorage.getItem(key);}catch(e){}
  if(stored==='light'||stored==='dark')root.setAttribute('data-theme',stored);
  function dark(){var t=root.getAttribute('data-theme');return t?t==='dark':!!(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);}
  function sync(button){button.setAttribute('aria-pressed',String(dark()));}
  function init(){
    var button=document.getElementById('theme-toggle');if(!button)return;sync(button);
    button.addEventListener('click',function(){var next=dark()?'light':'dark';root.setAttribute('data-theme',next);try{localStorage.setItem(key,next);}catch(e){}sync(button);});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
