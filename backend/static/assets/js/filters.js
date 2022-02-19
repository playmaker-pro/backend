// push params to url in filter page

const getNameFilter = document.querySelector('[name="first_last"]')
const getLeague = document.querySelector('[title="rozgrywki"]');
const vivo = document.querySelector('[name="vivo"]');
const possition = document.querySelector('[title="pozycja"]');
const leg = document.querySelector('[title="noga"]');
const minYear = document.querySelector('[name="year_min"]');
const maxYear = document.querySelector('[name="year_max"]');


let urlSearchParams = new URLSearchParams(window.location.search);


const inputParams = (dom, nameOfParam) => {
    urlSearchParams = new URLSearchParams(window.location.search);
    urlSearchParams.set(nameOfParam, dom.value);
    window.history.pushState("", "", `?${urlSearchParams}`);
}

const dropdownParams = (dom, nameOfParam) =>{
    
    urlSearchParams = new URLSearchParams(window.location.search);
    const selected = dom.parentElement.querySelectorAll('.dropdown-menu .show .dropdown-item.selected');

    let newEl = [];

    selected.forEach(element => {
        newEl.push(element.innerText)
    })

    urlSearchParams.set(nameOfParam, newEl);
    window.history.pushState("", "", `?${urlSearchParams}`);
}

if(getNameFilter){
    getNameFilter.addEventListener('input', () => {
        inputParams(getNameFilter, 'first_last')
    })    
}

if(minYear){
    minYear.addEventListener('input', () => {
        inputParams(minYear, 'year_min')
    })
}

if(maxYear){
    maxYear.addEventListener('input', () => {
        inputParams(maxYear, 'year_max')
    })
}

if(getLeague){
    getLeague.addEventListener('change', () =>{
        dropdownParams(getLeague, 'league');
    })
}

if(vivo){
    vivo.addEventListener('change', () =>{
        dropdownParams(vivo, 'vivo');
    })    
}

if(possition){
    possition.addEventListener('change', () => {
        dropdownParams(possition, 'position');
    })
}

if(leg){
    leg.addEventListener('change', ()=> {
        dropdownParams(leg, 'leg')
    })
}

const foreignAndJuniorURLS = link => {
    // window.location.href
    urlSearchParams = new URLSearchParams(window.location.search);
    let params = '?';
    for (let [param, value] of urlSearchParams.entries()){
        value.split(',').forEach(element => {
            params += `${param}=${element}&`
        })
    }
    let newUrl = link.trim() + params;
    window.location.href = newUrl;
}
