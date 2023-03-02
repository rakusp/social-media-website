function setup_image_preview() {
    let img = document.getElementById('preview-image')
    document.getElementById('id_image').addEventListener('change', ev => {
        const [file] = ev.target.files
        if (file) {
            img.src = URL.createObjectURL(file)
            img.style.display = 'block'
            adjust_image_size(img)
        } else {
            img.style.display = 'none'
        }
    })
}

window.onload = setup_image_preview