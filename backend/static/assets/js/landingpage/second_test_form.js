const secondFormBtn = document.querySelector('.second__form__btn');
const secondFormVideos = document.querySelector('.video__section textarea');
const secontFormComment = document.querySelector('.form__section .extra__comment');
const secondFormTextArea = document.querySelector('.form__section textarea');

secondFormTextArea.addEventListener('input', () => {
    changeBtn(secondFormTextArea)
})

secontFormComment.addEventListener('input', () => {
    changeBtn(secontFormComment)
})

const changeBtn = element => {
    let secondFormTextAreaValue = element.value

    if (secondFormTextAreaValue){
        secondFormBtn.style.backgroundColor = 'Black';
        secondFormBtn.style.color = 'White';
        secondFormBtn.removeAttribute('disabled')

    } else {
        secondFormBtn.style.backgroundColor = '#EBEDF0';
        secondFormBtn.style.color = 'rgba(20, 20, 20, 0.24)';
        secondFormBtn.setAttribute('disabled', '')
    }
}


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

if(secondFormBtn){
    secondFormBtn.addEventListener('click', e => {
        e.preventDefault();

        const data = {
            videos: secondFormVideos.value,
            comment: secontFormComment.value,
            user: user
        }

        const url_path = window.location.pathname.split('/')
        const url = `/landingpage/test-form/${url_path[url_path.length-2]}/`

        fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                csrfmiddlewaretoken: getCookie('csrftoken'),
            },
            body: JSON.stringify(
                data
            )
        })
        .then(response => response.json())
        .then(data => {
            if(data.success){
                window.location.href = '/landingpage/we-got-it-success/'
            } else{
                showToastErrorRedMessage('Coś poszło nie tak. Spróbuj ponownie później');
            }
        })
    })
}
