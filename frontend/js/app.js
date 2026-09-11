// Global State
let currentTab = 'monitor';
let webcamStream = null;
let isWebcamActive = false;
let autoScanInterval = null;
let isProcessing = false;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setupTabNavigation();
    setupWebcamHandlers();
    setupSimulatorHandlers();
    setupFileUploadHandlers();
    setupVehicleRegistryHandlers();
    setupLogHandlers();
    setupManualBarrierControls();

    // Initialize Charts & Load Initial Data
    if (window.initCharts) window.initCharts();
    loadDashboardSummary();
    loadSampleVehiclesList();
    loadVehiclesTable();
    loadLogsTable();

    // Auto-refresh stats & barrier status every 3 seconds
    setInterval(() => {
        refreshBarrierStatus();
        if (currentTab === 'analytics') {
            window.updateChartsData();
        }
        loadDashboardSummary();
    }, 3000);
});

// --- Tab Navigation ---
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('[data-tab-target]');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab-target');
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('[data-tab-content]').forEach(content => {
        content.classList.add('hidden');
    });
    const activeContent = document.getElementById(`tab-${tabId}`);
    if (activeContent) activeContent.classList.remove('hidden');

    document.querySelectorAll('[data-tab-target]').forEach(btn => {
        if (btn.getAttribute('data-tab-target') === tabId) {
            btn.classList.add('bg-blue-600/20', 'text-blue-400', 'border-blue-500');
            btn.classList.remove('text-slate-400', 'border-transparent');
        } else {
            btn.classList.remove('bg-blue-600/20', 'text-blue-400', 'border-blue-500');
            btn.classList.add('text-slate-400', 'border-transparent');
        }
    });

    if (tabId === 'vehicles') loadVehiclesTable();
    if (tabId === 'logs') loadLogsTable();
    if (tabId === 'analytics') {
        if (window.updateChartsData) window.updateChartsData();
    }
}

// --- Webcam Support ---
function setupWebcamHandlers() {
    const startBtn = document.getElementById('btnStartWebcam');
    const stopBtn = document.getElementById('btnStopWebcam');
    const scanBtn = document.getElementById('btnScanWebcamFrame');
    const videoElem = document.getElementById('webcamVideo');
    const placeholder = document.getElementById('webcamPlaceholder');

    startBtn?.addEventListener('click', async () => {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } }
            });
            videoElem.srcObject = webcamStream;
            videoElem.classList.remove('hidden');
            placeholder.classList.add('hidden');
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            scanBtn.classList.remove('hidden');
            isWebcamActive = true;
            showNotification('Webcam connected successfully', 'success');
        } catch (err) {
            console.error(err);
            showNotification('Could not access webcam. Ensure permissions are granted.', 'error');
        }
    });

    stopBtn?.addEventListener('click', () => {
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
        }
        videoElem.classList.add('hidden');
        placeholder.classList.remove('hidden');
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        scanBtn.classList.add('hidden');
        isWebcamActive = false;
    });

    scanBtn?.addEventListener('click', () => {
        captureAndRecognizeWebcamFrame();
    });
}

async function captureAndRecognizeWebcamFrame() {
    if (!isWebcamActive || isProcessing) return;
    const video = document.getElementById('webcamVideo');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Img = canvas.toDataURL('image/jpeg', 0.9);

    await processRecognitionPayload('/api/recognize/frame', {
        image_base64: base64Img,
        source: 'WEBCAM'
    });
}

// --- File Upload & Drag-and-Drop ---
function setupFileUploadHandlers() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    dropzone?.addEventListener('click', () => fileInput.click());

    dropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-blue-500', 'bg-blue-500/10');
    });

    dropzone?.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-blue-500', 'bg-blue-500/10');
    });

    dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-blue-500', 'bg-blue-500/10');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    if (isProcessing) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', 'FILE_UPLOAD');

    setScanningState(true);
    try {
        const res = await fetch('/api/recognize/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        renderRecognitionResult(data);
        loadDashboardSummary();
    } catch (err) {
        showNotification('Recognition failed: ' + err.message, 'error');
    } finally {
        setScanningState(false);
    }
}

// --- Virtual IoT Simulator Handlers ---
function setupSimulatorHandlers() {
    const btnSimulateRandom = document.getElementById('btnSimulateRandom');
    const sampleSelect = document.getElementById('sampleVehicleSelect');
    const btnSimulateSelected = document.getElementById('btnSimulateSelected');
    const autoSimToggle = document.getElementById('autoSimToggle');

    btnSimulateRandom?.addEventListener('click', async () => {
        await triggerSimulation();
    });

    btnSimulateSelected?.addEventListener('click', async () => {
        const val = sampleSelect.value;
        await triggerSimulation(val || null);
    });

    autoSimToggle?.addEventListener('change', (e) => {
        if (e.target.checked) {
            autoScanInterval = setInterval(() => triggerSimulation(), 6000);
            showNotification('Auto-simulation feed started (every 6s)', 'info');
        } else {
            if (autoScanInterval) clearInterval(autoScanInterval);
            showNotification('Auto-simulation feed stopped', 'info');
        }
    });
}

async function loadSampleVehiclesList() {
    try {
        const res = await fetch('/api/simulator/samples');
        if (res.ok) {
            const list = await res.json();
            const select = document.getElementById('sampleVehicleSelect');
            if (select) {
                select.innerHTML = '<option value="">-- Random Vehicle --</option>';
                list.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item.filename;
                    opt.textContent = `${item.name}`;
                    select.appendChild(opt);
                });
            }
        }
    } catch (err) {
        console.error("Failed to load sample vehicles:", err);
    }
}

async function triggerSimulation(filename = null) {
    if (isProcessing) return;
    setScanningState(true);
    try {
        let url = '/api/simulator/trigger';
        if (filename) url += `?sample_filename=${encodeURIComponent(filename)}`;
        const res = await fetch(url, { method: 'POST' });
        const data = await res.json();
        renderRecognitionResult(data);
        loadDashboardSummary();
    } catch (err) {
        showNotification('Simulator trigger failed: ' + err.message, 'error');
    } finally {
        setScanningState(false);
    }
}

// --- Core API Processor ---
async function processRecognitionPayload(endpoint, bodyData) {
    setScanningState(true);
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        const data = await res.json();
        renderRecognitionResult(data);
        loadDashboardSummary();
    } catch (err) {
        showNotification('Processing error: ' + err.message, 'error');
    } finally {
        setScanningState(false);
    }
}

// --- Render Recognition Output UI ---
function renderRecognitionResult(result) {
    const resultCard = document.getElementById('latestResultCard');
    const plateTextElem = document.getElementById('resPlateNumber');
    const statusBadge = document.getElementById('resStatusBadge');
    const gateBadge = document.getElementById('resGateBadge');
    const confElem = document.getElementById('resConfidence');
    const ownerElem = document.getElementById('resOwner');
    const latencyElem = document.getElementById('resLatency');
    const snapshotImg = document.getElementById('resSnapshot');
    const cropImg = document.getElementById('resPlateCrop');

    if (!resultCard) return;

    if (!result.success || !result.plate_number) {
        plateTextElem.textContent = 'NO PLATE DETECTED';
        plateTextElem.className = 'font-mono-plate text-2xl font-extrabold text-slate-500';
        statusBadge.textContent = 'NOT DETECTED';
        statusBadge.className = 'px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-700 text-slate-300';
        gateBadge.textContent = 'GATE LOCKED';
        gateBadge.className = 'px-2.5 py-1 text-xs font-semibold rounded-md bg-red-900/50 text-red-400 border border-red-800';
        confElem.textContent = '0%';
        ownerElem.textContent = 'N/A';
        latencyElem.textContent = `${result.processing_time_ms} ms`;
        if (result.image_url) snapshotImg.src = result.image_url;
        cropImg.classList.add('hidden');
        return;
    }

    plateTextElem.textContent = result.plate_number;
    confElem.textContent = `${Math.round(result.confidence * 100)}%`;
    latencyElem.textContent = `${result.processing_time_ms} ms`;
    ownerElem.textContent = result.owner_name ? `${result.owner_name} (${result.vehicle_model || ''})` : 'Unregistered Visitor';

    // Status Styling
    if (result.status === 'AUTHORIZED') {
        plateTextElem.className = 'font-mono-plate text-3xl font-black text-emerald-400 tracking-wider';
        statusBadge.textContent = 'AUTHORIZED';
        statusBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-emerald-900/60 text-emerald-300 border border-emerald-500/40 animate-pulse';
        gateBadge.textContent = 'BARRIER OPENED';
        gateBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-emerald-900/60 text-emerald-300 border border-emerald-500/40';
        animateBarrierGate('OPEN');
    } else if (result.status === 'BLACKLISTED') {
        plateTextElem.className = 'font-mono-plate text-3xl font-black text-red-500 tracking-wider';
        statusBadge.textContent = 'BLACKLISTED / ALERT';
        statusBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-red-900/70 text-red-300 border border-red-500';
        gateBadge.textContent = 'ACCESS DENIED';
        gateBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-red-900/70 text-red-300 border border-red-500';
        animateBarrierGate('CLOSED');
    } else {
        plateTextElem.className = 'font-mono-plate text-3xl font-black text-amber-400 tracking-wider';
        statusBadge.textContent = 'UNAUTHORIZED';
        statusBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-amber-900/60 text-amber-300 border border-amber-500/40';
        gateBadge.textContent = 'ACCESS DENIED';
        gateBadge.className = 'px-3 py-1 text-xs font-bold rounded-md bg-red-900/60 text-red-400 border border-red-800';
        animateBarrierGate('CLOSED');
    }

    if (result.image_url) {
        snapshotImg.src = result.image_url;
        snapshotImg.classList.remove('hidden');
    }
    if (result.plate_crop_url) {
        cropImg.src = result.plate_crop_url;
        cropImg.classList.remove('hidden');
    } else {
        cropImg.classList.add('hidden');
    }
}

// --- Barrier Gate Status & Animations ---
function animateBarrierGate(state) {
    const gateArm = document.getElementById('barrierArmVisual');
    const gateText = document.getElementById('barrierStatusText');
    const gateLed = document.getElementById('barrierStatusLed');

    if (state === 'OPEN') {
        gateArm?.classList.add('open');
        if (gateText) gateText.textContent = 'BARRIER OPEN';
        if (gateLed) {
            gateLed.className = 'w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-ping';
        }
    } else {
        gateArm?.classList.remove('open');
        if (gateText) gateText.textContent = 'BARRIER CLOSED';
        if (gateLed) {
            gateLed.className = 'w-3 h-3 rounded-full bg-red-500 shadow-lg shadow-red-500/50';
        }
    }
}

async function refreshBarrierStatus() {
    try {
        const res = await fetch('/api/simulator/barrier/status');
        if (res.ok) {
            const data = await res.json();
            animateBarrierGate(data.state);
        }
    } catch (e) { }
}

function setupManualBarrierControls() {
    document.getElementById('btnGateOverrideOpen')?.addEventListener('click', async () => {
        await fetch('/api/simulator/barrier/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'OPEN' })
        });
        animateBarrierGate('OPEN');
        showNotification('Manual Override: Barrier OPENED (Auto-closes in 5s)', 'info');
    });

    document.getElementById('btnGateOverrideClose')?.addEventListener('click', async () => {
        await fetch('/api/simulator/barrier/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'CLOSE' })
        });
        animateBarrierGate('CLOSED');
        showNotification('Manual Override: Barrier CLOSED', 'info');
    });
}

// --- Summary Counters & Dashboard Stats ---
async function loadDashboardSummary() {
    try {
        const res = await fetch('/api/logs/stats');
        if (res.ok) {
            const stats = await res.json();
            document.getElementById('statTotalScans').textContent = stats.total_scans;
            document.getElementById('statTodayScans').textContent = stats.today_scans;
            document.getElementById('statAuthorized').textContent = stats.authorized_count;
            document.getElementById('statUnauthorized').textContent = stats.unauthorized_count + stats.blacklisted_count;
            document.getElementById('statRegistered').textContent = stats.registered_vehicles_count;
        }
    } catch (err) {
        console.error("Failed to load dashboard summary:", err);
    }
}

// --- Vehicle Registry CRUD ---
function setupVehicleRegistryHandlers() {
    const modal = document.getElementById('vehicleModal');
    const btnOpenAdd = document.getElementById('btnOpenAddVehicle');
    const btnClose = document.getElementById('btnCloseVehicleModal');
    const form = document.getElementById('vehicleForm');
    const searchInput = document.getElementById('vehicleSearchInput');
    const tierFilter = document.getElementById('vehicleTierFilter');

    btnOpenAdd?.addEventListener('click', () => {
        form.reset();
        modal.classList.remove('hidden');
    });

    btnClose?.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            plate_number: document.getElementById('inputPlate').value,
            owner_name: document.getElementById('inputOwner').value,
            vehicle_model: document.getElementById('inputModel').value,
            access_tier: document.getElementById('inputTier').value,
            notes: document.getElementById('inputNotes').value
        };

        try {
            const res = await fetch('/api/vehicles/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showNotification('Vehicle registered successfully!', 'success');
                modal.classList.add('hidden');
                loadVehiclesTable();
                loadDashboardSummary();
            } else {
                const err = await res.json();
                showNotification(err.detail || 'Registration failed', 'error');
            }
        } catch (err) {
            showNotification(err.message, 'error');
        }
    });

    searchInput?.addEventListener('input', () => loadVehiclesTable());
    tierFilter?.addEventListener('change', () => loadVehiclesTable());
}

async function loadVehiclesTable() {
    const query = document.getElementById('vehicleSearchInput')?.value || '';
    const tier = document.getElementById('vehicleTierFilter')?.value || '';
    let url = `/api/vehicles/?query=${encodeURIComponent(query)}`;
    if (tier) url += `&access_tier=${encodeURIComponent(tier)}`;

    try {
        const res = await fetch(url);
        if (res.ok) {
            const list = await res.json();
            const tbody = document.getElementById('vehiclesTableBody');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-slate-500">No registered vehicles found.</td></tr>`;
                return;
            }

            list.forEach(v => {
                let badgeClass = 'bg-emerald-900/50 text-emerald-300 border border-emerald-600/30';
                if (v.access_tier === 'BLACKLIST') badgeClass = 'bg-red-900/50 text-red-300 border border-red-600/30';
                if (v.access_tier === 'GUEST') badgeClass = 'bg-blue-900/50 text-blue-300 border border-blue-600/30';

                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-800 hover:bg-slate-800/40 transition-colors';
                tr.innerHTML = `
                    <td class="py-3 px-4 font-mono-plate font-bold text-slate-100">${v.plate_number}</td>
                    <td class="py-3 px-4 text-slate-200">${v.owner_name}</td>
                    <td class="py-3 px-4 text-slate-400 text-sm">${v.vehicle_model || '—'}</td>
                    <td class="py-3 px-4"><span class="px-2.5 py-0.5 text-xs font-semibold rounded-full ${badgeClass}">${v.access_tier}</span></td>
                    <td class="py-3 px-4 text-right">
                        <button onclick="deleteVehicle(${v.id})" class="p-1.5 text-slate-400 hover:text-red-400 rounded hover:bg-red-500/10 transition-colors">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        }
    } catch (err) {
        console.error("Failed to load vehicles:", err);
    }
}

async function deleteVehicle(id) {
    if (!confirm('Are you sure you want to remove this vehicle from the registry?')) return;
    try {
        const res = await fetch(`/api/vehicles/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showNotification('Vehicle deleted', 'info');
            loadVehiclesTable();
            loadDashboardSummary();
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}
window.deleteVehicle = deleteVehicle;

// --- Access Logs & Search ---
function setupLogHandlers() {
    const searchInput = document.getElementById('logSearchInput');
    const statusFilter = document.getElementById('logStatusFilter');
    const btnExport = document.getElementById('btnExportLogs');
    const btnClear = document.getElementById('btnClearLogs');

    searchInput?.addEventListener('input', () => loadLogsTable());
    statusFilter?.addEventListener('change', () => loadLogsTable());

    btnExport?.addEventListener('click', () => {
        window.location.href = '/api/logs/export/csv';
    });

    btnClear?.addEventListener('click', async () => {
        if (!confirm('Clear all access detection logs?')) return;
        try {
            await fetch('/api/logs/clear', { method: 'DELETE' });
            showNotification('Logs cleared', 'info');
            loadLogsTable();
            loadDashboardSummary();
        } catch (err) {
            showNotification(err.message, 'error');
        }
    });
}

async function loadLogsTable() {
    const plate = document.getElementById('logSearchInput')?.value || '';
    const status = document.getElementById('logStatusFilter')?.value || '';
    let url = `/api/logs/?limit=50`;
    if (plate) url += `&plate=${encodeURIComponent(plate)}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;

    try {
        const res = await fetch(url);
        if (res.ok) {
            const list = await res.json();
            const tbody = document.getElementById('logsTableBody');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">No detection logs recorded yet.</td></tr>`;
                return;
            }

            list.forEach(log => {
                const dateStr = new Date(log.timestamp).toLocaleString();
                let statusBadge = 'bg-emerald-900/50 text-emerald-300 border border-emerald-500/30';
                if (log.status === 'BLACKLISTED') statusBadge = 'bg-red-900/50 text-red-300 border border-red-500/30';
                if (log.status === 'UNAUTHORIZED') statusBadge = 'bg-amber-900/50 text-amber-300 border border-amber-500/30';

                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-800 hover:bg-slate-800/40 transition-colors';
                tr.innerHTML = `
                    <td class="py-3 px-4 text-xs text-slate-400 font-mono">${dateStr}</td>
                    <td class="py-3 px-4 font-mono-plate font-bold text-slate-100">${log.plate_number}</td>
                    <td class="py-3 px-4 text-sm text-slate-300">${Math.round((log.confidence || 0) * 100)}%</td>
                    <td class="py-3 px-4"><span class="px-2.5 py-0.5 text-xs font-semibold rounded-full ${statusBadge}">${log.status}</span></td>
                    <td class="py-3 px-4 text-xs text-slate-300 font-medium">${log.gate_action}</td>
                    <td class="py-3 px-4 text-xs text-slate-400">${log.notes || log.source}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load logs:", err);
    }
}

// --- Utilities & UI Helpers ---
function setScanningState(scanning) {
    isProcessing = scanning;
    const indicator = document.getElementById('scanningIndicator');
    if (indicator) {
        if (scanning) indicator.classList.remove('hidden');
        else indicator.classList.add('hidden');
    }
}

function showNotification(msg, type = 'info') {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-emerald-600 text-white',
        error: 'bg-red-600 text-white',
        info: 'bg-blue-600 text-white'
    };
    toast.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg shadow-xl text-sm font-medium transition-all duration-300 transform translate-y-4 opacity-0 ${colors[type] || colors.info}`;
    toast.textContent = msg;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('translate-y-4', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('translate-y-4', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
