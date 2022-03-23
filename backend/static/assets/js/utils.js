const inputParams = (dom, nameOfParam) => {

    urlSearchParams = new URLSearchParams(window.location.search);

    if (!dom.value){
        urlSearchParams.delete(nameOfParam, dom.value)
    } else {
        urlSearchParams.set(nameOfParam, dom.value);
    }
    window.history.pushState("", "", `?${urlSearchParams}`);
}

function get_urls_params(){
    const queryString = window.location.search;
    return new URLSearchParams(queryString)
}