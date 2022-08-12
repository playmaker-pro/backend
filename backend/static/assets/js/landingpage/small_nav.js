const anchors = document.querySelectorAll('.second__navbar_fixed a');

anchors.forEach(anchor => {
    anchor.addEventListener('click', function (e) {

        const pElements = document.querySelectorAll('.second__navbar_fixed p');
        pElements.forEach(element =>{
            element.classList.remove('active__border')
        })

        anchor.querySelector('p').classList.add('active__border');

        // Scroll up 120px to clicked div.
        const getElement = document.querySelector(anchor.dataset.href)
        const newY = getElement.getBoundingClientRect().top + window.scrollY - 120;
        window.scrollTo({top: newY, behavior: 'smooth'});
    });
})