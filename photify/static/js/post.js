const max_image_height = Math.floor(0.65 * screen.height)

// if image is too long, scale it down, retaining the aspect ratio
function adjust_image_size(img) {
    if (img.height > max_image_height) {
        let scale_by = max_image_height / img.height
        img.height = Math.floor(img.height * scale_by)
        img.width = Math.floor(img.width * scale_by)
    }
}

// update the number of likes on load
function update_like_status(like_counter, like_image, like_count, action) {
    if (action === 'like') {
        like_image.setAttribute('src', '/static/post/heart-full.png')
        like_image.setAttribute('data-liked', 'true')
    } else {
        like_image.setAttribute('src', '/static/post/heart-empty.png')
        like_image.setAttribute('data-liked', 'false')
    }
    like_counter.innerText = like_count
}

function like(like_image, post_id, user_id) {
    let URL = '/post/like/'
    let post_data = {
        'post_id': post_id,
        'user_id': user_id,
        'action': 'like'
    }
    if (like_image.getAttribute('data-liked') === 'true') {post_data['action'] = 'unlike'}

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
                update_like_status(document.getElementById('post' + post_id + '-like-count'), like_image,
                    JSON.parse(data['content'])['likesCount'], post_data['action'])
            } else {
                alert(JSON.parse(data['content'])['error'])
            }
        })
}