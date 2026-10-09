const reveals = document.querySelectorAll('.reveal');
const photoTrigger = document.querySelector('.interest-trigger');
const photoGallery = document.querySelector('#photo-gallery');
const contactVideo = document.querySelector('.contact-video[data-src]');
const educationVideo = document.querySelector('.education-video[data-src]');

const requestInlineVideoPlayback = (video) => {
  if (!video) return;
  const play = () => {
    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;
    video.setAttribute('muted', '');
    const playAttempt = video.play();
    playAttempt?.catch(() => {});
  };
  video.setAttribute('playsinline', '');
  video.setAttribute('webkit-playsinline', 'true');
  video.setAttribute('x5-playsinline', 'true');
  video.setAttribute('x5-video-player-type', 'h5');
  video.setAttribute('x5-video-player-fullscreen', 'false');
  video.addEventListener('loadedmetadata', play, { once: true });
  video.addEventListener('loadeddata', play, { once: true });
  video.addEventListener('canplay', play, { once: true });
  document.addEventListener('WeixinJSBridgeReady', play, { once: true });
  document.addEventListener('YixinJSBridgeReady', play, { once: true });
  document.addEventListener('touchstart', play, { once: true });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) play();
  });
  if ('WeixinJSBridge' in window) play();
  play();
};

const loadContactVideo = () => {
  if (!contactVideo || contactVideo.dataset.loaded === 'true') return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  contactVideo.dataset.loaded = 'true';
  contactVideo.src = contactVideo.dataset.src;
  contactVideo.load();
  requestInlineVideoPlayback(contactVideo);
};

if (contactVideo) {
  const videoStage = contactVideo.closest('.contact-video-stage');
  if ('IntersectionObserver' in window && videoStage) {
    const contactVideoObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        loadContactVideo();
        contactVideoObserver.unobserve(entry.target);
      });
    }, { rootMargin: '260px 0px' });
    contactVideoObserver.observe(videoStage);
  } else {
    loadContactVideo();
  }
}

const loadEducationVideo = () => {
  if (!educationVideo || educationVideo.dataset.loaded === 'true') return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const educationCard = educationVideo.closest('.school-primary');
  const revealEducationVideo = () => educationCard?.classList.add('is-education-video-ready');
  educationVideo.dataset.loaded = 'true';
  educationVideo.addEventListener('playing', revealEducationVideo, { once: true });
  educationVideo.src = educationVideo.dataset.src;
  educationVideo.load();
  requestInlineVideoPlayback(educationVideo);
};

if (educationVideo) {
  const educationCard = educationVideo.closest('.school-primary');
  if ('IntersectionObserver' in window && educationCard) {
    const educationVideoObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        loadEducationVideo();
        educationVideoObserver.unobserve(entry.target);
      });
    }, { rootMargin: '250px 0px' });
    educationVideoObserver.observe(educationCard);
  } else {
    loadEducationVideo();
  }
  const desktopEducationVideoQuery = matchMedia('(min-width: 681px)');
  desktopEducationVideoQuery.addEventListener?.('change', (event) => {
    if (event.matches) loadEducationVideo();
  });
}

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

const pptDialogs = [...document.querySelectorAll('.ppt-dialog')];
const pptDialogControllers = new Map();

const setupPptDialog = (pptDialog) => {
  const pptSlideGrid = pptDialog.querySelector('.ppt-slide-grid');
  const pptSlides = [...pptDialog.querySelectorAll('.ppt-slide-grid .ppt-slide[data-slide]')];
  const pptStage = pptDialog.querySelector('.ppt-dialog-stage');
  const pptStageImage = pptStage?.querySelector('img');
  const pptStageNumber = pptStage?.querySelector('.ppt-stage-number');
  const pptStagePrevious = pptStage?.querySelector('.ppt-stage-previous');
  const pptStageNext = pptStage?.querySelector('.ppt-stage-next');
  const pptBackButton = pptDialog.querySelector('.ppt-dialog-back');
  const pptCloseButtons = [...pptDialog.querySelectorAll('.ppt-dialog-close, .ppt-slide-grid-close')];
  let activePptSlide = null;
  let pptReturnFocus = null;
  let pptTransitionTimer;
  let pptPointerStart = null;
  let suppressPptStageClick = false;

  const getSlideImage = (slide) => {
    const thumbnail = slide.querySelector('img');
    return {
      src: slide.dataset.image || slide.dataset.src || thumbnail?.currentSrc || thumbnail?.src || '',
      alt: slide.dataset.alt || thumbnail?.alt || slide.textContent.trim() || 'PPT 幻灯片预览'
    };
  };

  const setPptThumbnailAvailability = (isFocused) => {
    pptSlides.forEach((slide) => {
      slide.tabIndex = isFocused ? -1 : 0;
      slide.setAttribute('aria-hidden', String(isFocused));
      slide.setAttribute('aria-current', String(slide === activePptSlide));
    });
  };

  const setPptView = (view, { focusSlide = false } = {}) => {
    const isFocused = view === 'slide';
    pptDialog.classList.toggle('is-grid-view', !isFocused);
    pptDialog.classList.toggle('is-slide-focused', isFocused);
    pptSlideGrid?.setAttribute('aria-hidden', String(isFocused));
    pptStage?.setAttribute('aria-hidden', String(!isFocused));
    [pptStagePrevious, pptStageNext].filter(Boolean).forEach((button) => {
      button.tabIndex = isFocused ? 0 : -1;
      button.setAttribute('aria-hidden', String(!isFocused));
    });
    if (pptBackButton) {
      pptBackButton.tabIndex = isFocused ? 0 : -1;
      pptBackButton.setAttribute('aria-hidden', String(!isFocused));
    }
    setPptThumbnailAvailability(isFocused);

    if (focusSlide && activePptSlide) activePptSlide.focus({ preventScroll: true });
  };

  const showPptSlide = (slide, { direction = 0, focusBack = true } = {}) => {
    if (!pptStageImage) return;
    const image = getSlideImage(slide);
    if (!image.src) return;
    activePptSlide = slide;
    clearTimeout(pptTransitionTimer);
    pptDialog.classList.remove('is-switching', 'is-moving-next', 'is-moving-previous');
    void pptDialog.offsetWidth;
    pptDialog.classList.add('is-switching');
    if (direction > 0) pptDialog.classList.add('is-moving-next');
    if (direction < 0) pptDialog.classList.add('is-moving-previous');
    pptStageImage.src = image.src;
    pptStageImage.alt = image.alt;
    if (pptStageNumber) pptStageNumber.textContent = `SLIDE ${String(pptSlides.indexOf(slide) + 1).padStart(2, '0')}`;
    setPptView('slide');
    pptTransitionTimer = setTimeout(() => pptDialog.classList.remove('is-switching', 'is-moving-next', 'is-moving-previous'), 420);
    if (focusBack) requestAnimationFrame(() => pptBackButton?.focus({ preventScroll: true }));
  };

  const showAdjacentPptSlide = (direction) => {
    if (!pptSlides.length) return;
    const currentIndex = Math.max(0, pptSlides.indexOf(activePptSlide));
    const nextIndex = (currentIndex + direction + pptSlides.length) % pptSlides.length;
    showPptSlide(pptSlides[nextIndex], { direction, focusBack: false });
  };

  const openPptGallery = (opener) => {
    pptReturnFocus = opener;
    pptDialog.classList.remove('is-switching');
    setPptView('grid');
    if (!pptDialog.open) pptDialog.showModal();
    requestAnimationFrame(() => {
      pptDialog.classList.add('is-open');
      pptSlides[0]?.focus({ preventScroll: true });
    });
  };

  pptSlides.forEach((slide) => {
    slide.addEventListener('click', () => showPptSlide(slide));
  });

  pptSlideGrid?.addEventListener('keydown', (event) => {
    const currentIndex = pptSlides.indexOf(document.activeElement);
    if (currentIndex < 0) return;
    let nextIndex = currentIndex;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = pptSlides.length - 1;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') nextIndex = (currentIndex + 1) % pptSlides.length;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') nextIndex = (currentIndex - 1 + pptSlides.length) % pptSlides.length;
    if (nextIndex === currentIndex) return;
    event.preventDefault();
    pptSlides[nextIndex]?.focus();
  });

  pptBackButton?.addEventListener('click', () => setPptView('grid', { focusSlide: true }));
  pptStagePrevious?.addEventListener('click', (event) => {
    event.stopPropagation();
    showAdjacentPptSlide(-1);
  });
  pptStageNext?.addEventListener('click', (event) => {
    event.stopPropagation();
    showAdjacentPptSlide(1);
  });
  pptStage?.addEventListener('pointerdown', (event) => {
    if (event.target.closest('.ppt-stage-nav')) return;
    pptPointerStart = { x: event.clientX, y: event.clientY };
  });
  pptStage?.addEventListener('pointerup', (event) => {
    if (!pptPointerStart) return;
    const dx = event.clientX - pptPointerStart.x;
    const dy = event.clientY - pptPointerStart.y;
    pptPointerStart = null;
    if (Math.abs(dx) < 44 || Math.abs(dx) <= Math.abs(dy) * 1.25) return;
    suppressPptStageClick = true;
    showAdjacentPptSlide(dx < 0 ? 1 : -1);
  });
  pptStage?.addEventListener('pointercancel', () => { pptPointerStart = null; });
  pptStage?.addEventListener('click', (event) => {
    if (event.target.closest('.ppt-stage-nav')) return;
    if (suppressPptStageClick) {
      suppressPptStageClick = false;
      return;
    }
    setPptView('grid', { focusSlide: true });
  });
  pptDialog.addEventListener('keydown', (event) => {
    if (!pptDialog.classList.contains('is-slide-focused')) return;
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    showAdjacentPptSlide(event.key === 'ArrowLeft' ? -1 : 1);
  });
  pptCloseButtons.forEach((button) => button.addEventListener('click', () => pptDialog.close()));
  pptDialog.addEventListener('click', (event) => {
    if (event.target === pptDialog) pptDialog.close();
  });
  pptDialog.addEventListener('close', () => {
    clearTimeout(pptTransitionTimer);
    pptDialog.classList.remove('is-open', 'is-switching', 'is-moving-next', 'is-moving-previous', 'is-slide-focused');
    pptDialog.classList.add('is-grid-view');
    setPptThumbnailAvailability(false);
    pptStage?.setAttribute('aria-hidden', 'true');
    pptSlideGrid?.setAttribute('aria-hidden', 'false');
    [pptStagePrevious, pptStageNext].filter(Boolean).forEach((button) => {
      button.tabIndex = -1;
      button.setAttribute('aria-hidden', 'true');
    });
    if (pptBackButton) {
      pptBackButton.tabIndex = -1;
      pptBackButton.setAttribute('aria-hidden', 'true');
    }
    if (pptReturnFocus?.isConnected) pptReturnFocus.focus({ preventScroll: true });
    pptReturnFocus = null;
    activePptSlide = null;
  });

  return { open: openPptGallery };
};

pptDialogs.forEach((pptDialog) => {
  const galleryKey = pptDialog.dataset.pptGallery || pptDialog.id.replace(/^ppt-gallery-dialog-/, 'ppt-');
  if (galleryKey) pptDialogControllers.set(galleryKey, setupPptDialog(pptDialog));
});

document.querySelectorAll('[data-ppt-gallery-open]').forEach((opener) => {
  const galleryKey = opener.dataset.pptGalleryOpen;
  const controller = pptDialogControllers.get(galleryKey);
  if (!controller) return;
  opener.addEventListener('click', () => controller.open(opener));
});

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

function openDialog(items, initialIndex = 0) {
  dialogItems = items;
  dialogIndex = Math.max(0, Math.min(initialIndex, items.length - 1));
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
const motorEvidenceItems = [...document.querySelectorAll('[data-motor-evidence]')];
const motorEvidenceGallery = motorEvidenceItems.map((item) => {
  const image = item.querySelector('img');
  return {
    src: image?.currentSrc || image?.src || '',
    alt: item.dataset.evidenceTitle || image?.alt || '直流电机控制实验图',
    rotate: false
  };
});
motorEvidenceItems.forEach((item, index) => {
  item.addEventListener('click', () => openDialog(motorEvidenceGallery, index));
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
