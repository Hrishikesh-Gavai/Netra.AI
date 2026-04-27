/* ─────────────────────────────────────────────────────────────────────────
   NetraAI — script.js
   Companion JS for index.html. The upload, kinetic type, and carousel logic
   live inline in index.html for immediate execution; this file adds
   supplementary behaviour (nav active state, scroll animations, lazy images,
   drag-zone polish) and exposes the NetraAI public API.
───────────────────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
    initNavigation();
    initScrollAnimations();
    initUploadZone();       // supplements the inline upload handler
    initSmoothScroll();
    initLazyLoading();
});

/* ─── Navigation Active State ──────────────────────────────────────────── */
function initNavigation() {
    const sections = document.querySelectorAll('section[id], div[id]');
    const navLinks  = document.querySelectorAll('.nav-links a[href^="#"]');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            if (scrollY >= section.offsetTop - 200) current = section.id;
        });
        navLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === '#' + current);
        });
    }, { passive: true });
}

/* ─── Scroll Reveal Animations ─────────────────────────────────────────── */
function initScrollAnimations() {
    const cards = document.querySelectorAll('.feature-card, .team-card, .disease-card, .step-item');
    const obs   = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    cards.forEach(card => {
        if (!card.classList.contains('reveal')) card.classList.add('reveal');
        obs.observe(card);
    });
}

/* ─── Drag-and-Drop Upload Zone Polish ─────────────────────────────────── */
function initUploadZone() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;

    // Prevent browser from opening files dropped outside the zone
    ['dragenter','dragover','dragleave','drop'].forEach(ev =>
        document.body.addEventListener(ev, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false)
    );

    // Body-level drop: re-route to zone
    document.body.addEventListener('drop', (e) => {
        const files = e.dataTransfer?.files;
        if (files?.length) {
            const input = document.getElementById('imageInput');
            // trigger the inline handler via a CustomEvent so we don't duplicate logic
            const evt = new CustomEvent('externalDrop', { detail: { file: files[0] } });
            uploadArea.dispatchEvent(evt);
        }
    });

    uploadArea.addEventListener('externalDrop', (e) => {
        handleFileExternal(e.detail.file);
    });
}

/* Helper: handle a file dropped from outside the zone */
function handleFileExternal(file) {
    if (!['image/jpeg','image/jpg','image/png'].includes(file.type)) {
        showNotification('Please upload a JPG or PNG image.', 'error');
        return;
    }
    if (file.size > 16 * 1024 * 1024) {
        showNotification('File must be under 16 MB.', 'error');
        return;
    }
    // Surface the file-chosen UI via the imageInput trick
    const dt    = new DataTransfer();
    dt.items.add(file);
    const input = document.getElementById('imageInput');
    if (input) {
        input.files = dt.files;
        input.dispatchEvent(new Event('change'));
    }
}

/* ─── Smooth Scroll ────────────────────────────────────────────────────── */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

/* ─── Lazy Loading ─────────────────────────────────────────────────────── */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    if (!images.length) return;
    const obs = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src   = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    images.forEach(img => obs.observe(img));
}

/* ─── Notification System ──────────────────────────────────────────────── */
function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const n = document.createElement('div');
    n.className = 'notification';
    n.style.cssText = `
        position: fixed;
        top: 88px; right: 24px;
        padding: 16px 22px;
        border: 2px solid #fff;
        background: #000;
        color: #fff;
        font-family: 'Playfair Display', serif;
        font-size: 14px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideInRight 0.3s ease;
        max-width: 340px;
        box-shadow: 0 0 0 1px #000;
    `;

    /* Colour-code the icon only (not background) */
    const iconColor = { success: '#22C55E', error: '#FF4757', warning: '#FFD700', info: '#fff' }[type] || '#fff';
    const iconClass = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' }[type] || 'fa-info-circle';

    n.innerHTML = `<i class="fas ${iconClass}" style="color:${iconColor};font-size:18px;flex-shrink:0;"></i><span>${message}</span>`;
    document.body.appendChild(n);

    setTimeout(() => {
        n.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => n.parentNode && n.remove(), 300);
    }, 3500);
}

/* ─── Inject global animation keyframes ───────────────────────────────── */
(function injectStyles() {
    const s = document.createElement('style');
    s.textContent = `
        @keyframes slideInRight  { from { transform:translateX(110%); opacity:0; } to { transform:translateX(0); opacity:1; } }
        @keyframes slideOutRight { from { transform:translateX(0); opacity:1; } to { transform:translateX(110%); opacity:0; } }
        @keyframes spin          { from { transform:rotate(0); } to { transform:rotate(360deg); } }
        .fa-spin { animation: spin 0.9s linear infinite; }
        .reveal  { opacity:0; transform:translateY(28px); transition:opacity 0.7s ease, transform 0.7s ease; }
        .reveal.visible { opacity:1; transform:translateY(0); }
    `;
    document.head.appendChild(s);
})();

/* ─── Image validation (exported utility) ─────────────────────────────── */
function validateImage(file) {
    const validTypes = ['image/jpeg','image/jpg','image/png'];
    if (!validTypes.includes(file.type)) {
        showNotification('Invalid file type. Please upload JPG or PNG.', 'error');
        return false;
    }
    if (file.size > 16 * 1024 * 1024) {
        showNotification('File too large. Maximum size is 16 MB.', 'error');
        return false;
    }
    return true;
}

/* ─── Analytics stub ───────────────────────────────────────────────────── */
function trackEvent(eventName, params = {}) {
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, { ...params, send_to: 'GA_MEASUREMENT_ID' });
    }
}

/* ─── Public API ───────────────────────────────────────────────────────── */
window.NetraAI = {
    showNotification,
    validateImage,
    trackEvent
};