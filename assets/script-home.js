// ================ SW ================ //
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/assets/sw.js')
}


// ================ PWA ================ //
document.addEventListener('DOMContentLoaded', () => {
    let install
    const PWA = document.getElementById('pwa')
    PWA.style.display = 'none'

    window.addEventListener('beforeinstallprompt', e => {
        e.preventDefault()
        install = e
        PWA.style.display = 'inline'
    })

    PWA.addEventListener('click', async e => {
        e.preventDefault()
        install.prompt()
        const { outcome } = await install.userChoice
        if (outcome == 'accepted') PWA.style.display = 'none'
    })
})


// ================ Protection ================ //
document.addEventListener('contextmenu',    e => e.preventDefault())
document.addEventListener('selectstart',    e => e.preventDefault())
document.addEventListener('copy',           e => e.preventDefault())
document.addEventListener('cut',            e => e.preventDefault())
document.addEventListener('mousedown',      e => (e.button === 2) && e.preventDefault())
document.addEventListener('keydown',        e => ((e.ctrlKey && ['c','u','s'].includes(e.key.toLowerCase())) || (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i')) && e.preventDefault())


// ================ Posts ================ //
document.querySelectorAll('#posts a').forEach(a => {
    const video = a.querySelector('video')
    a.addEventListener('mouseenter', () => { video.play()                })
    a.addEventListener('mouseleave', () => { video.pause(); video.load() })
})