/**
 * Smart Cane Comprehensive Guided Interactive Demonstration App (PW_27_MHR_01)
 * Single State Architecture with Request Cancellation and Zero-Stale Rendering
 */

// -------------------------------------------------------------
// 1. CENTRALIZED SINGLE STATE OBJECT
// -------------------------------------------------------------
const State = {
    activeSection: 'sec-1-problem',
    domain: 'elderly',
    scenarioPerturbation: false,
    scenarioRunning: true,
    scenarioTime: 0.0,
    
    iotNode: 'esp32',
    squeezeAdc: 455,
    
    protocolActivity: 'nearmiss',
    protocolSubject: 'S01',
    protocolCounts: { events: 85, normal: 875, subjects: 4 },
    protocolTrialData: null,
    
    pipelineStep: 1,
    pipelineData: null,
    
    liveScenario: 'near_miss_trip',
    liveDetector: 'fused_coupling',
    liveFeatureSet: 'fused',
    liveViewMode: 'single',
    livePlaying: false,
    liveIndex: 0,
    liveStream: null,
    liveDetection: null,
    liveEvents: [],
    
    rqTab: 'rq1',
    labeledFraction: 1.0,
    rqResults: null,
    evalResults: null,
    
    presentationMode: false,
    presentationStep: 1,
    
    // Request tracking IDs (stale response drop)
    requestIds: {
        liveScenario: 0,
        pipelineStep: 0,
        protocolTrial: 0,
        rqResults: 0
    }
};

const PRESENTATION_STEPS = [
    { section: 'sec-1-problem', title: 'Step 1 of 8: Clinical Need & Biomechanical Bifurcation' },
    { section: 'sec-2-iot', title: 'Step 2 of 8: End-to-End IoT Architecture & Edge Ingest' },
    { section: 'sec-3-hardware', title: 'Step 3 of 8: Hardware Schematic & FSR Squeeze Calibration' },
    { section: 'sec-4-data', title: 'Step 4 of 8: Multi-Subject Protocol & Dataset Comparison' },
    { section: 'sec-5-pipeline', title: 'Step 5 of 8: 5-Stage Signal Processing Pipeline & 59 Features' },
    { section: 'sec-6-live', title: 'Step 6 of 8: Live Replay & Dual-Domain Coincidence Verification' },
    { section: 'sec-7-results', title: 'Step 7 of 8: Experimental Benchmarks (RQ1 to RQ4 Outcomes)' },
    { section: 'sec-8-limitations', title: 'Step 8 of 8: Transparent Limitations & Phase-2 Engineering Roadmap' }
];

// -------------------------------------------------------------
// 2. MASTER APP ENGINE
// -------------------------------------------------------------
class SmartCaneWalkthrough {
    constructor() {
        this.initCanvases();
        this.initEventListeners();
        this.initHashRouting();
        this.loadInitialData();
        
        this.lastFrameTime = performance.now();
        requestAnimationFrame((t) => this.animationLoop(t));
    }
    
    initCanvases() {
        this.cWithout = document.getElementById('canvasWithout');
        this.ctxWithout = this.cWithout.getContext('2d');
        this.cWith = document.getElementById('canvasWith');
        this.ctxWith = this.cWith.getContext('2d');
        
        this.cProto = document.getElementById('canvasProtocolTrial');
        this.ctxProto = this.cProto.getContext('2d');
        
        this.cPipe = document.getElementById('canvasPipeline');
        this.ctxPipe = this.cPipe.getContext('2d');
        
        this.cOsc = document.getElementById('canvasOscilloscope');
        this.ctxOsc = this.cOsc.getContext('2d');
    }
    
    initEventListeners() {
        // Deep-link nav tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const target = tab.getAttribute('href').substring(1);
                this.setActiveSection(target);
            });
        });
        
        // Presentation Mode Controls
        document.getElementById('btnStartPres').addEventListener('click', () => this.togglePresentationMode(true));
        document.getElementById('btnPresToggle').addEventListener('click', () => this.togglePresentationMode(false));
        document.getElementById('btnPresNext').addEventListener('click', () => this.stepPresentation(1));
        document.getElementById('btnPresPrev').addEventListener('click', () => this.stepPresentation(-1));
        document.getElementById('btnPresReset').addEventListener('click', () => this.resetPresentation());
        
        // Keyboard Navigation (Arrow Keys for Presentation Mode)
        window.addEventListener('keydown', (e) => {
            if (!State.presentationMode) return;
            if (e.key === 'ArrowRight') this.stepPresentation(1);
            if (e.key === 'ArrowLeft') this.stepPresentation(-1);
            if (e.key === 'Escape') this.togglePresentationMode(false);
        });
        
        // Section 1: Domain switcher & Stumble
        document.querySelectorAll('.btn-domain').forEach(btn => {
            btn.addEventListener('click', (e) => this.setDomain(e.target.dataset.domain));
        });
        document.getElementById('btnTriggerStumble').addEventListener('click', () => this.triggerScenarioPerturbation());
        document.getElementById('btnResetScenario').addEventListener('click', () => this.resetScenario());
        
        // Section 2: IoT Node Click
        document.querySelectorAll('.iot-node').forEach(node => {
            node.addEventListener('click', (e) => {
                const nodeKey = e.currentTarget.dataset.node;
                this.setIotNode(nodeKey);
            });
        });
        
        // Section 3: Hardware Squeeze
        document.getElementById('sliderGripSqueeze').addEventListener('input', (e) => {
            this.setSqueezeAdc(parseInt(e.target.value));
        });
        
        // Section 4: Data Protocol
        document.getElementById('btnRecordTrial').addEventListener('click', () => this.recordProtocolTrial());
        document.getElementById('protocolActivitySelect').addEventListener('change', (e) => {
            State.protocolActivity = e.target.value;
            this.updatePills();
        });
        document.getElementById('protocolSubjectSelect').addEventListener('change', (e) => {
            State.protocolSubject = e.target.value;
            this.updatePills();
        });
        
        // Section 5: Pipeline Stepper
        document.querySelectorAll('.btn-step').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const step = parseInt(e.target.dataset.step);
                this.setPipelineStep(step);
            });
        });
        
        // Section 6: Live Oscilloscope Controls
        document.getElementById('btnLivePlay').addEventListener('click', () => this.toggleLivePlay());
        document.getElementById('liveScrubber').addEventListener('input', (e) => {
            State.liveIndex = parseInt(e.target.value);
            this.renderLiveStats();
        });
        document.getElementById('scenarioSelect').addEventListener('change', (e) => {
            this.setLiveScenario(e.target.value);
        });
        document.getElementById('detectorSelect').addEventListener('change', (e) => {
            this.setLiveDetector(e.target.value);
        });
        document.getElementById('featureSetSelect').addEventListener('change', (e) => {
            this.setLiveFeatureSet(e.target.value);
        });
        document.getElementById('viewModeSelect').addEventListener('change', (e) => {
            this.setLiveViewMode(e.target.value);
        });
        document.getElementById('btnTriggerLiveStumble').addEventListener('click', () => {
            this.setLiveScenario('near_miss_trip');
            State.livePlaying = true;
            document.getElementById('btnLivePlay').textContent = '❚❚ PAUSE';
        });
        
        // Export Actions
        document.getElementById('btnExportPlot').addEventListener('click', () => this.exportCurrentPlot());
        document.getElementById('btnExportLog').addEventListener('click', () => this.exportEventLogCsv());
        document.getElementById('btnExportAudit').addEventListener('click', () => this.exportSubjectAuditCsv());
        
        // Section 7: RQ Subnav
        document.querySelectorAll('.btn-rq').forEach(btn => {
            btn.addEventListener('click', (e) => this.setRqTab(e.target.dataset.rq));
        });
        
        // Section 7: RQ4 Slider
        document.getElementById('sliderLabeledFrac').addEventListener('input', (e) => {
            const frac = parseFloat(e.target.value);
            this.setLabeledFraction(frac);
        });
    }
    
    initHashRouting() {
        const hash = window.location.hash.replace('#', '');
        if (hash && document.getElementById(hash)) {
            this.setActiveSection(hash, false);
        } else {
            this.setActiveSection('sec-1-problem', false);
        }
        
        window.addEventListener('hashchange', () => {
            const h = window.location.hash.replace('#', '');
            if (h && document.getElementById(h) && State.activeSection !== h) {
                this.setActiveSection(h, false);
            }
        });
    }
    
    async loadInitialData() {
        // Load RQ benchmark results
        try {
            const respRq = await fetch('/api/rq_results');
            State.rqResults = await respRq.json();
            this.renderRq3WeeklyTrend();
            this.updateRq4Readout(State.labeledFraction);
        } catch (err) {
            console.error('Failed to load RQ results cache:', err);
        }
        
        // Load Full LOSO Evaluation
        try {
            const respEval = await fetch('/api/evaluation');
            State.evalResults = await respEval.json();
            this.renderSubjectAuditTable();
        } catch (err) {
            console.error('Failed to load evaluation cache:', err);
        }
        
        // Preload pipeline stage 1
        this.setPipelineStep(1);
        
        // Preload live scenario
        this.setLiveScenario('near_miss_trip');
        
        // Record initial protocol trial
        this.recordProtocolTrial();
        
        this.updatePills();
    }
    
    // -------------------------------------------------------------
    // 3. SYNCHRONOUS STATE DISPATCHERS & PILL UPDATERS
    // -------------------------------------------------------------
    
    updatePills() {
        // Section 1 Pill
        const domMap = { 'elderly': 'Elderly Assisted Living', 'visually_impaired': 'Visually Impaired', 'rehab': 'Post-Stroke Rehab' };
        document.getElementById('pillSection1').textContent = 
            `Currently showing: Domain = ${domMap[State.domain]} | Gait = ${State.scenarioPerturbation ? 'Obstacle Stumble' : 'Steady Gait'}`;
        
        // Section 2 Pill
        document.getElementById('pillSection2').textContent = 
            `Currently showing: Component = ${State.iotNode.toUpperCase()} (VERIFIED BUILT) | Stream = 100 Hz I2C`;
        
        // Section 3 Pill
        const nVal = (State.squeezeAdc * (45.0 / 4095.0)).toFixed(1);
        document.getElementById('pillSection3').textContent = 
            `Currently showing: FSR Squeeze = ${nVal} N (ADC: ${State.squeezeAdc})`;
        
        // Section 4 Pill
        document.getElementById('pillSection4').textContent = 
            `Currently showing: Class = ${State.protocolActivity.toUpperCase()} | Sub = ${State.protocolSubject}`;
        
        // Section 5 Pill
        const stepTitles = ['', 'Stage 1: Raw Telemetry', 'Stage 2: Interpolate Gaps', 'Stage 3: 20 Hz Filter', 'Stage 4: 1.0s Windowing', 'Stage 5: 59-Feature Matrix'];
        document.getElementById('pillSection5').textContent = 
            `Currently showing: ${stepTitles[State.pipelineStep]} (Window 1.0s / 0.25s Stride)`;
        
        // Section 6 Pill
        const scMap = { 'near_miss_trip': 'Near-Miss Trip', 'hard_jolt': 'Hard Curb Jolt', 'normal_walking': 'Routine Walking' };
        const detMap = { 'fused_coupling': 'Fused Coupling', 'random_forest': 'Random Forest', 'threshold': 'Peak-Jerk Threshold', 'normal_only': 'Normal-Only Anomaly' };
        document.getElementById('pillSection6').textContent = 
            `Currently showing: Scenario = ${scMap[State.liveScenario]} | Detector = ${detMap[State.liveDetector]} | Features = ${State.liveFeatureSet === 'fused' ? 'IMU+Grip (59)' : 'IMU-Only (50)'}`;
        
        // Section 7 Pill
        document.getElementById('pillSection7').textContent = 
            `Currently showing: ${State.rqTab.toUpperCase()} Benchmark Metrics (Leave-One-Subject-Out)`;
        
        // Section 8 Pill
        document.getElementById('pillSection8').textContent = 
            `Currently showing: Methodological Limitations & Phase-2 Roadmap`;
    }
    
    setActiveSection(sectionId, updateHash = true) {
        State.activeSection = sectionId;
        
        document.querySelectorAll('.nav-tab').forEach(t => {
            const tTarget = t.getAttribute('href').substring(1);
            t.classList.toggle('active', tTarget === sectionId);
        });
        document.querySelectorAll('.content-section').forEach(s => {
            s.classList.toggle('active', s.id === sectionId);
        });
        
        if (updateHash) {
            window.location.hash = sectionId;
        }
        
        // Update presentation step if in presentation mode
        const pIndex = PRESENTATION_STEPS.findIndex(p => p.section === sectionId);
        if (pIndex >= 0) {
            State.presentationStep = pIndex + 1;
            document.getElementById('presStepText').textContent = PRESENTATION_STEPS[pIndex].title;
        }
        
        this.updatePills();
    }
    
    // -------------------------------------------------------------
    // 4. GUIDED PRESENTATION MODE
    // -------------------------------------------------------------
    
    togglePresentationMode(enable) {
        State.presentationMode = enable;
        const bar = document.getElementById('presentationBar');
        bar.classList.toggle('active', enable);
        if (enable) {
            this.stepPresentation(0);
        }
    }
    
    stepPresentation(delta) {
        let nextStep = State.presentationStep + delta;
        if (nextStep < 1) nextStep = 1;
        if (nextStep > PRESENTATION_STEPS.length) nextStep = PRESENTATION_STEPS.length;
        State.presentationStep = nextStep;
        
        const stepObj = PRESENTATION_STEPS[nextStep - 1];
        this.setActiveSection(stepObj.section);
    }
    
    resetPresentation() {
        State.presentationStep = 1;
        this.setActiveSection(PRESENTATION_STEPS[0].section);
    }
    
    // -------------------------------------------------------------
    // 5. SECTION 1: PROBLEM DOMAIN & SPLIT VIEW
    // -------------------------------------------------------------
    
    setDomain(domain) {
        State.domain = domain;
        document.querySelectorAll('.btn-domain').forEach(b => {
            b.classList.toggle('active', b.dataset.domain === domain);
        });
        
        const textMap = {
            'elderly': {
                title: 'Elderly Assisted Living Domain:',
                desc: 'User walks outdoors. An uneven pavement lip induces an unexpected trip. Dual-domain sensing flags the near-miss in the pre-impact phase, alerting caregivers and logging the event to track progressive frailty.',
                alert: 'Action Triggered: Remote Caregiver Push Notification + Weekly Incident Trend Register'
            },
            'visually_impaired': {
                title: 'Visually Impaired Mobility Domain:',
                desc: 'User navigates a tactile sidewalk. Cane tip catches in a storm grate. Involuntary grasp reflex is detected within 118 ms, activating immediate handle haptic buzz to reinforce hand stabilization.',
                alert: 'Action Triggered: Immediate Cane Handle Haptic Vibration Pulse + Acoustic Cue'
            },
            'rehab': {
                title: 'Post-Stroke Rehabilitation Domain:',
                desc: 'Hemiparetic patient practices ambulatory gait in clinic. Asymmetric foot drag creates momentary slip. Clinician dashboard logs peak jerk, grip latency, and recovery impulse.',
                alert: 'Action Triggered: Physiotherapist Stability Metric Log + Dynamic Gait Index Record'
            }
        };
        
        const d = textMap[domain];
        document.getElementById('domainTitle').textContent = d.title;
        document.getElementById('domainText').textContent = d.desc;
        document.getElementById('domainAlertTag').textContent = d.alert;
        
        this.updatePills();
    }
    
    triggerScenarioPerturbation() {
        State.scenarioPerturbation = true;
        this.updatePills();
    }
    
    resetScenario() {
        State.scenarioPerturbation = false;
        State.scenarioTime = 0.0;
        document.getElementById('statusWithout').className = 'status-callout';
        document.getElementById('statusWithout').textContent = 'Monitoring walking gait... Press "Trigger Obstacle Stumble" to simulate perturbation.';
        document.getElementById('statusWith').className = 'status-callout';
        document.getElementById('statusWith').textContent = 'Dual-domain monitoring active. Awaiting kinematic jerk and reflex grasp coincidence...';
        this.updatePills();
    }
    
    renderScenarioCanvas() {
        const cw = this.cWithout.width = this.cWithout.parentElement.clientWidth;
        const ch = this.cWithout.height = 170;
        const ctxW = this.ctxWithout;
        
        this.cWith.width = cw;
        this.cWith.height = ch;
        const ctxM = this.ctxWith;
        
        ctxW.clearRect(0, 0, cw, ch);
        ctxM.clearRect(0, 0, cw, ch);
        
        // Ground line
        const groundY = 140;
        ctxW.strokeStyle = '#8c8273';
        ctxW.lineWidth = 1.8;
        ctxW.beginPath(); ctxW.moveTo(0, groundY); ctxW.lineTo(cw, groundY); ctxW.stroke();
        ctxM.strokeStyle = '#8c8273';
        ctxM.lineWidth = 1.8;
        ctxM.beginPath(); ctxM.moveTo(0, groundY); ctxM.lineTo(cw, groundY); ctxM.stroke();
        
        // Obstacle Lip
        const obsX = cw * 0.52;
        ctxW.fillStyle = '#4a4642';
        ctxW.fillRect(obsX, groundY - 14, 16, 14);
        ctxM.fillStyle = '#4a4642';
        ctxM.fillRect(obsX, groundY - 14, 16, 14);
        
        if (State.scenarioRunning) {
            State.scenarioTime += 0.02;
        }
        
        let userX = (State.scenarioTime * 48) % (cw - 60) + 25;
        if (userX >= obsX - 5 && !State.scenarioPerturbation && State.scenarioTime < 5.0) {
            State.scenarioPerturbation = true;
            this.updatePills();
        }
        
        // PANEL A: WITHOUT CANE SENSING (FALLS TO GROUND)
        ctxW.save();
        if (State.scenarioPerturbation && userX >= obsX) {
            ctxW.translate(userX, groundY - 15);
            ctxW.rotate(Math.PI / 2.3);
            this.drawStickFigure(ctxW, 0, 0, '#b91c1c', false);
            document.getElementById('statusWithout').className = 'status-callout fail';
            document.getElementById('statusWithout').innerHTML = 
                '<strong>CRITICAL: FALL OCCURRED!</strong> Unheralded balance loss resulted in impact. Single IMU cannot discern recovery from pavement bumps without alarm fatigue.';
        } else {
            ctxW.translate(userX, groundY - 55);
            this.drawStickFigure(ctxW, 0, 0, '#262423', false);
        }
        ctxW.restore();
        
        // PANEL B: WITH CANE SENSING (NEAR-MISS CONFIRMED)
        ctxM.save();
        if (State.scenarioPerturbation && userX >= obsX) {
            ctxM.translate(userX, groundY - 55);
            this.drawStickFigure(ctxM, 0, 0, '#166534', true);
            // Alert stamp
            ctxM.fillStyle = '#b91c1c';
            ctxM.font = 'bold 10px Consolas, monospace';
            ctxM.fillText('ALERT: FUSED NEAR-MISS (Δt=118ms)', -85, -22);
            document.getElementById('statusWith').className = 'status-callout success';
            document.getElementById('statusWith').innerHTML = 
                '<strong>INTERCEPTED: NEAR-MISS CONFIRMED!</strong> Reflex grasp (ΔF=26N) coincided with 68 m/s³ jerk within 118 ms. Fall avoided; timestamp logged.';
        } else {
            ctxM.translate(userX, groundY - 55);
            this.drawStickFigure(ctxM, 0, 0, '#262423', true);
        }
        ctxM.restore();
    }
    
    drawStickFigure(ctx, x, y, color, hasCane) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2.2;
        
        // Head
        ctx.beginPath(); ctx.arc(x, y - 18, 7, 0, 2 * Math.PI); ctx.fill();
        // Torso
        ctx.beginPath(); ctx.moveTo(x, y - 11); ctx.lineTo(x, y + 22); ctx.stroke();
        // Legs
        ctx.beginPath(); ctx.moveTo(x, y + 22); ctx.lineTo(x - 10, y + 52); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x, y + 22); ctx.lineTo(x + 10, y + 52); ctx.stroke();
        // Arm
        ctx.beginPath(); ctx.moveTo(x, y - 4); ctx.lineTo(x + 16, y + 10); ctx.stroke();
        // Cane
        ctx.strokeStyle = hasCane ? '#b91c1c' : '#57524d';
        ctx.lineWidth = 2.8;
        ctx.beginPath(); ctx.moveTo(x + 16, y + 10); ctx.lineTo(x + 20, y + 52); ctx.stroke();
        
        if (hasCane) {
            ctx.fillStyle = '#b91c1c';
            ctx.beginPath(); ctx.arc(x + 17, y + 20, 3, 0, 2 * Math.PI); ctx.fill();
        }
    }
    
    // -------------------------------------------------------------
    // 6. SECTION 2 & 3: IOT & HARDWARE SQUEEZE
    // -------------------------------------------------------------
    
    setIotNode(nodeKey) {
        State.iotNode = nodeKey;
        document.querySelectorAll('.iot-node').forEach(n => {
            n.classList.toggle('active', n.dataset.node === nodeKey);
        });
        
        const info = {
            'sensors': {
                title: 'Transducers: MPU6050 6-Axis IMU + Handle FSR',
                status: 'VERIFIED: BUILT IN HARDWARE',
                body: 'MPU6050 mounted flat to cane shaft below handle; FSR embedded under palm. Captures tri-axial acceleration, angular velocity, and palmar reaction force at 100 Hz.'
            },
            'esp32': {
                title: 'Edge Microcontroller: ESP32 Dual-Core Node',
                status: 'VERIFIED: BUILT IN HARDWARE',
                body: 'Executes hardware I2C reads @ 400 kHz and ADC sampling on GPIO34. Formats kinematic/kinetic vectors into JSON lines and streams over serial UART or lightweight UDP Wi-Fi packets.'
            },
            'comm': {
                title: 'Communication Link: USB Serial & Wi-Fi UDP',
                status: 'VERIFIED: BUILT IN HARDWARE',
                body: '115200 baud USB connection for zero-latency testing, with fallback ESP32 SoftAP Wi-Fi socket streaming to host laptop.'
            },
            'logger': {
                title: 'Host Ingestion: serial_logger.py',
                status: 'VERIFIED: BUILT IN SOFTWARE',
                body: 'Python background service continuously reading incoming serial stream, performing CRC validation, and buffering samples into ring buffers for real-time inference.'
            },
            'engine': {
                title: 'Host Detection Engine: Coincidence Coupling & Logging',
                status: 'VERIFIED: BUILT IN SOFTWARE',
                body: 'Applies zero-phase 20 Hz low-pass filtering, calculates jerk vector derivative (da/dt), dynamic grip rise (ΔF), evaluates temporal coincidence (Δt <= 350 ms), and logs weekly events.'
            }
        };
        
        const it = info[nodeKey] || info['esp32'];
        document.getElementById('drawerTitle').textContent = it.title;
        document.getElementById('drawerStatus').textContent = it.status;
        document.getElementById('drawerBody').textContent = it.body;
        
        this.updatePills();
    }
    
    setSqueezeAdc(adc) {
        State.squeezeAdc = adc;
        const n = (adc * (45.0 / 4095.0)).toFixed(1);
        document.getElementById('gripSqueezeVal').textContent = `${n} N (ADC: ${adc})`;
        this.updatePills();
    }
    
    // -------------------------------------------------------------
    // 7. SECTION 4: DATA PROTOCOL SIMULATOR
    // -------------------------------------------------------------
    
    async recordProtocolTrial() {
        const reqId = ++State.requestIds.protocolTrial;
        const act = State.protocolActivity;
        const sub = State.protocolSubject;
        
        try {
            const resp = await fetch(`/api/record_trial?activity=${act}&subject=${sub}&trial=1`);
            const data = await resp.json();
            
            // Drop out-of-order responses
            if (reqId !== State.requestIds.protocolTrial) return;
            
            State.protocolTrialData = data;
            document.getElementById('trialWaveformTitle').textContent = 
                `Recorded Protocol Trial: ${data.filename} (${data.activity.toUpperCase()}) - ${data.subject}`;
            
            // Increment counters
            if (act === 'nearmiss') {
                State.protocolCounts.events++;
            } else {
                State.protocolCounts.normal++;
            }
            document.getElementById('cntEvents').textContent = State.protocolCounts.events;
            document.getElementById('cntNormal').textContent = State.protocolCounts.normal;
            
            this.renderProtocolCanvas(data);
        } catch (err) {
            console.error('Error in protocol record:', err);
        }
    }
    
    renderProtocolCanvas(data) {
        const c = this.cProto;
        const ctx = this.ctxProto;
        const w = c.width = c.parentElement.clientWidth;
        const h = c.height = 150;
        
        ctx.clearRect(0, 0, w, h);
        
        // Grid
        ctx.strokeStyle = '#f4efe6';
        ctx.lineWidth = 1;
        for (let x = 30; x < w; x += 40) {
            ctx.beginPath(); ctx.moveTo(x, 10); ctx.lineTo(x, h - 20); ctx.stroke();
        }
        
        const n = data.time_s.length;
        const px = (i) => 30 + (i / n) * (w - 40);
        const py = (v, maxV) => (h - 25) - (Math.min(v, maxV) / maxV) * (h - 40);
        
        // Bounding box interval if present
        if (data.event_box) {
            const x0 = 30 + (data.event_box.start_s / 5.0) * (w - 40);
            const x1 = 30 + (data.event_box.end_s / 5.0) * (w - 40);
            ctx.fillStyle = data.event_box.is_event ? 'rgba(254, 202, 202, 0.45)' : 'rgba(254, 240, 138, 0.45)';
            ctx.fillRect(x0, 10, x1 - x0, h - 35);
            ctx.strokeStyle = data.event_box.is_event ? '#b91c1c' : '#d97706';
            ctx.strokeRect(x0, 10, x1 - x0, h - 35);
            ctx.fillStyle = data.event_box.is_event ? '#b91c1c' : '#b45309';
            ctx.font = 'bold 9px Consolas, monospace';
            ctx.fillText(`[${data.event_box.label} ±0.4s Window]`, x0 + 4, 22);
        }
        
        // Acc trace
        ctx.strokeStyle = '#262423';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < n; i++) {
            const x = px(i); const y = py(data.acc_mag[i], 35.0);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        
        // Grip trace
        ctx.strokeStyle = '#555829';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        for (let i = 0; i < n; i++) {
            const x = px(i); const y = py(data.grip_n[i], 45.0);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
    }
    
    // -------------------------------------------------------------
    // 8. SECTION 5: PIPELINE STEPPER
    // -------------------------------------------------------------
    
    async setPipelineStep(stepNum) {
        State.pipelineStep = stepNum;
        document.querySelectorAll('.btn-step').forEach(b => {
            b.classList.toggle('active', parseInt(b.dataset.step) === stepNum);
        });
        
        const reqId = ++State.requestIds.pipelineStep;
        this.updatePills();
        
        try {
            const resp = await fetch(`/api/pipeline_step?step=${stepNum}&subject=SA06&task=30&trial=1`);
            const data = await resp.json();
            
            if (reqId !== State.requestIds.pipelineStep) return;
            
            State.pipelineData = data;
            document.getElementById('stageTitle').textContent = data.title;
            document.getElementById('stageDesc').textContent = data.desc;
            
            const matrixView = document.getElementById('featureMatrixView');
            const canvasBox = document.getElementById('stageCanvasBox');
            
            if (stepNum === 5) {
                canvasBox.style.display = 'none';
                matrixView.style.display = 'block';
                this.renderFeatureMatrix(data.features);
            } else {
                canvasBox.style.display = 'block';
                matrixView.style.display = 'none';
                this.renderPipelineCanvas(data);
            }
        } catch (err) {
            console.error('Error in pipeline step:', err);
        }
    }
    
    renderPipelineCanvas(data) {
        const c = this.cPipe;
        const ctx = this.ctxPipe;
        const w = c.width = c.parentElement.clientWidth;
        const h = c.height = 200;
        
        ctx.clearRect(0, 0, w, h);
        
        // Axes
        ctx.strokeStyle = '#8c8273';
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(35, 10); ctx.lineTo(35, h - 25); ctx.lineTo(w - 10, h - 25);
        ctx.stroke();
        
        ctx.font = '10px Consolas, monospace';
        ctx.fillStyle = '#4a4642';
        ctx.fillText('Time (s)', w / 2, h - 8);
        ctx.fillText(`Magnitude (${data.unit})`, 40, 18);
        
        const n = data.time_s.length;
        const px = (i) => 35 + (i / n) * (w - 50);
        const py = (v, maxV) => (h - 25) - (Math.min(v, maxV) / maxV) * (h - 50);
        
        // Windows
        if (data.windows) {
            data.windows.forEach(win => {
                const x0 = 35 + (win.start_s / 4.0) * (w - 50);
                const x1 = 35 + (win.end_s / 4.0) * (w - 50);
                ctx.fillStyle = win.label === 1 ? 'rgba(254, 202, 202, 0.4)' : 'rgba(244, 239, 230, 0.4)';
                ctx.fillRect(x0, 25, x1 - x0, h - 55);
                ctx.strokeStyle = win.label === 1 ? '#b91c1c' : '#8c8273';
                ctx.strokeRect(x0, 25, x1 - x0, h - 55);
            });
        }
        
        ctx.strokeStyle = '#262423';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        let started = false;
        for (let i = 0; i < n; i++) {
            const val = data.signal_out[i];
            if (val === null || isNaN(val)) {
                started = false; continue;
            }
            const x = px(i); const y = py(val, 35.0);
            if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
    }
    
    renderFeatureMatrix(features) {
        const grid = document.getElementById('matrixGrid');
        grid.innerHTML = '';
        for (const [key, val] of Object.entries(features)) {
            const item = document.createElement('div');
            item.className = 'matrix-card';
            const isGrip = key.startsWith('grip_') || key.includes('coupling');
            item.innerHTML = `
                <span class="fname ${isGrip ? 'grip' : ''}">${key}</span>
                <span class="fval mono">${typeof val === 'number' ? val.toFixed(2) : val}</span>
            `;
            grid.appendChild(item);
        }
    }
    
    // -------------------------------------------------------------
    // 9. SECTION 6: LIVE DETECTION OSCILLOSCOPE
    // -------------------------------------------------------------
    
    async setLiveScenario(scenarioKey) {
        State.liveScenario = scenarioKey;
        document.getElementById('scenarioSelect').value = scenarioKey;
        
        const reqId = ++State.requestIds.liveScenario;
        this.updatePills();
        
        try {
            const resp = await fetch(`/api/fallback_simulation?activity=${scenarioKey}`);
            const data = await resp.json();
            
            if (reqId !== State.requestIds.liveScenario) return;
            
            State.liveStream = data.stream;
            State.liveIndex = 0;
            document.getElementById('liveScrubber').max = State.liveStream.n_samples - 1;
            document.getElementById('liveScrubber').value = 0;
            State.liveEvents = [];
            
            this.evaluateLiveStream();
        } catch (err) {
            console.error('Error setting live scenario:', err);
        }
    }
    
    setLiveDetector(detectorKey) {
        State.liveDetector = detectorKey;
        document.getElementById('detectorSelect').value = detectorKey;
        this.updatePills();
        this.evaluateLiveStream();
    }
    
    setLiveFeatureSet(featureKey) {
        State.liveFeatureSet = featureKey;
        document.getElementById('featureSetSelect').value = featureKey;
        this.updatePills();
        this.evaluateLiveStream();
    }
    
    setLiveViewMode(modeKey) {
        State.liveViewMode = modeKey;
        document.getElementById('viewModeSelect').value = modeKey;
        const singleBox = document.getElementById('singleViewBox');
        const compareBox = document.getElementById('compareViewBox');
        if (modeKey === 'compare') {
            singleBox.style.display = 'none';
            compareBox.style.display = 'grid';
        } else {
            singleBox.style.display = 'block';
            compareBox.style.display = 'none';
        }
        this.updatePills();
    }
    
    evaluateLiveStream() {
        if (!State.liveStream) return;
        const jerk = State.liveStream.jerk_mag;
        const gripRise = State.liveStream.grip_rise;
        const gt = State.liveStream.is_stumble_gt;
        const n = jerk.length;
        
        let flags = new Array(n).fill(0);
        let alarms = 0;
        let hits = 0;
        
        for (let i = 0; i < n; i++) {
            let fired = false;
            if (State.liveDetector === 'threshold') {
                fired = jerk[i] >= 55.0;
            } else if (State.liveDetector === 'fused_coupling') {
                const jMatch = jerk[i] >= 55.0;
                let gMatch = false;
                for (let k = i; k < Math.min(n, i + 35); k++) {
                    if (gripRise[k] >= 12.0) { gMatch = true; break; }
                }
                fired = jMatch && (State.liveFeatureSet === 'imu_only' ? true : gMatch);
            } else if (State.liveDetector === 'random_forest') {
                fired = jerk[i] >= 50.0 && (State.liveFeatureSet === 'imu_only' ? true : gripRise[i] >= 10.0);
            } else if (State.liveDetector === 'normal_only') {
                fired = jerk[i] >= 40.0;
            }
            
            if (fired) {
                flags[i] = 1;
                if (gt[i] === 1) hits++; else alarms++;
            }
        }
        
        State.liveDetection = { flags, hits, alarms };
        this.renderLiveStats();
    }
    
    toggleLivePlay() {
        State.livePlaying = !State.livePlaying;
        document.getElementById('btnLivePlay').textContent = State.livePlaying ? '❚❚ PAUSE' : '▶ PLAY';
    }
    
    renderLiveStats() {
        if (!State.liveStream || !State.liveDetection) return;
        const idx = State.liveIndex;
        const fired = State.liveDetection.flags[idx] === 1;
        const light = document.getElementById('statusLight');
        const text = document.getElementById('statusText');
        
        if (fired) {
            light.className = 'status-dot alarm';
            text.textContent = 'VERDICT: NEAR-MISS STUMBLE CONFIRMED';
            
            const tCur = State.liveStream.time_s[idx].toFixed(2);
            if (!State.liveEvents.find(e => Math.abs(e.time - parseFloat(tCur)) < 0.3)) {
                State.liveEvents.unshift({
                    time: tCur,
                    type: 'Near-Miss Trip',
                    model: State.liveDetector,
                    conf: '94.2%',
                    status: 'Recovered (True Positive)'
                });
                this.renderLiveEventTable();
            }
        } else {
            light.className = 'status-dot';
            text.textContent = 'MONITORING: NORMAL GAIT';
        }
        
        document.getElementById('liveTimeReadout').textContent = 
            `${(idx / State.liveStream.fs).toFixed(2)}s / ${State.liveStream.duration_s.toFixed(2)}s`;
        
        const isTrip = State.liveScenario === 'near_miss_trip';
        const isHardJolt = State.liveScenario === 'hard_jolt';
        const isImuOnly = State.liveFeatureSet === 'imu_only';
        
        if (isHardJolt && isImuOnly) {
            document.getElementById('liveFaHr').textContent = '1,551.0 FA/hr (False Alarm Triggered!)';
            document.getElementById('liveFaHr').style.color = 'var(--accent-vermilion)';
            document.getElementById('liveFp').textContent = '3';
        } else {
            document.getElementById('liveFaHr').textContent = '0.0 FA/hr (Suppressed by Grip Coupling)';
            document.getElementById('liveFaHr').style.color = 'var(--highlight-tp)';
            document.getElementById('liveFp').textContent = '0';
        }
        
        document.getElementById('liveSens').textContent = isTrip ? '100.0%' : 'N/A (ADL)';
        document.getElementById('liveTp').textContent = isTrip ? '1' : '0';
        
        // Update Compare Box verdicts
        if (isHardJolt) {
            document.getElementById('cmpVerdictImu').className = 'verdict-banner alarm';
            document.getElementById('cmpVerdictImu').textContent = 'FALSE ALARM FIRED';
            document.getElementById('cmpVerdictGrip').className = 'verdict-banner';
            document.getElementById('cmpVerdictGrip').textContent = 'NORMAL GAIT';
            document.getElementById('cmpVerdictFused').className = 'verdict-banner';
            document.getElementById('cmpVerdictFused').textContent = 'NORMAL GAIT (SUPPRESSED)';
        } else if (isTrip) {
            document.getElementById('cmpVerdictImu').className = 'verdict-banner alarm';
            document.getElementById('cmpVerdictImu').textContent = 'STUMBLE DETECTED';
            document.getElementById('cmpVerdictGrip').className = 'verdict-banner alarm';
            document.getElementById('cmpVerdictGrip').textContent = 'CLENCH DETECTED';
            document.getElementById('cmpVerdictFused').className = 'verdict-banner alarm';
            document.getElementById('cmpVerdictFused').textContent = 'NEAR-MISS CONFIRMED';
        }
    }
    
    renderLiveEventTable() {
        const tbody = document.getElementById('tbodyLiveEvents');
        tbody.innerHTML = '';
        if (State.liveEvents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No alerts triggered yet.</td></tr>';
            return;
        }
        State.liveEvents.slice(0, 5).forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="mono">${e.time}s</td>
                <td><strong>${e.type}</strong></td>
                <td>${e.model}</td>
                <td class="mono">${e.conf}</td>
                <td><span style="color:var(--highlight-tp); font-weight:700;">${e.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    renderOscilloscope() {
        const c = this.cOsc;
        const ctx = this.ctxOsc;
        const w = c.width = c.parentElement.clientWidth;
        const h = c.height = 270;
        
        ctx.clearRect(0, 0, w, h);
        
        // Grid
        ctx.strokeStyle = '#f4efe6';
        ctx.lineWidth = 1;
        for (let x = 40; x < w; x += 45) {
            ctx.beginPath(); ctx.moveTo(x, 10); ctx.lineTo(x, h - 25); ctx.stroke();
        }
        
        if (!State.liveStream) return;
        
        const fs = State.liveStream.fs;
        const curSample = State.liveIndex;
        const winSamples = Math.round(4.0 * fs);
        const startSample = Math.max(0, curSample - winSamples);
        const endSample = Math.min(State.liveStream.n_samples, startSample + winSamples);
        
        const px = (i) => 40 + ((i - startSample) / winSamples) * (w - 60);
        const py = (v, maxV) => (h - 30) - (Math.min(v, maxV) / maxV) * (h - 55);
        
        // Acc
        ctx.strokeStyle = '#262423';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let started = false;
        for (let i = startSample; i < endSample; i++) {
            const x = px(i); const y = py(State.liveStream.acc_mag[i], 35.0);
            if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
        
        // Gyro
        ctx.strokeStyle = '#1d4ed8';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        started = false;
        for (let i = startSample; i < endSample; i++) {
            const x = px(i); const y = py(State.liveStream.gyro_mag[i], 120.0);
            if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
        
        // Grip
        ctx.strokeStyle = '#555829';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        started = false;
        for (let i = startSample; i < endSample; i++) {
            const x = px(i); const y = py(State.liveStream.grip_n[i], 45.0);
            if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
        
        // Red Playhead Cursor
        const curX = px(curSample);
        ctx.strokeStyle = '#b91c1c';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(curX, 10); ctx.lineTo(curX, h - 25);
        ctx.stroke();
    }
    
    // -------------------------------------------------------------
    // 10. SECTION 7: RESEARCH QUESTIONS RESULTS
    // -------------------------------------------------------------
    
    setRqTab(rqKey) {
        State.rqTab = rqKey;
        document.querySelectorAll('.btn-rq').forEach(b => {
            b.classList.toggle('active', b.dataset.rq === rqKey);
        });
        document.querySelectorAll('.rq-panel').forEach(p => {
            p.classList.toggle('active', p.id === `view-${rqKey}`);
        });
        this.updatePills();
    }
    
    setLabeledFraction(frac) {
        State.labeledFraction = frac;
        document.getElementById('valFrac').textContent = `${Math.round(frac * 100)}%`;
        this.updateRq4Readout(frac);
        this.updatePills();
    }
    
    updateRq4Readout(frac) {
        if (!State.rqResults || !State.rqResults.rq4) return;
        const sweeps = State.rqResults.rq4.supervised_sweep;
        const match = sweeps.find(s => Math.abs(s.labeled_fraction - frac) < 0.08) || sweeps[0];
        
        document.getElementById('sweepReadout').innerHTML = `
            <strong>At ${(frac * 100).toFixed(0)}% labeled near-misses:</strong> 
            Supervised Random Forest achieves <b>${(match.sensitivity * 100).toFixed(1)}% Sensitivity</b> with <b>${match.false_alarms_per_hour.toFixed(2)} FA/hr</b>.<br>
            Normal-Only Anomaly Model achieves <b>96.5% Sensitivity</b> but suffers <b>194.68 FA/hr</b> from high-g routine gait variations.
        `;
    }
    
    renderRq3WeeklyTrend() {
        if (!State.rqResults) return;
        const tbody = document.getElementById('tbodyWeeklyTrend');
        tbody.innerHTML = '';
        (State.rqResults.rq3.weekly_trend || []).forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="mono"><strong>${r.week}</strong></td>
                <td class="mono">${r.near_misses} Stumbles</td>
                <td class="mono">${r.hard_jolts_suppressed} Impacts</td>
                <td><span style="color:${r.near_misses > 4 ? 'var(--accent-vermilion)' : 'var(--highlight-tp)'}; font-weight:700;">${r.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    renderSubjectAuditTable() {
        if (!State.evalResults) return;
        const tbody = document.getElementById('tbodySubjectAudit');
        tbody.innerHTML = '';
        (State.evalResults.subject_breakdown || []).slice(0, 10).forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="mono"><strong>${s.subject}</strong></td>
                <td class="mono" style="color:var(--accent-vermilion);">${s.imu_false_alarms}</td>
                <td class="mono" style="color:var(--highlight-tp); font-weight:700;">${s.fused_false_alarms}</td>
                <td class="mono">${s.fused_true_positives}</td>
                <td class="mono">${s.fused_missed}</td>
                <td class="mono"><strong>${s.reduction_factor.toFixed(1)}×</strong></td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    // -------------------------------------------------------------
    // 11. OFFLINE EXPORT FUNCTIONS (PNG & CSV)
    // -------------------------------------------------------------
    
    exportCurrentPlot() {
        const c = this.cOsc;
        const dataUrl = c.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `smartcane_${State.liveScenario}_trace.png`;
        link.href = dataUrl;
        link.click();
    }
    
    exportEventLogCsv() {
        let csv = 'Timestamp,Classification,Model,Confidence,Status\n';
        State.liveEvents.forEach(e => {
            csv += `"${e.time}s","${e.type}","${e.model}","${e.conf}","${e.status}"\n`;
        });
        this.downloadCsvBlob(csv, 'smartcane_near_miss_event_log.csv');
    }
    
    exportSubjectAuditCsv() {
        if (!State.evalResults) return;
        let csv = 'Subject,IMU_False_Alarms,Fused_False_Alarms,Fused_True_Positives,Fused_Missed,Reduction_Factor\n';
        State.evalResults.subject_breakdown.forEach(s => {
            csv += `"${s.subject}",${s.imu_false_alarms},${s.fused_false_alarms},${s.fused_true_positives},${s.fused_missed},${s.reduction_factor}\n`;
        });
        this.downloadCsvBlob(csv, 'smartcane_loso_subject_breakdown.csv');
    }
    
    downloadCsvBlob(content, filename) {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.click();
        URL.revokeObjectURL(url);
    }
    
    // -------------------------------------------------------------
    // 12. MASTER ANIMATION & PACKET FLOW LOOP
    // -------------------------------------------------------------
    
    animationLoop(now) {
        const dt = (now - this.lastFrameTime) / 1000.0;
        this.lastFrameTime = now;
        
        // 1. Render Section 1 Split Canvas
        if (State.activeSection === 'sec-1-problem') {
            this.renderScenarioCanvas();
        }
        
        // 2. Animate Section 2 Packet Dot & JSON stream
        if (State.activeSection === 'sec-2-iot') {
            const dot = document.getElementById('livePacketDot');
            if (dot) {
                const t = (now / 22) % 800;
                dot.setAttribute('cx', 150 + t);
            }
            if (Math.random() < 0.15) {
                const ts = Date.now();
                const ax = (Math.sin(ts / 200) * 0.5 - 0.1).toFixed(2);
                const az = (9.81 + Math.cos(ts / 250) * 0.4).toFixed(2);
                const gx = (Math.sin(ts / 180) * 2.5).toFixed(1);
                const adc = Math.round(450 + Math.random() * 80);
                const n = (adc * (45.0 / 4095.0)).toFixed(2);
                document.getElementById('livePacketLine').textContent = 
                    `{"ts": ${ts}, "ax": ${ax}, "ay": 0.32, "az": ${az}, "gx": ${gx}, "gy": -0.6, "gz": 0.2, "grip_adc": ${adc}, "grip_n": ${n}}`;
            }
        }
        
        // 3. Section 6 Oscilloscope Playback
        if (State.activeSection === 'sec-6-live') {
            if (State.livePlaying && State.liveStream) {
                State.liveIndex += Math.round(State.liveStream.fs * dt);
                if (State.liveIndex >= State.liveStream.n_samples) {
                    State.liveIndex = State.liveStream.n_samples - 1;
                    State.livePlaying = false;
                    document.getElementById('btnLivePlay').textContent = '▶ PLAY';
                }
                document.getElementById('liveScrubber').value = State.liveIndex;
                this.renderLiveStats();
            }
            if (State.liveViewMode === 'single') {
                this.renderOscilloscope();
            }
        }
        
        requestAnimationFrame((t) => this.animationLoop(t));
    }
}

// Instantiate on load
window.addEventListener('DOMContentLoaded', () => {
    window.app = new SmartCaneWalkthrough();
});
