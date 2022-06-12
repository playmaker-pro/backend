const getLeagueDivs = document.querySelectorAll('.choose__league ');
const dinstanceDivs = document.querySelectorAll('.choose__distance');

getLeagueDivs.forEach(element => {
    element.addEventListener('click', () =>{

        let counter = 0;

        getLeagueDivs.forEach(element =>{
            if(element.classList.contains('league__active')){
                counter += 1;
            }
        })

        if (counter < 2 && !element.classList.contains('league__active')){
           element.classList.add('league__active')

        } else if(counter ===2 && element.classList.contains('league__active')){

            element.classList.remove('league__active');

        } else if(counter ===2 && !element.classList.contains('league__active')) {

            const formDiv = document.querySelector('.leagues__form .form__error');

            formDiv.classList.remove('d-none')
            formDiv.classList.add('error__form');

            setTimeout(() => {
                formDiv.classList.add('d-none')
            }, 5000)
        }
    })
})

dinstanceDivs.forEach(element => {
    element.addEventListener('click', () =>{

        let counter = 0;

        dinstanceDivs.forEach(element =>{
            if(element.classList.contains('distance__active')){
                counter += 1;
            }
        })

        if (counter < 1 && !element.classList.contains('distance__active')){
           element.classList.add('distance__active')

        } else if(counter === 1 && element.classList.contains('distance__active')){

            element.classList.remove('distance__active');

        } else if(counter === 1 && !element.classList.contains('distance__active')) {

            const formDiv = document.querySelector('.distance__form .form__error');

            formDiv.classList.remove('d-none')
            formDiv.classList.add('error__form');

            setTimeout(() => {
                formDiv.classList.add('d-none')
            }, 5000)
        }
    })
})

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const formBtn = document.querySelector('.user_is_authenticated');
const sendForm = (url, data) => {

     return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                csrfmiddlewaretoken: getCookie('csrftoken'),
            },
            body: JSON.stringify(
                data
            )
        })
}

const clearAtributes = () => {

    const inputForm =  document.querySelector('.form__input input');

    inputForm.style.setProperty("--c", "");
    inputForm.style.background = '#EBEDF0';
    inputForm.style.border = '1px solid rgba(20, 20, 20, 0.48)';

    const errorMessage = document.querySelector('.error_message_form');

    errorMessage.classList.add('d-none');
    errorMessage.classList.remove('error__form');


    document.querySelector('.form__input img').classList.add('d-none')
}

const formInput = document.querySelector('.form__input input');

if (formInput){
    formInput.addEventListener('click', ()=>{
        clearAtributes()
    })
}

const addAtributes = () => {
    const inputForm =  document.querySelector('.form__input input');
    inputForm.style.setProperty("--c", "#F2183D");
    inputForm.style.background = 'rgba(240, 14, 14, 0.08)';
    inputForm.style.border = '1px solid #F00E0E';
    const errorMessage = document.querySelector('.error_message_form');
    errorMessage.classList.remove('d-none');
    errorMessage.classList.add('error__form');

        setTimeout(() => {
            errorMessage.classList.add('d-none')
        }, 5000)

    document.querySelector('.form__input img').classList.remove('d-none')
}

if(formBtn){
    formBtn.addEventListener('click', (e) => {

        e.preventDefault();

        let leagues = [];

        const getLeagues = document.querySelectorAll('.leagues__form .league__active');
        getLeagues.forEach(element => {
            leagues.push(element.querySelector('p').innerText)
        })

        let distance = [];
        const getDistance = document.querySelectorAll('.distance__form .distance__active');

        getDistance.forEach(element => {
            distance.push(element.querySelector('p').innerText)
        })

        const getCity = document.querySelector('.form__input input').value;

        if (getCity && distance.length === 1 && leagues.length >= 1) {

            const url = '/landingpage/test-form/1/';
            const result = {
                leagues: leagues,
                distance: distance[0],
                city: getCity,
                user: user
            }

            sendForm(url, result)
                .then(response => response.json())
                .then(data => {
                    if(data.success){
                         window.location.href = `/landingpage/we-got-it/${data.success}`
                    }
                })

        } else if(!getCity){

            addAtributes()

        } else {
            showToastErrorRedMessage('Coś poszło nie tak. Spróbuj ponownie później');
        }
    })
}

