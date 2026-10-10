/**
 * VIKRAM AI - System Telemetry & Diagnostics
 * Updates live HUD gauges for CPU, RAM, GPU, Storage, Battery, and Network.
 */

class DiagnosticsManager {
  constructor() {
    this.initTelemetry();
  }

  initTelemetry() {
    // Initial fetch via REST API
    this.fetchTelemetry();
  }

  async fetchTelemetry() {
    try {
      const res = await fetch('/api/telemetry');
      const data = await res.json();
      this.updateUI(data);
    } catch (e) {
      console.warn('Telemetry poll notice:', e);
    }
  }

  updateUI(data) {
    if (!data) return;

    // CPU
    if (data.cpu) {
      const cpuVal = document.getElementById('tele-cpu-val');
      const cpuFill = document.getElementById('tele-cpu-fill');
      if (cpuVal) cpuVal.innerText = `${data.cpu.percent}%`;
      if (cpuFill) cpuFill.style.width = `${Math.min(100, data.cpu.percent)}%`;
    }

    // RAM
    if (data.ram) {
      const ramVal = document.getElementById('tele-ram-val');
      const ramFill = document.getElementById('tele-ram-fill');
      const ramSub = document.getElementById('tele-ram-sub');
      if (ramVal) ramVal.innerText = `${data.ram.percent}%`;
      if (ramFill) ramFill.style.width = `${Math.min(100, data.ram.percent)}%`;
      if (ramSub) ramSub.innerText = `${data.ram.used_gb} / ${data.ram.total_gb} GB`;
    }

    // GPU
    if (data.gpu) {
      const gpuVal = document.getElementById('tele-gpu-val');
      const gpuFill = document.getElementById('tele-gpu-fill');
      if (gpuVal) gpuVal.innerText = `${data.gpu.percent}%`;
      if (gpuFill) gpuFill.style.width = `${Math.min(100, data.gpu.percent)}%`;
    }

    // Storage
    if (data.storage) {
      const diskVal = document.getElementById('tele-disk-val');
      const diskFill = document.getElementById('tele-disk-fill');
      const diskSub = document.getElementById('tele-disk-sub');
      if (diskVal) diskVal.innerText = `${data.storage.percent}%`;
      if (diskFill) diskFill.style.width = `${Math.min(100, data.storage.percent)}%`;
      if (diskSub) diskSub.innerText = `${data.storage.free_gb} GB Free`;
    }

    // Battery
    if (data.battery) {
      const batVal = document.getElementById('tele-battery-val');
      const batFill = document.getElementById('tele-battery-fill');
      const batSub = document.getElementById('tele-battery-sub');
      if (batVal) batVal.innerText = `${data.battery.percent}%`;
      if (batFill) batFill.style.width = `${Math.min(100, data.battery.percent)}%`;
      if (batSub) batSub.innerText = data.battery.is_charging ? 'Charging (AC)' : 'On Battery';
    }

    // Network (Online / Offline Laptop Control)
    if (data.network) {
      const netVal = document.getElementById('tele-net-val');
      const netSub = document.getElementById('tele-net-sub');
      if (netVal) {
        if (data.network.is_online) {
          netVal.innerText = 'ONLINE';
          netVal.style.color = 'var(--success-green)';
          if (netSub) netSub.innerText = 'Connected + Full Laptop Control';
        } else {
          netVal.innerText = 'OFFLINE (LOCAL)';
          netVal.style.color = 'var(--cyan-bright)';
          if (netSub) netSub.innerText = '100% Offline Laptop Control Active';
        }
      }
    }
  }
}

window.diagnostics = null;
document.addEventListener('DOMContentLoaded', () => {
  window.diagnostics = new DiagnosticsManager();
});
