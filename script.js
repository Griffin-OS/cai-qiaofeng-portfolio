const reveals = document.querySelectorAll('.reveal');
const photoTrigger = document.querySelector('.interest-trigger');
const photoGallery = document.querySelector('#photo-gallery');
if (photoTrigger && photoGallery) {
  photoGallery.hidden = true;
  photoTrigger.addEventListener('click', () => {
    const open = photoGallery.hidden;
    photoGallery.hidden = !open;
    photoTrigger.setAttribute('aria-expanded', String(open));
  });
}
reveals.forEach((item) => {
  if (item.dataset.delay) item.style.setProperty('--delay', `${item.dataset.delay}ms`);
});

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px' });
  reveals.forEach((item) => observer.observe(item));
} else {
  reveals.forEach((item) => item.classList.add('is-visible'));
}

const meter = document.querySelector('.scroll-meter span');
const navLinks = [...document.querySelectorAll('.topbar nav a')];
const navTargets = navLinks.map((link) => ({
  link,
  target: document.querySelector(link.getAttribute('href'))
})).filter((item) => item.target);
const updateMeter = () => {
  const max = document.documentElement.scrollHeight - innerHeight;
  meter.style.width = `${max > 0 ? (scrollY / max) * 100 : 0}%`;
  const marker = scrollY + 150;
  let current = navTargets[0];
  navTargets.forEach((item) => {
    if (item.target.offsetTop <= marker) current = item;
  });
  navLinks.forEach((link) => link.classList.toggle('is-active', link === current.link));
};
addEventListener('scroll', updateMeter, { passive: true });
updateMeter();

const ticker = document.querySelector('.ticker div');
ticker.textContent += ` ${ticker.textContent}`;

const portraitStage = document.querySelector('.portrait-stage');
if (portraitStage && matchMedia('(pointer: fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const portrait = portraitStage.querySelector('.portrait-cutout');
  const portraitType = portraitStage.querySelector('.portrait-type');
  portraitStage.addEventListener('pointermove', (event) => {
    const box = portraitStage.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    portrait.style.transform = `translate3d(${x * 24}px, ${y * 18}px, 0)`;
    portraitType.style.transform = `translate3d(${x * -36}px, ${y * -27}px, 0)`;
  });
  portraitStage.addEventListener('pointerleave', () => {
    portrait.style.transform = '';
    portraitType.style.transform = '';
  });
}

const dialog = document.querySelector('.certificate-dialog');
const dialogImage = dialog.querySelector('img');
document.querySelectorAll('.award-card[data-image]').forEach((card) => {
  card.addEventListener('click', () => {
    dialogImage.src = card.dataset.image;
    dialogImage.alt = `${card.querySelector('h3').textContent}证书`;
    dialogImage.classList.toggle('is-rotated', card.dataset.rotate === '180');
    dialog.showModal();
  });
});
document.querySelectorAll('.photo-gallery figure img').forEach((image) => {
  image.addEventListener('click', () => {
    dialogImage.src = image.src;
    dialogImage.alt = image.alt;
    dialogImage.classList.remove('is-rotated');
    dialog.showModal();
  });
});
dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => {
  if (event.target === dialog) dialog.close();
});

if (location.hash) {
  addEventListener('load', () => {
    const target = document.querySelector(location.hash);
    if (!target) return;
    const previous = document.documentElement.style.scrollBehavior;
    document.documentElement.style.scrollBehavior = 'auto';
    target.scrollIntoView();
    target.querySelectorAll('.reveal').forEach((item) => item.classList.add('is-visible'));
    document.documentElement.style.scrollBehavior = previous;
  }, { once: true });
}
