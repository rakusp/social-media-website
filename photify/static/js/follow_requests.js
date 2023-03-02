function follow_request_action(user_from_id, user_to_id, action) {
    let URL = '/accounts/follow-request-action/'
    let post_data = {
        'user_from_id': user_from_id,
        'user_to_id': user_to_id,
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
                document.getElementById('request' + user_from_id + '-' + user_to_id).remove()
            } else {
                alert(JSON.parse(data['content'])['error'])
            }
        })
}
