"use strict";

const TRIGGER = "#SAVE_FORMULA";

window.__formulaCache = [];
window.__processedTriggerCount = 0;

// ── Cache rebuild ────────────────────────────────────────────────────────────

function rebuildCache() {
  const allTurns = document.querySelectorAll("[data-message-author-role]");
  const cache = [];
  allTurns.forEach((el) => {
    const role = el.getAttribute("data-message-author-role");
    const content = el.innerText.trim();
    if (role && content) {
      cache.push({ role, content });
    }
  });
  window.__formulaCache = cache;
}

function countTriggers(cache) {
  return cache.filter((m) => m.role === "user" && m.content.includes(TRIGGER)).length;
}

// Returns only the last assistant message before the #SAVE_FORMULA trigger.
function getRelevantMessages() {
  const cache = window.__formulaCache;
  const lastAssistant = [...cache].reverse().find((m) => m.role === "assistant");
  return lastAssistant ? [lastAssistant] : [];
}

// ── Tab ID helper ────────────────────────────────────────────────────────────

async function getCurrentTabId() {
  return new Promise((resolve) => {
    browser.runtime.sendMessage({ type: "GET_TAB_ID" }, (response) => {
      resolve(response && response.tabId ? response.tabId : null);
    });
  });
}

// ── Trigger detection ────────────────────────────────────────────────────────

function checkTrigger() {
  const cache = window.__formulaCache;
  const currentCount = countTriggers(cache);

  if (currentCount <= window.__processedTriggerCount) return;

  // New trigger detected — update baseline immediately to prevent double-fire.
  window.__processedTriggerCount = currentCount;
  handleTrigger();
}

// ── Trigger handler ──────────────────────────────────────────────────────────

async function handleTrigger() {
  const tabId = await getCurrentTabId();
  const { monitoredTabs = [] } = await browser.storage.local.get("monitoredTabs");

  if (!monitoredTabs.includes(tabId)) return;

  const messages = getRelevantMessages();
  const chatTitle = document.title || "ChatGPT Conversation";

  browser.runtime.sendMessage(
    { type: "PROCESS_FORMULA", payload: { chat_title: chatTitle, messages } },
    ({ ok, data } = {}) => {
      if (!data) {
        showNotification("No response from backend", "error");
      } else if (ok && data.status === "ok") {
        showNotification(`Formula saved: ${data.formula_name}`, "success");
      } else {
        showNotification(data.detail || "Formula extraction failed", "error");
      }
    }
  );
}

// ── Notifications ────────────────────────────────────────────────────────────

function showNotification(message, type) {
  const existing = document.getElementById("__formula-archiver-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "__formula-archiver-toast";
  toast.textContent = message;

  const isSuccess = type === "success";
  Object.assign(toast.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    zIndex: "2147483647",
    padding: "12px 18px",
    borderRadius: "8px",
    fontFamily: "system-ui, sans-serif",
    fontSize: "14px",
    fontWeight: "600",
    color: "#fff",
    background: isSuccess ? "#2ecc71" : "#e74c3c",
    boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
    maxWidth: "320px",
    wordBreak: "break-word",
    transition: "opacity 0.4s ease",
    opacity: "1",
  });

  document.body.appendChild(toast);

  const dismissMs = isSuccess ? 4000 : 6000;
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, dismissMs);
}

// ── MutationObserver ─────────────────────────────────────────────────────────

function startObserver() {
  const container =
    document.querySelector("main") ||
    document.querySelector('[role="main"]') ||
    document.body;

  if (!container) {
    console.warn("[Formula Archiver] Could not find conversation container — retrying in 2s");
    setTimeout(startObserver, 2000);
    return;
  }

  const observer = new MutationObserver(() => {
    rebuildCache();
    checkTrigger();
  });

  observer.observe(container, { childList: true, subtree: true });

  // Build initial cache and set baseline trigger count so existing
  // #SAVE_FORMULA messages in history are never re-processed.
  rebuildCache();
  window.__processedTriggerCount = countTriggers(window.__formulaCache);
}

startObserver();
