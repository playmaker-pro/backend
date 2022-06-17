// let indicators = document.querySelectorAll('.carouselDesktopIndicators');
const cards = document.querySelectorAll('.carousel_item_desktop');
// const getIndicatorParent = document.querySelector('.slideshow_container_desktop .carousel-indicators');
// getIndicatorParent.innerHTML = '';
const carouselItem = document.querySelectorAll('.carousel_item_desktop');
const getCarouselWrapper = document.querySelector('.slideshow_container_main_desktop');
const carouselConstrolPrev = document.querySelector('.carousel-control-prev');
const caourselConstrolNext = document.querySelector('.carousel-control-next');
const howItWorksControlPrev = document.querySelector('#how_it_works .carousel-control-prev')
const howItWorksControlNext = document.querySelector('#how_it_works .carousel-control-next')
const howItWorkCards = document.querySelector('#how_it_works .slideshow_container_main_desktop')

const carouselFirstRange = window.matchMedia('(max-width: 500px)');
const carouselSecondRange = window.matchMedia('(max-width: 700px) and (min-width: 501px');
const carouselThirdRange = window.matchMedia('(max-width: 900px) and (min-width: 701px)');
const carouselFourthRange = window.matchMedia('(max-width: 1200px) and (min-width: 901px)');
const carouselFifthRange = window.matchMedia('(min-width: 1201px)');

const carouselRanges = [carouselFirstRange, carouselSecondRange, carouselThirdRange, carouselFourthRange, carouselFifthRange]


// carouselRanges.forEach(element =>{
//   element.addEventListener('change', function (mq) {
//     checkCarouselWitdh()
// })
// })

const createDotElements = slide => {
    getIndicatorParent.insertAdjacentHTML('beforeend',
        `<li class="carouselDesktopIndicators" data-slide-to="${slide}"></li>`
    );
}

function checkCarouselWitdh(){
  if (carouselFirstRange.matches) {
        getIndicatorParent.innerHTML = '';
        carouselItem.forEach(element =>{
            element.style.minWidth = '80vw'
        });

        cards.forEach((element, count) =>{
            createDotElements(count);
            if(isInViewport(element)){
                const colourDot = document.querySelector(`[data-slide-to="${count}"]`);
                colourDot.classList.add('active')

            }
        })
  }

  else if (carouselSecondRange.matches){

        getIndicatorParent.innerHTML = '';
        carouselItem.forEach(element =>{
            // element.style.minWidth = '50vw'
        });
        for(let i = 1; i <= cards.length/2; i++){
            createDotElements(i)
        }
        getCarouselWrapper.classList.add('d-flex');

  }
  else if (carouselThirdRange.matches){
       carouselItem.forEach(element =>{
            // element.style.minWidth = '40vw'
        })
        // getCarouselWrapper.classList.add('d-flex');
       // getCarouselWrapper.classList.remove('d-flex');
       //  getCarouselWrapper.style.display = 'grid';
       //  getCarouselWrapper.style.gridTemplateColumns = 'repeat(3, 3fr)'

  }
    else if (carouselFourthRange.matches){
        carouselItem.forEach(element =>{
            // element.style.minWidth = '30vw'
        })
        // getCarouselWrapper.classList.add('d-flex');


    }
    else if(carouselFifthRange.matches || carouselFourthRange.matches){
        carouselItem.forEach(element =>{
            // element.style.minWidth = '20vw'
        });
        // getCarouselWrapper.classList.remove('d-flex');
        // getCarouselWrapper.style.display = 'grid';
        // getCarouselWrapper.style.gridTemplateColumns = 'repeat(3, 3fr)'
  }
    else{
        carouselItem.forEach(element =>{
            // element.style.minWidth = '80vw'
        });
        // getCarouselWrapper.classList.add('d-flex');

  }
}

function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        // rect.top >= 0 &&
        rect.left >= 0 &&
        // rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}


// checkCarouselWitdh()

// carouselConstrolPrev.addEventListener('click', ()=> {
//     console.log('klikam')
//     if (carouselFirstRange.matches || carouselSecondRange.matches) {
//         const getActiveCard = document.querySelector('.active__card');
//         const cardNum = +getActiveCard.dataset.target;
//
//         if(cardNum > 1 ) {
//             const getPreviousCard = document.querySelector(`[data-target="${cardNum - 1}"]`);
//                 getPreviousCard.classList.add('active__card');
//             //     getPreviousCard.classList.remove('d-none')
//                 getActiveCard.classList.remove('active__card');
//             //     getActiveCard.classList.add('d-none')
//             // }
//             getCarouselWrapper.scrollLeft -= 350;
//             const indicators = document.querySelectorAll('.carouselDesktopIndicators');
//             indicators.forEach(element => {
//                 // console.log(element)
//                 element.classList.remove('active')
//
//             })
//
//             cards.forEach((element, count) => {
//                 if (isInViewport(element)) {
//                     console.log(element, count)
//
//                     const colourDot = document.querySelector(`[data-slide-to="${count - 1}"]`);
//                     colourDot.classList.add('active')
//                 }
//             })
//         }
//   }
//   else if (carouselThirdRange.matches){
//
//
//   }
//   else if (carouselFourthRange.matches){
//
//   }
//   else if(carouselFifthRange.matches){
//
//   }
//   else{
//
//   }
// })


// caourselConstrolNext.addEventListener('click', ()=> {
//
//
//     if (carouselFirstRange.matches || carouselSecondRange.matches) {
//         const getActiveCard = document.querySelector('.active__card');
//         const cardNum = +getActiveCard.dataset.target;
//
//         console.log('cards num', cardNum)
//
//         if(cardNum < cards.length ) {
//                 const getNextCard = document.querySelector(`[data-target="${cardNum+1}"]`);
//                 console.log(getNextCard)
//                 getNextCard.classList.add('active__card');
//             //     getNextCard.classList.remove('d-none')
//                 getActiveCard.classList.remove('active__card');
//             //     getActiveCard.classList.add('d-none')
//             // }
//
//             getCarouselWrapper.scrollLeft += 350;
//             const indicators = document.querySelectorAll('.carouselDesktopIndicators');
//             indicators.forEach(element => {
//                 // console.log(element)
//                 element.classList.remove('active')
//
//             })
//
//             for (let i = 1; i <= cards.length; i++) {
//                 // console.log(cards[i - 1])
//                 if (isInViewport(cards[i - 1])) {
//                     const colourDot = document.querySelector(`[data-slide-to="${i}"]`);
//                     colourDot.classList.add('active')
//                 }
//             }
//         }
//
//         // cards.forEach((element, count) => {
//         //     if (isInViewport(element)){
//         //        // console.log(element, count)
//         //
//         //         const colourDot = document.querySelector(`[data-slide-to="${count + 1}"]`);
//         //         colourDot.classList.add('active')
//         //     }
//         // })
//   }
//   else if (carouselThirdRange.matches){
//
//
//   }
//   else if (carouselFourthRange.matches){
//
//   }
//   else if(carouselFifthRange.matches){
//
//   }
//   else{
//
//   }
// })


carouselConstrolPrev.addEventListener('click', ()=>{
    getCarouselWrapper.scrollLeft -= 350
})

caourselConstrolNext.addEventListener('click', ()=>{
    getCarouselWrapper.scrollLeft += 350
})

howItWorksControlPrev.addEventListener('click', ()=>{
    howItWorkCards.scrollLeft -= 350
})

howItWorksControlNext.addEventListener('click', ()=>{
    howItWorkCards.scrollLeft += 350
})

//Scroll right/ left for desktop

// const scrollRightBtn = document.querySelector('.scroll__right');
// const scrollLeftBtn = document.querySelector('.scroll__left');
//
// scrollRightBtn.addEventListener('click', ()=> {
//
//     const scrollElement = document.querySelector('.slideshow_container_main_second')
//     scrollElement.style.marginLeft = '-15rem'
// })
//
// scrollLeftBtn.addEventListener('click', ()=> {
//
//     const scrollElement = document.querySelector('.slideshow_container_main_second')
//     scrollElement.style.marginLeft = '0'
// })