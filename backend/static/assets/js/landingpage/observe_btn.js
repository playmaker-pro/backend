const observeBtn = document.querySelector('.observe-div');
const disabledBtn = document.querySelector('.main__btn');
let testReadyBtn = document.querySelector('.ready_for_tests_unauthenticated a');

const btnAuthenticated = document.querySelector('#test__section .user_is_authenticated')

testReadyBtn = testReadyBtn ?? btnAuthenticated

function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= -100 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

document.onscroll = function() {

    const hiddenElementRangeStart = window.scrollY + disabledBtn.getBoundingClientRect().top;
    const TestReadyTop = window.scrollY + testReadyBtn.getBoundingClientRect().top;

    if(hiddenElementRangeStart >= TestReadyTop || window.scrollY < 590){
        disabledBtn.classList.remove('main__btn__toggle');
        testReadyBtn.style.visibility = "visible"
    }
    else if (window.scrollY >= 590 && !disabledBtn.classList.contains('main__btn__toggle') && window.scrollY <= 1000){
        testReadyBtn.style.visibility = "hidden"
        disabledBtn.classList.add('main__btn__toggle');
        disabledBtn.animate([
            {opacity:0},
            {opacity:0.25},
            {opacity:0.5},
            {opacity:0.75},
            {opacity:1},
        ],
             {duration:800}
        )
    }
    else{
        testReadyBtn.style.visibility = "hidden"
        disabledBtn.classList.add('main__btn__toggle');
    }

};

// the callback function to be provided to the IntersectionObserver;
// entries: an Array of IntersectionObserverEntries,
// o: a reference to the options Object passed to the IntersectionObserver:
function toggle(entries, o) {

  // finding the relevant element:
    console.log('observer')
    console.log('!entries[0].isIntersecting', !entries[0].isIntersecting)

    if (!entries[0].isIntersecting){
        disabledBtn.classList.add('main__btn__toggle');
        disabledBtn.animate([
            {opacity:0},
            {opacity:0.25},
            {opacity:0.5},
            {opacity:0.75},
            {opacity:1},
        ],
             {duration:800}
        )
    } else {
        disabledBtn.classList.remove('main__btn__toggle');

    }

  // disabledBtn
  //
  //   // updating its class-name, adding the 'inViewport' class
  //   // if entries[0].isIntersecting is true (the observed
  //   // element is in the viewport) or removing the class if
  //   // entries[0].isIntersecting is false (the observed element
  //   // is not in the viewport):
  //   .classList.toggle('main__btn__toggle', entries[0].isIntersecting);

}

// initialising the IntersectionObserver, and assigning the
// handler function:
// let observer = new IntersectionObserver(toggle);
//
// // specifying which element the IntersectionObserver should
// // observe:
// observer.observe(observeBtn);
//
