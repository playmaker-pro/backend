const nav = document.querySelector('.navbar');
const playA = nav.querySelector('.logo a');
const hamburger = document.querySelector('.hamburger__icons');
const hambList = hamburger.querySelectorAll('rect');
const scrollContainer = document.querySelector(".second__navbar_fixed");


window.onscroll = function () {
    "use strict";
    if (document.body.scrollTop >= 1000 || document.documentElement.scrollTop >= 700 ) {

        nav.classList.remove('dark__background');
        nav.classList.add('white__background');
        document.querySelector('#header').classList.remove('dark__background');
        document.querySelector('#header').classList.add('white__background')
        document.querySelector('.navbar-collapse').classList.remove('dark__background');
        document.querySelector('.navbar-collapse').classList.add('white__background');
        const liElements = document.querySelectorAll('#header .navbar-nav .nav-item a');

        liElements.forEach(element => {
            element.style.color = '#141414';
        })
        if(document.querySelector('.view-logo')){
            document.querySelector('.view-logo').style.filter = 'invert(1)'
        }
        if(document.querySelector('.email-logo')){
            document.querySelector('.email-logo').style.filter = 'invert(1)'
        }
        try{
            document.querySelector('.menu__dropdown .dropdown-menu').style.backgroundColor = '#FFFFFF'
            document.querySelector('#header .dropdown-menu a').style.color = '#141414'

            document.querySelector('.nav-item .dropdown-menu').style.backgroundColor = '#FFFFFF'
        }catch(e){
        }

        playA.classList.add('color__change');

        hambList.forEach(element => {
            element.style.fill = 'black'
        })

    }
    else {
        nav.classList.add('dark__background');
        nav.classList.remove('white__background');

        playA.classList.remove('color__change');

        hambList.forEach(element => {
            element.style.fill = 'white'
        })

        document.querySelector('#header').classList.add('dark__background');
        document.querySelector('#header').classList.remove('white__background')
        document.querySelector('.navbar-collapse').classList.add('dark__background');
        document.querySelector('.navbar-collapse').classList.remove('white__background');
        const liElements = document.querySelectorAll('#header .navbar-nav .nav-item a');

        liElements.forEach(element => {
            element.style.color = 'white';
        })

        if(document.querySelector('.view-logo')){
            document.querySelector('.view-logo').style.filter = 'none'
        }
        if(document.querySelector('.email-logo')){
            document.querySelector('.email-logo').style.filter = 'none'
        }

        try{
            document.querySelector('.menu__dropdown .dropdown-menu').style.backgroundColor = '#141414'
            document.querySelector('#header .dropdown-menu a').style.color = '#FFFFFF'
            document.querySelector('.nav-item .dropdown-menu').style.backgroundColor = '#141414'
        }catch(e){}

    }
};
