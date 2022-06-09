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
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)===' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

const formBtn = document.querySelector('.user_is_authenticated');
const sendForm = (url, data) => {

        fetch(url, {
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
formInput.addEventListener('click', ()=>{
    clearAtributes()
})

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

        const url = '/landingpage/test-form/';
        const result = {
            leagues: leagues,
            distance: distance[0],
            city: getCity,
            user: user
        }

        sendForm(url, result)

    } else if(!getCity){

        addAtributes()

    } else {
        showToastErrorRedMessage('Coś poszło nie tak. Spróbuj ponownie później');
    }
})