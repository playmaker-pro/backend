/**

 Change value of paginate dropdown when button is clicked

 */

const dropdownList = [10, 25, 50, 100]
const dropdown = document.querySelectorAll('.total-ann .btn-group');
const dropdownCustom = document.querySelectorAll('.dropdown-custom .dropdown-item')

let num;

dropdownCustom.forEach(element => {
    element.addEventListener('click', ()=> {
        urlSearchParams = new URLSearchParams(window.location.search);
        element = element.querySelector('span');
        console.log(element.innerText)
        if (!element.innerText){
            urlSearchParams.delete('total_items')
        } else {
            console.log('jestem w elsie')
            urlSearchParams.set('total_items', element.innerText);
        }

        window.history.pushState("", "", `?${urlSearchParams}`);

        // inputParams(element, 'total_items');
        window.location.reload()
    })
})

num = get_urls_params().get('total_items');

if(num){
   const newArr = dropdownList.filter(element => {if(element !== +num) {return element}})
    document.querySelector('.total-ann .dropdown-btn a').innerHTML = num;
    newArr.forEach((element, index) => {

    if(element !== +num){
        console.log(element, num, index)
        try{
            const dropdownA = document.querySelector(`[data-${index+1}="${index+1}"]`);
            console.log(dropdownA)
            dropdownA.innerHTML = element +'';

            // dropdownA.href = `${window.location.pathname}?total_items=${element}`
            dropdownA.addEventListener('click', ()=> {

            })
        } catch (e){}

        }
    })
}

/**

 catch value of input redirecting to specific paginate page

 */

const paginatePage = document.querySelector('.paginate-page');

if(paginatePage){
    paginatePage.addEventListener('input', ()=> {
        inputParams(paginatePage, 'page')
    })

    const goToSite = document.querySelector('.go-to-site')
    goToSite.addEventListener('submit', (e)=> {
        console.log(window.location)
        e.preventDefault()
        window.location.reload()
})
}
