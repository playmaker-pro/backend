/**

 Change value of paginate dropdown when button is clicked

 */

const dropdownList = [10, 25, 50, 100]
const dropdown = document.querySelectorAll('.total-ann .btn-group');

function get_urls_params(){
    const queryString = window.location.search;
    return new URLSearchParams(queryString)
}

let num;


num = get_urls_params().get('total_items');

if(num){
   const newArr = dropdownList.filter(element => {if(element !== +num) {return element}})
    document.querySelector('.total-ann .dropdown-btn a').innerHTML = num;
    newArr.forEach((element, index) => {
    if(element !== +num){
        console.log(element, num, index)
        const dropdownA = document.querySelector(`[data-${index+1}="${index+1}"]`);
        dropdownA.innerHTML = element +'';

        const urlPath =

        dropdownA.href = `${window.location.pathname}?total_items=${element}`
        }
    })
}
