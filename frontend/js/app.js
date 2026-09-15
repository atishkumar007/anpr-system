// Global App State
let webcamStream = null;
let isWebcamRunning = false;
let isScanning = false;

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setupInputModeTabs();
    setupFileUpload();
    setupWebcam();
    setupDirectSearch();
    setupApiModal();
    loadSamplePresets();

    // Default initial demonstration vehicle (PB10AB1234)
    fetchVehicleDetails('PB10AB1234');
});

// --- Tab Mode Switcher ---
function setupInputModeTabs() {
    const tabUpload = document.getElementById('tabUpload');
    const tabWebcam = document.getElementById('tabWebcam');
    const tabSamples = document.getElementById('tabSamples');

    const viewUpload = document.getElementById('viewUpload');
    const viewWebcam = document.getElementById('viewWebcam');
    const viewSamples = document.getElementById('viewSamples');

    function selectTab(activeTab, activeView) {
        [tabUpload, tabWebcam, tabSamples].forEach(t => {
            t.classList.remove('bg-white', 'text-brand-600', 'shadow-xs');
            t.classList.add('text-slate-600');
        });
        [viewUpload, viewWebcam, viewSamples].forEach(v => v.classList.add('hidden'));

        activeTab.classList.add('bg-white', 'text-brand-600', 'shadow-xs');
        activeTab.classList.remove('text-slate-600');
        activeView.classList.remove('hidden');
    }

    tabUpload?.addEventListener('click', () => selectTab(tabUpload, viewUpload));
    tabWebcam?.addEventListener('click', () => selectTab(tabWebcam, viewWebcam));
    tabSamples?.addEventListener('click', () => selectTab(tabSamples, viewSamples));
}

// --- Direct Plate Search ---
function setupDirectSearch() {
    const input = document.getElementById('directPlateInput');
    const btnSearch = document.getElementById('btnDirectSearch');

    const handleSearch = () => {
        const plate = input.value.trim().toUpperCase();
        if (plate) {
            fetchVehicleDetails(plate);
        }
    };

    btnSearch?.addEventListener('click', handleSearch);
    input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
}

// --- API Key Modal Settings ---
function setupApiModal() {
    const modal = document.getElementById('apiModal');
    const btnOpen = document.getElementById('btnOpenApiModal');
    const btnClose = document.getElementById('btnCloseApiModal');
    const btnCancel = document.getElementById('btnCancelApiModal');
    const form = document.getElementById('apiSettingsForm');

    btnOpen?.addEventListener('click', () => modal.classList.remove('hidden'));
    btnClose?.addEventListener('click', () => modal.classList.add('hidden'));
    btnCancel?.addEventListener('click', () => modal.classList.add('hidden'));

    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const rekorKey = document.getElementById('inputRekorKey').value;
        const rapidKey = document.getElementById('inputRapidApiKey').value;

        try {
            const res = await fetch('/api/vehicle/settings/apikey', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rekor_api_key: rekorKey, rapidapi_key: rapidKey })
            });
            if (res.ok) {
                alert("API Gateway settings updated!");
                modal.classList.add('hidden');
            }
        } catch (err) {
            alert("Error saving API keys: " + err.message);
        }
    });
}

// --- File Upload & Drag and Drop ---
function setupFileUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    dropzone?.addEventListener('click', () => fileInput.click());

    dropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-brand-500', 'bg-brand-50/50');
    });

    dropzone?.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-brand-500', 'bg-brand-50/50');
    });

    dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-brand-500', 'bg-brand-50/50');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            uploadAndRecognize(e.dataTransfer.files[0]);
        }
    });

    fileInput?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            uploadAndRecognize(e.target.files[0]);
        }
    });
}

async function uploadAndRecognize(file) {
    if (isScanning) return;
    setScanningStatus(true, "AI Processing: YOLO Detection + OCR...");

    const camSelect = document.getElementById('cameraSelector');
    const camId = camSelect ? camSelect.value : 'CAM-01';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', camId);

    try {
        const res = await fetch('/api/recognize/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        handleRecognitionResponse(data);
    } catch (err) {
        setScanningStatus(false, "Recognition failed: " + err.message);
    }
}

// --- Live Webcam Controls ---
function setupWebcam() {
    const btnToggle = document.getElementById('btnToggleWebcam');
    const btnCapture = document.getElementById('btnCaptureWebcam');
    const video = document.getElementById('webcamVideo');
    const prompt = document.getElementById('webcamPrompt');

    btnToggle?.addEventListener('click', async () => {
        if (!isWebcamRunning) {
            try {
                webcamStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 1280 }, height: { ideal: 720 } }
                });
                video.srcObject = webcamStream;
                video.classList.remove('hidden');
                prompt.classList.add('hidden');
                btnCapture.disabled = false;
                btnToggle.innerHTML = `<i data-lucide="video-off" class="w-3.5 h-3.5"></i> Stop Camera`;
                isWebcamRunning = true;
                lucide.createIcons();
            } catch (err) {
                alert("Could not access camera. Please check permissions.");
            }
        } else {
            if (webcamStream) {
                webcamStream.getTracks().forEach(t => t.stop());
            }
            video.classList.add('hidden');
            prompt.classList.remove('hidden');
            btnCapture.disabled = true;
            btnToggle.innerHTML = `<i data-lucide="video" class="w-3.5 h-3.5"></i> Start Camera`;
            isWebcamRunning = false;
            lucide.createIcons();
        }
    });

    btnCapture?.addEventListener('click', async () => {
        if (!isWebcamRunning || isScanning) return;
        setScanningStatus(true, "Capturing frame & extracting plate...");

        const camSelect = document.getElementById('cameraSelector');
        const camId = camSelect ? camSelect.value : 'CAM-01';

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64Img = canvas.toDataURL('image/jpeg', 0.9);

        try {
            const res = await fetch('/api/recognize/frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_base64: base64Img, source: camId })
            });
            const data = await res.json();
            handleRecognitionResponse(data);
        } catch (err) {
            setScanningStatus(false, "Capture failed: " + err.message);
        }
    });
}

// --- Sample Presets Loader ---
async function loadSamplePresets() {
    const grid = document.getElementById('samplePresetsGrid');
    if (!grid) return;

    try {
        const res = await fetch('/api/simulator/samples');
        if (res.ok) {
            const samples = await res.json();
            grid.innerHTML = '';
            samples.forEach(s => {
                const btn = document.createElement('button');
                btn.className = 'p-2.5 bg-slate-50 hover:bg-brand-50 border border-slate-200 hover:border-brand-300 rounded-xl text-left transition';
                btn.innerHTML = `
                    <span class="text-xs font-bold text-slate-800 block">${s.name}</span>
                    <span class="text-[10px] text-brand-600 font-semibold block mt-0.5">Click to scan</span>
                `;
                btn.onclick = () => triggerSampleScan(s.filename);
                grid.appendChild(btn);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function triggerSampleScan(filename) {
    setScanningStatus(true, "AI Model analyzing vehicle plate...");
    try {
        const res = await fetch(`/api/simulator/trigger?sample_filename=${encodeURIComponent(filename)}`, {
            method: 'POST'
        });
        const data = await res.json();
        handleRecognitionResponse(data);
    } catch (err) {
        setScanningStatus(false, "Sample scan error: " + err.message);
    }
}

// --- Recognition Response Handler ---
function handleRecognitionResponse(data) {
    setScanningStatus(false, data.success ? "Plate recognized successfully!" : "No plate detected");

    const plateText = document.getElementById('detectedPlateText');
    const conf = document.getElementById('detectedConfidence');
    const cropContainer = document.getElementById('cropPreviewContainer');
    const cropImg = document.getElementById('cropPreviewImg');

    if (data.success && data.plate_number) {
        plateText.textContent = data.plate_number;
        conf.textContent = `${Math.round(data.confidence * 100)}% Match`;

        // Update AI metadata HUD
        document.getElementById('detVehicleType').textContent = data.vehicle_type || "Car";
        document.getElementById('detVehicleColor').textContent = data.vehicle_color || "White";
        document.getElementById('detCameraDir').textContent = `${data.camera_id || 'CAM-01'} / ${data.direction || 'ENTRY'}`;
        document.getElementById('detAiEngine').textContent = `AI: ${data.ai_engine || 'Local YOLO + OCR'}`;
        document.getElementById('detLatency').textContent = `${data.processing_time_ms} ms`;

        if (data.plate_crop_url) {
            cropImg.src = data.plate_crop_url;
            cropContainer?.classList.remove('hidden');
        }

        // Render Vehicle Dossier
        if (data.vehicle_dossier) {
            renderVehicleDossier(data.vehicle_dossier);
        } else {
            fetchVehicleDetails(data.plate_number);
        }
    } else {
        plateText.textContent = "NOT DETECTED";
        conf.textContent = "0%";
    }
}

// --- Fetch & Render Full Vehicle Details & Challans ---
async function fetchVehicleDetails(plateNumber) {
    try {
        const res = await fetch(`/api/vehicle/details/${encodeURIComponent(plateNumber)}`);
        if (res.ok) {
            const data = await res.json();
            renderVehicleDossier(data);
            
            const input = document.getElementById('directPlateInput');
            if (input) input.value = plateNumber;
            const plateDisplay = document.getElementById('detectedPlateText');
            if (plateDisplay) plateDisplay.textContent = plateNumber;
        }
    } catch (err) {
        console.error("Failed to fetch vehicle details:", err);
    }
}

function renderVehicleDossier(dossier) {
    if (!dossier || !dossier.rc_details) return;

    const rc = dossier.rc_details;
    const challans = dossier.challan_summary || { total_challans: 0, unpaid_challans: 0, total_unpaid_amount: 0, challans: [] };

    // Overview Header
    document.getElementById('dossierPlateNumber').textContent = dossier.plate_number;
    document.getElementById('dossierStateBadge').textContent = rc.state || "State RTO";
    document.getElementById('dossierVehicleModel').textContent = rc.vehicle_model || rc.vehicle_make || "Vehicle Model";
    document.getElementById('dossierRtoName').textContent = rc.registration_authority || "Regional Transport Office";

    // Source Tag
    const sourceTag = document.getElementById('dossierSourceTag');
    if (sourceTag) {
        if (dossier.is_live_api) {
            sourceTag.className = "px-2.5 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-800 border border-emerald-300";
            sourceTag.textContent = "🟢 Live RTO Gateway";
        } else {
            sourceTag.className = "px-2.5 py-0.5 text-[10px] font-semibold rounded bg-slate-100 text-slate-600 border border-slate-200";
            sourceTag.textContent = "Parivahan RTO Service";
        }
    }

    // Insurance Badge
    const insBadge = document.getElementById('dossierInsuranceBadge');
    if (rc.insurance_details && rc.insurance_details.status === "Valid") {
        insBadge.className = "px-3 py-1 text-xs font-bold rounded-full acko-badge-green flex items-center gap-1";
        insBadge.innerHTML = `<i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Insurance Active`;
    } else {
        insBadge.className = "px-3 py-1 text-xs font-bold rounded-full acko-badge-red flex items-center gap-1";
        insBadge.innerHTML = `<i data-lucide="shield-alert" class="w-3.5 h-3.5"></i> Insurance Expired`;
    }

    // Specs Badges
    document.getElementById('specFuel').textContent = rc.fuel_type || "Petrol";
    document.getElementById('specClass').textContent = rc.vehicle_class || "LMV";
    document.getElementById('specEmission').textContent = rc.emission_norm || "BS6";
    document.getElementById('specRegDate').textContent = rc.registration_date || "--/--/----";

    // Owner Table
    document.getElementById('valOwnerName').textContent = rc.owner_name || "Registered Citizen";
    document.getElementById('valInsurer').textContent = rc.insurance_details?.provider || "Acko General Insurance";
    document.getElementById('valPolicyExpiry').textContent = `${rc.insurance_details?.policy_number || 'POL-N/A'} (Exp: ${rc.insurance_details?.expiry_date || 'N/A'})`;
    document.getElementById('valChassisEngine').textContent = `${rc.chassis_number || '••••'} / ${rc.engine_number || '••••'}`;

    // Traffic Challans
    const challanBadge = document.getElementById('challanCountBadge');
    const challanList = document.getElementById('challansList');
    const noChallanBox = document.getElementById('noChallansPlaceholder');

    challanList.innerHTML = '';

    if (challans.unpaid_challans > 0) {
        challanBadge.textContent = `${challans.unpaid_challans} Pending (₹${challans.total_unpaid_amount.toLocaleString()})`;
        challanBadge.className = "px-2.5 py-0.5 text-xs font-bold rounded-full acko-badge-red";
        noChallanBox?.classList.add('hidden');

        challans.challans.forEach(ch => {
            const card = document.createElement('div');
            card.className = "p-3.5 bg-white border border-slate-200 rounded-xl space-y-1.5 shadow-2xs";
            
            const isUnpaid = ch.status === 'UNPAID';
            const statusClass = isUnpaid ? 'acko-badge-red' : 'acko-badge-green';

            card.innerHTML = `
                <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-900">${ch.violation}</span>
                    <span class="font-extrabold text-slate-900 text-sm">₹${ch.amount.toLocaleString()}</span>
                </div>
                <div class="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-500 gap-1">
                    <span>${ch.location} • ${ch.date}</span>
                    <div class="flex items-center gap-2 mt-1 sm:mt-0">
                        <span class="font-mono text-[10px] text-slate-400">${ch.challan_number}</span>
                        <span class="px-2 py-0.5 text-[10px] font-bold rounded-full ${statusClass}">${ch.status}</span>
                    </div>
                </div>
            `;
            challanList.appendChild(card);
        });
    } else {
        challanBadge.textContent = `0 Pending Challans`;
        challanBadge.className = "px-2.5 py-0.5 text-xs font-bold rounded-full acko-badge-green";
        noChallanBox?.classList.remove('hidden');
    }

    lucide.createIcons();
}

// --- Helpers ---
function setScanningStatus(scanning, text) {
    isScanning = scanning;
    const badge = document.getElementById('scanStatusBadge');
    if (badge) {
        badge.textContent = text;
        if (scanning) {
            badge.className = "px-2.5 py-0.5 text-[11px] font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-200 animate-pulse";
        } else {
            badge.className = "px-2.5 py-0.5 text-[11px] font-semibold rounded-full acko-badge-purple";
        }
    }
}
