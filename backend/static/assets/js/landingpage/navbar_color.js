const nav = document.querySelector('.navbar');
const playA = nav.querySelector('.logo a');
const loginBtn = nav.querySelector('.login_btn');
const hamburger = document.querySelector('.hamburger__icons');
const hambList = hamburger.querySelectorAll('rect');

window.onscroll = function () {
    "use strict";
    if (document.body.scrollTop >= 1500 || document.documentElement.scrollTop>= 1500 ) {

        nav.classList.remove('dark__background');
        nav.classList.add('white__background');

        playA.classList.add('color__change');
        loginBtn.classList.add('login-btn__change');

        hambList.forEach(element => {
            element.style.fill = 'black'
        })

    }
    else {
        nav.classList.add('dark__background');
        nav.classList.remove('white__background');

        playA.classList.remove('color__change');
        loginBtn.classList.remove('login-btn__change');

        hambList.forEach(element => {
            element.style.fill = 'white'
        })

    }
};


const scrollContainer = document.querySelector(".second__navbar_fixed");

scrollContainer.addEventListener('wheel', (event) => {
  event.preventDefault();

  element.scrollBy({
    left: event.deltaY < 0 ? -30 : 30,

  });
});

let slideIndex = 1;
currentSlide(slideIndex);

// Next/previous controls
function plusSlides(n) {
  currentSlide(slideIndex += n);
}


function currentSlide(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");

  if (n > slides.length) {slideIndex = 1}
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    // slides[i].style.display = "none";
  }
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";
  dots[slideIndex-1].className += " active";
}
