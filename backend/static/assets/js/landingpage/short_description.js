const maxSize = window.matchMedia('(max-width: 470px) and (min-width: 431px)');
const maxSize2 = window.matchMedia('(max-width: 430px) and (min-width: 395px');
const maxSize3 = window.matchMedia('(max-width: 396px) and (min-width: 370px)');
let secondNav = document.querySelector('.second__navbar span:last-child')
const baseText = document.querySelector('.second__navbar span:last-child').innerText

const sizesArr = [maxSize, maxSize2, maxSize3]

sizesArr.forEach(element =>{
  element.addEventListener('change', function (mq) {
    checkWidth()
})
})

function checkWidth(){

  if (maxSize.matches) {
    secondNav.innerText = baseText;
    secondNav.innerText = secondNav.innerText.slice(0, secondNav.innerText.length - 6) + '...'
  } else if (maxSize2.matches){
    secondNav.innerText = baseText;
    secondNav.innerText = secondNav.innerText.slice(0, secondNav.innerText.length - 12) + '...'
  }else if (maxSize3.matches){
    secondNav.innerText = baseText;
    secondNav.innerText = secondNav.innerText.slice(0, secondNav.innerText.length - 16) + '...'
  }else{
    secondNav.innerText = baseText
  }
}


checkWidth()