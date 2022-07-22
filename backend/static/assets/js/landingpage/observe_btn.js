const observeBtn = document.querySelector('.observe-div');
const disabledBtn = document.querySelector('.main__btn');

function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function changeVisibility(){
    disabledBtn.classList.remove('d-flex');
    disabledBtn.classList.add('d-none');
}

document.addEventListener('scroll', (event) => {
    console.log(isInViewport(observeBtn) && disabledBtn.classList.contains('d-flex') && disabledBtn.style.getPropertyValue('opacity') === '0')
    if (!isInViewport(observeBtn) && disabledBtn.classList.contains('d-none')){
        disabledBtn.classList.remove('d-none');
        disabledBtn.classList.add('d-flex');
        disabledBtn.style.zIndex = 100;
        disabledBtn.style.opacity = 1;
        disabledBtn.animate([
            {opacity:0},
            {opacity:0.25},
            {opacity:0.5},
            {opacity:0.75},
            {opacity:1},
        ],
             {duration:2000, fill: 'forwards'}
        )
    } else if (isInViewport(observeBtn) && disabledBtn.classList.contains('d-flex') && disabledBtn.style.getPropertyValue('opacity') === '1'){
        console.log('odpalam')
        const animate = disabledBtn.animate([
            {opacity:1},
            {opacity:0.75},
            {opacity:0.5},
            {opacity:0.25},
            {opacity:0, display: 'none'},
        ],
             {duration:300}
        )
        const myTimeout = setTimeout(changeVisibility, 400);

    }
});

