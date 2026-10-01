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

const ticker = document.querySelector('.ticker');
const tickerTrack = ticker?.querySelector('.ticker-track');
const tickerGroup = tickerTrack?.querySelector('.ticker-group');
if (ticker && tickerTrack && tickerGroup) {
  let tickerFrame;
  const buildTickerLoop = () => {
    cancelAnimationFrame(tickerFrame);
    tickerFrame = requestAnimationFrame(() => {
      tickerTrack.querySelectorAll('[data-ticker-clone]').forEach((clone) => clone.remove());
      const loopWidth = Math.ceil(tickerGroup.getBoundingClientRect().width);
      if (!loopWidth) return;
      const copies = Math.ceil(ticker.clientWidth / loopWidth) + 2;
      for (let index = 0; index < copies; index += 1) {
        const clone = tickerGroup.cloneNode(true);
        clone.dataset.tickerClone = 'true';
        clone.setAttribute('aria-hidden', 'true');
        tickerTrack.append(clone);
      }
      tickerTrack.style.setProperty('--ticker-shift', `-${loopWidth}px`);
    });
  };
  buildTickerLoop();
  if ('ResizeObserver' in window) new ResizeObserver(buildTickerLoop).observe(ticker);
  else addEventListener('resize', buildTickerLoop, { passive: true });
  document.fonts?.ready?.then(buildTickerLoop);
}

const portraitStage = document.querySelector('.portrait-stage');
if (portraitStage && matchMedia('(pointer: fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const portrait = portraitStage.querySelector('.portrait-cutout');
  const portraitType = portraitStage.querySelector('.portrait-type');
  portraitStage.addEventListener('pointermove', (event) => {
    const box = portraitStage.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    portrait.style.transform = `translateX(-48.5%) translate3d(${x * 24}px, ${y * 18}px, 0)`;
    portraitType.style.transform = `translate3d(${x * -36}px, ${y * -27}px, 0)`;
  });
  portraitStage.addEventListener('pointerleave', () => {
    portrait.style.transform = '';
    portraitType.style.transform = '';
  });
}

const mascotCard = document.querySelector('.school-primary');
if (mascotCard && matchMedia('(pointer: fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const mascot = mascotCard.querySelector('.education-mascot');
  let mascotReset;
  mascotCard.addEventListener('pointerenter', () => {
    clearTimeout(mascotReset);
    mascot.style.animation = '';
    mascot.style.transform = '';
    mascotCard.classList.add('is-mascot-breath');
  });
  mascotCard.addEventListener('pointerleave', () => {
    mascotCard.classList.remove('is-mascot-breath');
    mascot.style.animation = 'none';
    mascot.style.transform = getComputedStyle(mascot).transform;
    void mascot.offsetWidth;
    requestAnimationFrame(() => { mascot.style.transform = 'scale(1)'; });
    mascotReset = setTimeout(() => {
      mascot.style.animation = '';
      mascot.style.transform = '';
    }, 1400);
  });
}

if (matchMedia('(max-width: 680px) and (pointer: coarse)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
  const mobilePulseObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        entry.target.classList.remove('is-mobile-pulsed');
        return;
      }
      entry.target.classList.remove('is-mobile-pulsed');
      void entry.target.offsetWidth;
      entry.target.classList.add('is-mobile-pulsed');
    });
  }, { threshold: 0.42 });
  [portraitStage, mascotCard].filter(Boolean).forEach((target) => mobilePulseObserver.observe(target));
}

const dialog = document.querySelector('.certificate-dialog');
const dialogImage = dialog.querySelector('img');
const dialogPrevious = dialog.querySelector('.dialog-gallery-previous');
const dialogNext = dialog.querySelector('.dialog-gallery-next');
const dialogCount = dialog.querySelector('.dialog-gallery-count');
let dialogItems = [];
let dialogIndex = 0;

function renderDialogItem() {
  const item = dialogItems[dialogIndex];
  if (!item) return;
  dialogImage.classList.remove('is-rotated');
  void dialogImage.offsetWidth;
  dialogImage.src = item.src;
  dialogImage.alt = item.alt;
  if (item.rotate) dialogImage.classList.add('is-rotated');
  const hasMultiple = dialogItems.length > 1;
  dialogPrevious.hidden = !hasMultiple;
  dialogNext.hidden = !hasMultiple;
  dialogCount.textContent = hasMultiple ? `${dialogIndex + 1} / ${dialogItems.length}` : '';
}

function openDialog(items) {
  dialogItems = items;
  dialogIndex = 0;
  renderDialogItem();
  if (!dialog.open) dialog.showModal();
}

document.querySelectorAll('.award-card[data-image]').forEach((card) => {
  card.addEventListener('click', () => {
    const sources = (card.dataset.gallery || card.dataset.image).split('|');
    const labels = (card.dataset.galleryLabels || '').split('|');
    openDialog(sources.map((src, index) => ({
      src,
      alt: labels[index] || `${card.querySelector('h3').textContent}证书`,
      rotate: index === 0 && card.dataset.rotate === '180'
    })));
  });
});
document.querySelectorAll('.photo-gallery figure img').forEach((image) => {
  image.addEventListener('click', () => {
    openDialog([{ src: image.src, alt: image.alt, rotate: false }]);
  });
});
document.querySelectorAll('.transcript-link[data-image]').forEach((link) => {
  link.addEventListener('click', () => {
    openDialog([{ src: link.dataset.image, alt: '成绩单预览', rotate: false }]);
  });
});
dialogPrevious.addEventListener('click', () => {
  dialogIndex = (dialogIndex - 1 + dialogItems.length) % dialogItems.length;
  renderDialogItem();
});
dialogNext.addEventListener('click', () => {
  dialogIndex = (dialogIndex + 1) % dialogItems.length;
  renderDialogItem();
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
