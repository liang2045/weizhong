const STORAGE_KEY = "product-resource-cards:v1";
const SYNC_KEY = "product-resource-sync-url:v1";
const THEME_KEY = "product-resource-theme:v1";

const RESOURCE_BUTTONS = ["详情页", "主图", "SKU", "白底图", "网盘链接", "产品资料"];
const CLOUD_LINK_LABEL = "网盘链接";
const isDesktopApp = Boolean(window.huazaiDesktop);

const placeholderSvg = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 650">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#C8102E"/><stop offset="1" stop-color="#222222"/></linearGradient></defs>
  <rect width="900" height="650" fill="#e7e7ea"/>
  <circle cx="720" cy="120" r="180" fill="#fff1f3"/>
  <rect x="170" y="160" width="560" height="330" rx="44" fill="url(#g)" opacity="0.95"/>
  <path d="M270 415l110-125 90 95 70-76 100 106z" fill="#fff" opacity="0.88"/>
  <circle cx="585" cy="250" r="46" fill="#fff" opacity="0.92"/>
  <text x="450" y="555" text-anchor="middle" fill="#222" font-family="Arial" font-size="40" font-weight="700">Product Image</text>
</svg>`);
const PLACEHOLDER_IMAGE = `data:image/svg+xml;charset=UTF-8,${placeholderSvg}`;

const sampleProducts = [
  {
    id: crypto.randomUUID(),
    name: "新品智能手柄 A1",
    price: "定价：¥299 / 批发价详询",
    image: PLACEHOLDER_IMAGE,
    links: {
      "详情页": "file:///Volumes/NAS/Products/A1/detail",
      "主图": "file:///Volumes/NAS/Products/A1/main-image",
      "SKU": "file:///Volumes/NAS/Products/A1/sku",
      "白底图": "file:///Volumes/NAS/Products/A1/white-bg",
      "网盘链接": "https://example.com/share/a1",
      "产品资料": "file:///Volumes/NAS/Products/A1/documents"
    }
  }
];

let products = loadProducts();
let draggedId = null;

const cardsEl = document.querySelector("#cards");
const emptyStateEl = document.querySelector("#emptyState");
const cardCountEl = document.querySelector("#cardCount");
const syncStatusEl = document.querySelector("#syncStatus");
const dialog = document.querySelector("#cardDialog");
const form = document.querySelector("#cardForm");
const linkFieldsEl = document.querySelector("#linkFields");
const imagePreviewEl = document.querySelector("#imagePreview");
const syncUrlEl = document.querySelector("#syncUrl");
const themeToggleBtn = document.querySelector("#themeToggleBtn");
const chooseSyncFileBtn = document.querySelector("#chooseSyncFileBtn");

syncUrlEl.value = localStorage.getItem(SYNC_KEY) || (isDesktopApp ? "" : "./products.json");
applyTheme(localStorage.getItem(THEME_KEY) || "light");
renderDesktopState();
renderLinkFields();
renderCards();

function loadProducts() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return sampleProducts;
  try {
    const parsed = JSON.parse(saved);
    return Array.isArray(parsed.products) ? parsed.products : sampleProducts;
  } catch {
    return sampleProducts;
  }
}

function buildConfigPayload() {
  return JSON.stringify({ updatedAt: new Date().toISOString(), products }, null, 2);
}

function persist({ publish = true } = {}) {
  localStorage.setItem(STORAGE_KEY, buildConfigPayload());
  if (publish) publishSharedConfig().catch((error) => setSyncStatus(`本机已保存，共享发布失败：${error.message}`));
}

async function publishSharedConfig() {
  const location = syncUrlEl.value.trim();
  if (!isDesktopApp || !location || /^https?:\/\//i.test(location)) return false;
  await window.huazaiDesktop.writeSyncFile(location, buildConfigPayload());
  setSyncStatus("已保存到团队共享配置，其他安装者点击“更新”即可同步。");
  return true;
}

function setSyncStatus(message) {
  syncStatusEl.textContent = message;
}

function normalizeProduct(product) {
  return {
    id: product.id || crypto.randomUUID(),
    name: product.name || "未命名产品",
    price: product.price || "定价待更新",
    image: product.image || PLACEHOLDER_IMAGE,
    links: RESOURCE_BUTTONS.reduce((links, label) => {
      links[label] = product.links?.[label] || "";
      return links;
    }, {})
  };
}

function renderCards() {
  cardsEl.innerHTML = "";
  products = products.map(normalizeProduct);
  cardCountEl.textContent = `${products.length} 个产品`;
  emptyStateEl.hidden = products.length > 0;

  const template = document.querySelector("#cardTemplate");
  products.forEach((product, index) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.dataset.id = product.id;
    card.querySelector(".product-image").src = product.image || PLACEHOLDER_IMAGE;
    card.querySelector(".product-image").alt = product.name;
    card.querySelector("h3").textContent = product.name;
    card.querySelector(".product-meta p").textContent = product.price;

    const buttonGrid = card.querySelector(".button-grid");
    RESOURCE_BUTTONS.forEach((label) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "resource-button";
      button.textContent = label;
      button.classList.toggle("is-unconfigured", !product.links[label]);
      button.title = product.links[label] || "请先在设置中配置地址";
      button.addEventListener("click", () => openResource(label, product.links[label]));
      buttonGrid.append(button);
    });

    card.querySelector(".settings-btn").addEventListener("click", () => openDialog(product.id));
    card.querySelectorAll(".move-btn").forEach((button) => {
      button.disabled = (button.dataset.direction === "up" && index === 0) || (button.dataset.direction === "down" && index === products.length - 1);
      button.addEventListener("click", () => moveCard(product.id, button.dataset.direction));
    });

    card.addEventListener("dragstart", () => {
      draggedId = product.id;
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => {
      draggedId = null;
      card.classList.remove("dragging");
    });
    card.addEventListener("dragover", (event) => event.preventDefault());
    card.addEventListener("drop", () => dropCard(product.id));
    cardsEl.append(card);
  });
}

async function openResource(label, url) {
  const rawUrl = url?.trim();
  if (!rawUrl) {
    alert(`请先在卡片设置中配置“${label}”地址。`);
    return;
  }

  const isCloudLink = label === CLOUD_LINK_LABEL;
  const targetUrl = isCloudLink || isDesktopApp ? rawUrl : toLocalResourceUrl(rawUrl);
  if (isDesktopApp) {
    try {
      const result = await window.huazaiDesktop.openResource({ label, url: targetUrl, isCloudLink });
      if (result?.ok === false) alert(result.message || `无法打开“${label}”。`);
    } catch (error) {
      alert(error.message || `无法打开“${label}”。`);
    }
    return;
  }

  const openedWindow = window.open(targetUrl, "_blank", "noopener,noreferrer");
  if (!openedWindow) alert(`浏览器阻止了“${label}”弹出窗口，请允许弹窗或使用桌面端。`);
}

function toLocalResourceUrl(rawUrl) {
  const url = rawUrl.trim();
  if (/^file:\/\//i.test(url)) return url;
  if (/^\\/.test(url)) {
    return `file://///${url.replace(/^\\+/, "").replaceAll("\\", "/")}`;
  }
  if (/^[a-zA-Z]:\\/.test(url)) {
    return `file:///${url.replaceAll("\\", "/")}`;
  }
  return url;
}

function moveCard(id, direction) {
  const index = products.findIndex((product) => product.id === id);
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= products.length) return;
  [products[index], products[targetIndex]] = [products[targetIndex], products[index]];
  persist();
  renderCards();
}

function dropCard(targetId) {
  if (!draggedId || draggedId === targetId) return;
  const draggedIndex = products.findIndex((product) => product.id === draggedId);
  const targetIndex = products.findIndex((product) => product.id === targetId);
  const [draggedProduct] = products.splice(draggedIndex, 1);
  products.splice(targetIndex, 0, draggedProduct);
  persist();
  renderCards();
}

function renderLinkFields() {
  linkFieldsEl.innerHTML = "";
  RESOURCE_BUTTONS.forEach((label) => {
    const field = document.createElement("label");
    field.textContent = label;
    const input = document.createElement("input");
    input.name = label;
    input.placeholder = label === CLOUD_LINK_LABEL ? "填写在线网盘分享 URL" : "填写本地 NAS / 共享盘文件夹路径";
    field.append(input);
    linkFieldsEl.append(field);
  });
}

function openDialog(id) {
  const product = products.find((item) => item.id === id) || normalizeProduct({ links: {} });
  document.querySelector("#dialogTitle").textContent = id ? "设置产品卡片" : "新建产品卡片";
  document.querySelector("#editingId").value = id || "";
  document.querySelector("#productName").value = id ? product.name : "";
  document.querySelector("#productPrice").value = id ? product.price : "";
  document.querySelector("#productImage").value = "";
  showPreview(id ? product.image : "");
  RESOURCE_BUTTONS.forEach((label) => {
    linkFieldsEl.querySelector(`[name="${label}"]`).value = id ? product.links[label] || "" : "";
  });
  document.querySelector("#deleteBtn").hidden = !id;
  dialog.showModal();
}

function showPreview(src) {
  imagePreviewEl.innerHTML = "";
  if (!src) {
    imagePreviewEl.textContent = "未上传图片时会显示默认占位图";
    return;
  }
  const img = document.createElement("img");
  img.src = src;
  img.alt = "产品图预览";
  imagePreviewEl.append(img);
}

function readImageFile(file) {
  return new Promise((resolve, reject) => {
    if (!file) return resolve(null);
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(reader.result));
    reader.addEventListener("error", reject);
    reader.readAsDataURL(file);
  });
}

async function saveCard() {
  const id = document.querySelector("#editingId").value;
  const existing = products.find((product) => product.id === id);
  const imageFile = document.querySelector("#productImage").files[0];
  const uploadedImage = await readImageFile(imageFile);
  const nextProduct = normalizeProduct({
    id: id || crypto.randomUUID(),
    name: document.querySelector("#productName").value.trim(),
    price: document.querySelector("#productPrice").value.trim(),
    image: uploadedImage || existing?.image || PLACEHOLDER_IMAGE,
    links: RESOURCE_BUTTONS.reduce((links, label) => {
      links[label] = linkFieldsEl.querySelector(`[name="${label}"]`).value.trim();
      return links;
    }, {})
  });

  if (!nextProduct.name) {
    document.querySelector("#productName").reportValidity();
    return;
  }

  if (existing) {
    products = products.map((product) => product.id === id ? nextProduct : product);
  } else {
    products = [nextProduct, ...products];
  }
  persist();
  renderCards();
  dialog.close();
}

function deleteCard() {
  const id = document.querySelector("#editingId").value;
  if (!id || !confirm("确认删除这张产品卡片吗？")) return;
  products = products.filter((product) => product.id !== id);
  persist();
  renderCards();
  dialog.close();
}

async function readSyncPayload(url) {
  if (isDesktopApp && !/^https?:\/\//i.test(url)) {
    return JSON.parse(await window.huazaiDesktop.readSyncFile(url));
  }
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`同步失败：${response.status}`);
  return response.json();
}

async function updateFromRemote() {
  const url = syncUrlEl.value.trim();
  if (!url) {
    alert("请先填写并保存团队同步地址。");
    return;
  }
  const payload = await readSyncPayload(url);
  const nextProducts = Array.isArray(payload) ? payload : payload.products;
  if (!Array.isArray(nextProducts)) throw new Error("同步文件格式错误，需要 products 数组。");
  products = nextProducts.map(normalizeProduct);
  persist({ publish: false });
  renderCards();
  setSyncStatus("更新完成，已同步最新产品卡片。");
  alert("更新完成，已同步最新产品卡片。");
}

function exportConfig() {
  const blob = new Blob([buildConfigPayload()], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "products.json";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importConfig(file) {
  if (!file) return;
  const payload = JSON.parse(await file.text());
  const nextProducts = Array.isArray(payload) ? payload : payload.products;
  if (!Array.isArray(nextProducts)) throw new Error("导入文件格式错误，需要 products 数组。");
  products = nextProducts.map(normalizeProduct);
  persist();
  renderCards();
}

function applyTheme(theme) {
  const nextTheme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = nextTheme;
  localStorage.setItem(THEME_KEY, nextTheme);
  themeToggleBtn.textContent = nextTheme === "dark" ? "浅色模式" : "深色模式";
}

function renderDesktopState() {
  document.documentElement.classList.toggle("is-desktop", isDesktopApp);
  if (!isDesktopApp) setSyncStatus("建议使用桌面端窗口运行；浏览器模式仅支持读取 HTTP/相对 JSON。 ");
}

async function chooseSyncFile() {
  if (!isDesktopApp) return;
  const filePath = await window.huazaiDesktop.chooseSyncFile();
  if (!filePath) return;
  syncUrlEl.value = filePath;
  localStorage.setItem(SYNC_KEY, filePath);
  await publishSharedConfig();
}

document.querySelector("#appSettingsBtn").addEventListener("click", () => document.querySelector("#settingsDialog").showModal());
themeToggleBtn.addEventListener("click", () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
document.querySelector("#newCardBtn").addEventListener("click", () => openDialog());
document.querySelector("#saveCardBtn").addEventListener("click", saveCard);
document.querySelector("#deleteBtn").addEventListener("click", deleteCard);
document.querySelector("#productImage").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) readImageFile(file).then(showPreview);
});
document.querySelector("#saveSyncBtn").addEventListener("click", () => {
  localStorage.setItem(SYNC_KEY, syncUrlEl.value.trim());
  publishSharedConfig().then((published) => {
    alert(published ? "同步地址已保存，当前配置已发布。" : "同步地址已保存；HTTP 地址支持更新读取，不能由客户端直接写回。");
  });
});
chooseSyncFileBtn.addEventListener("click", () => chooseSyncFile().catch((error) => alert(error.message)));
document.querySelector("#updateBtn").addEventListener("click", () => updateFromRemote().catch((error) => alert(error.message)));
document.querySelector("#exportBtn").addEventListener("click", exportConfig);
document.querySelector("#importInput").addEventListener("change", (event) => importConfig(event.target.files[0]).catch((error) => alert(error.message)));
form.addEventListener("submit", (event) => {
  if (event.submitter?.value === "cancel") return;
  event.preventDefault();
});
