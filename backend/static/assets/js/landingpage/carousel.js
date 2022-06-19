const cards = document.querySelectorAll('.carousel_item_desktop');
const getCarouselWrapper = document.querySelector('.slideshow_container_main_desktop');
const carouselConstrolPrev = document.querySelector('.carousel-control-prev');
const caourselConstrolNext = document.querySelector('.carousel-control-next');
const howItWorksControlPrev = document.querySelector('#how_it_works .carousel-control-prev')
const howItWorksControlNext = document.querySelector('#how_it_works .carousel-control-next')
const howItWorkCards = document.querySelector('#how_it_works .slideshow_container_main_desktop')


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
