"use strict";

const btn = document.getElementById("toggleBtn");
const statusEl = document.getElementById("status");

async function getCurrentTabId() {
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  return tab ? tab.id : null;
}

async function render() {
  const tabId = await getCurrentTabId();
  if (!tabId) {
    statusEl.textContent = "Could not detect current tab.";
    return;
  }

  const { monitoredTabs = [] } = await browser.storage.local.get("monitoredTabs");
  const isMonitored = monitoredTabs.includes(tabId);

  if (isMonitored) {
    btn.textContent = "Stop Monitoring";
    btn.className = "stop";
    statusEl.textContent = `Tab ${tabId} is being monitored.`;
  } else {
    btn.textContent = "Monitor This Tab";
    btn.className = "monitor";
    statusEl.textContent = `Tab ${tabId} is not monitored.`;
  }
}

btn.addEventListener("click", async () => {
  const tabId = await getCurrentTabId();
  if (!tabId) return;

  const { monitoredTabs = [] } = await browser.storage.local.get("monitoredTabs");
  let updated;

  if (monitoredTabs.includes(tabId)) {
    updated = monitoredTabs.filter((id) => id !== tabId);
  } else {
    updated = [...monitoredTabs, tabId];
  }

  await browser.storage.local.set({ monitoredTabs: updated });
  await render();
});

render();
