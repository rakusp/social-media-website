function setup_follow_button(follow_status, profile_id) {
    let button = document.getElementById('follow-button')
    switch (follow_status) {
        case 'yourself':
            button.style.display = 'none'
            return
        case 'followed':
            button.value = 'Unfollow'
            button.style.backgroundColor = 'indianred'
            button.onclick = function () {send_follow_request(profile_id, 'unfollow')}
            return
        case 'pending':
            button.style.backgroundColor = 'dimgray';
            button.value = 'Pending'
            button.disabled = true;
            return
        case 'rejected':
            button.value = 'Rejected'
            button.disabled = true;
            return
        case 'not sent':
            button.value = 'Follow'
            button.style.backgroundColor = 'cornflowerblue';
            button.onclick = function () {send_follow_request(profile_id)}
            return
    }
}

function send_follow_request(profile_id, action='follow') {
    let URL = '/profile/follow-request/'
    let post_data = {
        'profile_id': profile_id,
        'action': action
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
                if (action==='follow') {
                    setup_follow_button('pending', profile_id)
                } else {
                    setup_follow_button('follow', profile_id)
                    location.reload()
                }
            } else {
                alert(JSON.parse(data['content'])['error'])
            }
        })
}
