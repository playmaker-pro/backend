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

    if (!dom.value){
        urlSearchParams.delete(nameOfParam, dom.value)
    } else {
        urlSearchParams.set(nameOfParam, dom.value);
    }
    window.history.pushState("", "", `?${urlSearchParams}`);
}

const dropdownParams = (dom, nameOfParam) =>{
    
    urlSearchParams = new URLSearchParams(window.location.search);
    const selected = dom.parentElement.querySelectorAll('.dropdown-menu .show .dropdown-item.selected');

    let newEl = [];

    selected.forEach(element => {
        newEl.push(element.innerText)
    })

    if ((nameOfParam == 'leg' && newEl[0] == '----') || selected.length == 0){
        urlSearchParams.delete(nameOfParam, newEl)
    } else {
        urlSearchParams.set(nameOfParam, newEl);   
    }
    window.history.pushState("", "", `?${urlSearchParams}`);
    
}

getNameFilter.addEventListener('input', () => {
    inputParams(getNameFilter, 'first_last')
})

minYear.addEventListener('input', () => {
    inputParams(minYear, 'year_min')
})

maxYear.addEventListener('input', () => {
    inputParams(maxYear, 'year_max')
})


getLeague.addEventListener('change', () =>{
    dropdownParams(getLeague, 'league');
})

vivo.addEventListener('change', () =>{
    dropdownParams(vivo, 'vivo');
})

possition.addEventListener('change', () => {
    dropdownParams(possition, 'position');
})

leg.addEventListener('change', ()=> {
    dropdownParams(leg, 'leg')
})


const foreignAndJuniorURLS = link => {

    urlSearchParams = new URLSearchParams(window.location.search);
    const actualPath = window.location.pathname;

    let params = '?';
    for (let [param, value] of urlSearchParams.entries()){
        if (value){
            value.split(',').forEach(element => {
                params += `${param}=${element}&`
            })
        }
    }

    let newUrl = '';

    newUrl = link.trim() + params;
    console.log(newUrl)
    window.location.href = newUrl;
}
