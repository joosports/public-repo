(() => {
  "use strict";

  const languageSelect = document.querySelector("#language-select");
  const english = document.querySelector("#profile-en");
  const japanese = document.querySelector("#profile-ja");
  const status = document.querySelector("#language-status");
  const printButton = document.querySelector("#print-button");
  const lightbox = document.querySelector("#photo-lightbox");
  const allPhotos = [...document.querySelectorAll(".profile-copy [data-lightbox]")];
  let photos = [...english.querySelectorAll("[data-lightbox]")];
  const image = lightbox.querySelector(".lightbox-image");
  const caption = lightbox.querySelector(".lightbox-caption");
  const count = lightbox.querySelector(".lightbox-count");
  let photoIndex = 0;
  let preparingPrint = false;

  const closeLightbox = () => lightbox.close();
  const showPhoto = (index) => {
    photoIndex = (index + photos.length) % photos.length;
    const photo = photos[photoIndex];
    image.src = photo.href;
    image.alt = photo.querySelector("img").alt;
    caption.textContent = [...photo.querySelector("figcaption").children].map((part) => part.textContent).join("\n");
    count.textContent = `${photoIndex + 1} / ${photos.length}`;
  };

  const setLanguage = (language, updateAddress = false) => {
    const isJapanese = language === "ja" || language === "jp";
    if (lightbox.open) closeLightbox();
    languageSelect.value = isJapanese ? "ja" : "en";
    english.hidden = isJapanese;
    japanese.hidden = !isJapanese;
    document.documentElement.lang = isJapanese ? "ja" : "en";
    photos = [...(isJapanese ? japanese : english).querySelectorAll("[data-lightbox]")];
    photoIndex = 0;
    printButton.disabled = preparingPrint;
    printButton.querySelector("span").textContent = isJapanese ? "印刷 / PDF保存" : "Print / Save PDF";
    document.querySelector('label[for="language-select"]').textContent = isJapanese ? "言語" : "Language";
    lightbox.setAttribute("aria-label", isJapanese ? "写真ビューアー" : "Photo viewer");
    lightbox.querySelector(".lightbox-close").setAttribute("aria-label", isJapanese ? "写真を閉じる" : "Close photo viewer");
    lightbox.querySelector(".lightbox-prev").setAttribute("aria-label", isJapanese ? "前の写真" : "Previous photo");
    lightbox.querySelector(".lightbox-next").setAttribute("aria-label", isJapanese ? "次の写真" : "Next photo");
    status.textContent = isJapanese ? "日本語を表示しています。" : "English selected.";
    document.title = isJapanese ? "謝朗天 (Tse Long Tin) | 選手プロフィール — Version 2" : "Tse Long Tin (謝朗天) | Player Profile — Version 2";
    if (updateAddress) {
      const url = new URL(window.location.href);
      url.searchParams.set("lang", isJapanese ? "ja" : "en");
      window.history.replaceState({}, "", url);
    }
  };

  // Default to English, independent of version 1's saved language or browser locale.
  setLanguage(new URLSearchParams(window.location.search).get("lang"));
  languageSelect.addEventListener("change", () => setLanguage(languageSelect.value, true));
  printButton.addEventListener("click", async () => {
    if (preparingPrint) return;
    const selectedProfile = languageSelect.value === "ja" ? japanese : english;
    if (lightbox.open) closeLightbox();
    preparingPrint = true;
    printButton.disabled = true;
    try {
      await document.fonts.ready;
      await Promise.all([...selectedProfile.querySelectorAll("img")].map((photo) => photo.decode()));
      if (!selectedProfile.hidden) window.print();
    } catch (_) {
      status.textContent = languageSelect.value === "ja"
        ? "画像を読み込めませんでした。印刷前に画像ファイルをご確認ください。"
        : "A profile image could not be loaded. Check the assets and img folders before printing.";
    } finally {
      preparingPrint = false;
      printButton.disabled = false;
    }
  });

  allPhotos.forEach((photo) => {
    photo.addEventListener("click", (event) => {
      if (typeof lightbox.showModal !== "function") return; // Keep the full-image link as a fallback.
      event.preventDefault();
      photos = [...photo.closest("main").querySelectorAll("[data-lightbox]")];
      showPhoto(photos.indexOf(photo));
      lightbox.showModal();
      document.body.classList.add("lightbox-open");
    });
  });
  lightbox.querySelector(".lightbox-close").addEventListener("click", closeLightbox);
  lightbox.querySelector(".lightbox-prev").addEventListener("click", () => showPhoto(photoIndex - 1));
  lightbox.querySelector(".lightbox-next").addEventListener("click", () => showPhoto(photoIndex + 1));
  lightbox.addEventListener("close", () => {
    document.body.classList.remove("lightbox-open");
    image.removeAttribute("src");
  });
  lightbox.addEventListener("click", (event) => {
    if (event.target !== lightbox) return;
    const rect = lightbox.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeLightbox();
  });
  document.addEventListener("keydown", (event) => {
    if (!lightbox.open) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      showPhoto(photoIndex + (event.key === "ArrowLeft" ? -1 : 1));
    }
  });
  let touchStartX = null;
  lightbox.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "touch") touchStartX = event.clientX;
  });
  lightbox.addEventListener("pointerup", (event) => {
    if (event.pointerType !== "touch" || touchStartX === null) return;
    const distance = event.clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(distance) >= 50) showPhoto(photoIndex + (distance < 0 ? 1 : -1));
  });
  lightbox.addEventListener("pointercancel", () => { touchStartX = null; });
})();
