function dropdown_functionality() {
    document.getElementById('index-container').addEventListener('mouseover', ev => {
        document.getElementById('index-dropdown-content').style.display = 'block';
    })
    document.getElementById('index-container').addEventListener('mouseout', ev => {
        document.getElementById('index-dropdown-content').style.display = 'none';
    })
}

function search_functionality() {
    let search = document.getElementById('search-input')
    if (search != null) {
        search.addEventListener('keypress', ev => {
            if (ev.key === 'Enter') {
                ev.preventDefault()
                let username = search.value
                search.value = ''
                search_request(username)
            }
        })
    }
}

function search_request(username) {
    let URL = '/profile/search/'
    let post_data = {
        'username': username
    }

    fetch(URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'post_data': post_data})
    })
        .then(response => {
            return response.json()
        })
        .then(data => {
            if (JSON.parse(data['status']) === 200) {
                window.location.href = JSON.parse(data['content'])['redirect_url']
            } else if (JSON.parse(data['status']) === 204) {
                let search = document.getElementById('search-input')
                search.placeholder = 'No such user found'
                search.style.borderColor = 'red'

            } else {
                alert(JSON.parse(data['content'])['error'])
            }
        })
}

function make_header_margin() {
    let header_height = document.getElementById('header').offsetHeight;
    document.getElementById('main').style.marginTop = Math.ceil(header_height * 1.01).toString() + 'px';

}

make_header_margin();
dropdown_functionality();
search_functionality();