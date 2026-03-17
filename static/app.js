let words=[]
let index=0
let flipped=false
let correct=0
let wrong=0


async function loadThemes(){

const r = await fetch("/themes")
const data = await r.json()

const box = document.getElementById("themes")

if(!box) return

if(data.length===0){

box.innerHTML = '<div style="opacity:.6;text-align:center;padding:20px">Noch keine Module</div>'
return
}

let html=""

for(const t of data){

html += `
<div class="topic" style="display:flex;justify-content:space-between;align-items:center">

<div>

<div style="font-size:18px;font-weight:600">
${t.name}
</div>

<div style="opacity:.7;font-size:14px;margin-top:3px">
${t.count} Wörter im Modul
</div>

</div>

<div style="display:flex;gap:8px">

<button class="small" onclick="start('${t.name}')">lernen</button>

<button class="small" onclick="deleteTheme('${t.file}')">x</button>

</div>

</div>
`
}

box.innerHTML = html

}



async function deleteTheme(file){

await fetch("/delete/"+file,{method:"DELETE"})
loadThemes()

}



function start(name){

window.location.href="/static/learn.html?m="+name

}



function speak(){

const text=document.getElementById("card").innerText

let lang=flipped?"ru":"de"

const voices=speechSynthesis.getVoices()

let voice=null

for(let v of voices){

if(lang==="de" && v.lang.toLowerCase().includes("de")){
voice=v
break
}

if(lang==="ru" && v.lang.toLowerCase().includes("ru")){
voice=v
break
}

}

const u=new SpeechSynthesisUtterance(text)

if(voice){
u.voice=voice
u.lang=voice.lang
}else{
u.lang=lang==="de"?"de-DE":"ru-RU"
}

u.rate=1

speechSynthesis.cancel()
speechSynthesis.speak(u)

}



async function startLearning(name){

const r = await fetch("/words/"+name+".json")

words = await r.json()

index=0
correct=0
wrong=0
flipped=false

document.getElementById("themesView").classList.add("hidden")
document.getElementById("learnView").classList.remove("hidden")

render()

}



function render(){

const w = words[index]

document.getElementById("card").innerText =
flipped ? w.ru : w.de

document.getElementById("stats").innerHTML =
`<div style="display:flex;justify-content:space-between;width:100%">
<div>${index+1} / ${words.length}</div>
<div>✔ ${correct} &nbsp;&nbsp; ✖ ${wrong}</div>
</div>`

}



function flip(){
flipped=!flipped
render()
}



function correctWord(){
correct++
next()
}



function wrongWord(){
wrong++
next()
}



function next(){

if(index < words.length-1){

index++
flipped=false
render()

}else{

document.getElementById("learnView").innerHTML = `
<div class="panel" style="text-align:center">
<h2>Modul abgeschlossen</h2>
<p>✔ ${correct} richtig</p>
<p>✖ ${wrong} falsch</p>
<button onclick="location.reload()">zurück</button>
</div>
`

}

}



function prevCard(){

if(index>0){
index--
render()
}

}
