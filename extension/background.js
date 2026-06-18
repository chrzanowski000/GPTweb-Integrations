"use strict";

const BACKEND_URL = "http://localhost:8000/process_formula";

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "GET_TAB_ID") {
    sendResponse({ tabId: sender.tab ? sender.tab.id : null });
    return;
  }

  // Content scripts cannot fetch http:// from an https:// page (mixed content).
  // The background script has no such restriction, so it proxies the request.
  if (message && message.type === "PROCESS_FORMULA") {
    fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message.payload),
    })
      .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
      .then(({ ok, data }) => sendResponse({ ok, data }))
      .catch((err) => sendResponse({ ok: false, data: { detail: err.message } }));

    return true; // keep channel open for async sendResponse
  }
});

// Remove closed tabs from the monitored list automatically.
browser.tabs.onRemoved.addListener((tabId) => {
  browser.storage.local.get("monitoredTabs").then(({ monitoredTabs = [] }) => {
    const updated = monitoredTabs.filter((id) => id !== tabId);
    if (updated.length !== monitoredTabs.length) {
      browser.storage.local.set({ monitoredTabs: updated });
    }
  });
});
