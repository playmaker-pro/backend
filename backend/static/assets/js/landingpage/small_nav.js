// const anchors = document.querySelectorAll('.second__navbar_fixed a');
//
// anchors.forEach(anchor => {
//     anchor.addEventListener('click', function (e) {
//
//         const pElements = document.querySelectorAll('.second__navbar_fixed p');
//         pElements.forEach(element =>{
//             element.classList.remove('active__border')
//         })
//
//         anchor.querySelector('p').classList.add('active__border');
//
//         e.preventDefault();
//         console.log('klikam', anchor)
//         const element = document.querySelector(this.getAttribute('href'));
//         const dims = element.getBoundingClientRect();
//         dims.y = dims.y -200;
//         window.scrollTo(window.scrollX, window.scrollY - 500);
//     });
// })