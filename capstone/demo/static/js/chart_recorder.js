/**
 * Smart Cane Capstone Demonstration Engine (PW_27_MHR_01)
 * Multi-Modal Sensor Trace Plotter, Dataset Coverage, LOSO Benchmark & Replay
 */

class SmartCaneDemoApp {
    constructor() {
        this.canvas = document.getElementById('chartRecorder');
        this.ctx = this.canvas.getContext('2d');
        
        // Data buffers
        this.stream = null;
        this.detection = null;
        this.availableCases = [];
        this.currentCaseIndex = 0;
        
        // Playlist state for 'Play All Cases'
        this.playlist = [];
        this.playlistIndex = 0;
        this.isPlayingPlaylist = false;
        
        // Playback state
        this.isPlaying = false;
        this.currentIndex = 0;
        this.playbackSpeed = 1.0;
        this.lastFrameTime = performance.now();
        this.windowSeconds = 4.0;
        
        // Detection Thresholds
        this.jerkThresh = 55.0;
        this.gripThresh = 12.0;
        this.windowSec = 0.35;
        
        // Running Tallies
        this.tallies = {
            imu_fa: 0, imu_tp: 0,
            grip_fa: 0, grip_tp: 0,
            fused_fa: 0, fused_tp: 0
        };
        
        this.initDOM();
        this.initTabs();
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        this.loadDatasetCoverage();
        this.loadEvaluationData();
        this.loadEventLog();
        this.loadPlaylist();
        this.loadInitialSubjects();
        
        requestAnimationFrame((t) => this.animationLoop(t));
    }
    
    initDOM() {
        // Controls
        this.btnPlay = document.getElementById('btnPlay');
        this.scrubber = document.getElementById('scrubber');
        this.timeReadout = document.getElementById('timeReadout');
        this.subjectSelect = document.getElementById('subjectSelect');
        this.categoryFilter = document.getElementById('categoryFilter');
        this.caseSelect = document.getElementById('caseSelect');
        this.provenanceBadge = document.getElementById('provenanceBadge');
        
        this.btnPrevCase = document.getElementById('btnPrevCase');
        this.btnNextCase = document.getElementById('btnNextCase');
        this.btnPlayAll = document.getElementById('btnPlayAll');
        this.btnStopPlaylist = document.getElementById('btnStopPlaylist');
        this.playlistStatus = document.getElementById('playlistStatus');
        this.playlistBannerText = document.getElementById('playlistBannerText');
        
        // Sliders & Calibration
        this.sliderJerk = document.getElementById('sliderJerk');
        this.valJerk = document.getElementById('valJerk');
        this.sliderGrip = document.getElementById('sliderGrip');
        this.valGrip = document.getElementById('valGrip');
        this.sliderWindow = document.getElementById('sliderWindow');
        this.valWindow = document.getElementById('valWindow');
        this.btnCalibrate = document.getElementById('btnCalibrate');
        this.calibFeedback = document.getElementById('calibFeedback');
        
        // Cards & Tallies
        this.verdictIMU = document.getElementById('verdictIMU');
        this.verdictGrip = document.getElementById('verdictGrip');
        this.verdictFused = document.getElementById('verdictFused');
        this.tallyImuFa = document.getElementById('tallyImuFa');
        this.tallyImuTp = document.getElementById('tallyImuTp');
        this.tallyGripFa = document.getElementById('tallyGripFa');
        this.tallyGripTp = document.getElementById('tallyGripTp');
        this.tallyFusedFa = document.getElementById('tallyFusedFa');
        this.tallyFusedTp = document.getElementById('tallyFusedTp');
        
        // Event Listeners
        this.btnPlay.addEventListener('click', () => this.togglePlay());
        this.scrubber.addEventListener('input', (e) => this.onScrub(e.target.value));
        
        // Speed Buttons
        document.querySelectorAll('.btn-speed').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.playbackSpeed = parseFloat(e.target.dataset.speed);
            });
        });
        
        // Threshold Sliders
        this.sliderJerk.addEventListener('input', (e) => {
            this.jerkThresh = parseFloat(e.target.value);
            this.valJerk.textContent = this.jerkThresh.toFixed(1);
            this.recomputeDetections();
        });
        this.sliderGrip.addEventListener('input', (e) => {
            this.gripThresh = parseFloat(e.target.value);
            this.valGrip.textContent = this.gripThresh.toFixed(1);
            this.recomputeDetections();
        });
        this.sliderWindow.addEventListener('input', (e) => {
            this.windowSec = parseFloat(e.target.value);
            this.valWindow.textContent = this.windowSec.toFixed(2);
            this.recomputeDetections();
        });
        
        this.btnCalibrate.addEventListener('click', () => this.runPersonalCalibration());
        
        // Case Navigation
        this.subjectSelect.addEventListener('change', () => this.onSubjectChange());
        this.categoryFilter.addEventListener('change', () => this.onCategoryChange());
        this.caseSelect.addEventListener('change', () => this.onCaseSelect());
        
        this.btnPrevCase.addEventListener('click', () => this.navigateCase(-1));
        this.btnNextCase.addEventListener('click', () => this.navigateCase(1));
        this.btnPlayAll.addEventListener('click', () => this.startPlayAllCases());
        this.btnStopPlaylist.addEventListener('click', () => this.stopPlayAllCases());
        
        document.getElementById('btnSimFallback').addEventListener('click', () => this.loadSimulatedFallback());
    }
    
    initTabs() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
                
                e.target.classList.add('active');
                const targetId = e.target.dataset.target;
                const targetSec = document.getElementById(targetId);
                if (targetSec) {
                    targetSec.classList.add('active');
                    if (targetId === 'sec-detection' || targetId === 'sec-replay') {
                        setTimeout(() => this.resizeCanvas(), 50);
                    }
                }
            });
        });
    }
    
    resizeCanvas() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        const displayWidth = rect.width - 28; // Account for padding
        const displayHeight = 340;
        
        this.canvas.width = displayWidth * window.devicePixelRatio;
        this.canvas.height = displayHeight * window.devicePixelRatio;
        this.canvas.style.width = displayWidth + 'px';
        this.canvas.style.height = displayHeight + 'px';
        
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.width = displayWidth;
        this.height = displayHeight;
    }
    
    // ------------------------------------------------------------------------
    // DATA LOADING: COVERAGE, BENCHMARK, CASES
    // ------------------------------------------------------------------------
    
    async loadDatasetCoverage() {
        try {
            const resp = await fetch('/api/dataset_coverage');
            const data = await resp.json();
            
            document.getElementById('covSubjects').textContent = data.total_subjects;
            document.getElementById('covFiles').textContent = data.total_files.toLocaleString();
            document.getElementById('covDuration').textContent = `${data.total_duration_hours} hrs`;
            document.getElementById('covSkipped').textContent = data.skipped_count;
            
            // Populate Table 1: Activity Classification Breakdown
            const tbody = document.getElementById('tbodyActivities');
            tbody.innerHTML = '';
            
            const metaMap = {
                'Walking & Stepping': { tasks: 'Tasks 04–07, 10–13', char: 'Rhythmic swing-stance gait kinematics' },
                'Stairs': { tasks: 'Tasks 14, 15', char: 'Vertical deceleration footfall impacts' },
                'Sitting & Getting Up': { tasks: 'Tasks 02, 03', char: 'Cane unloading / posture transitions' },
                'Turning': { tasks: 'Tasks 08, 09', char: 'Centripetal gyro rotation without shock' },
                'High Impact / Jumping': { tasks: 'Tasks 17, 19', char: 'Hard pavement strike (IMU false-alarm stress test)' },
                'Cane Drag & Tapping': { tasks: 'Task 18', char: 'High-frequency surface chatter' },
                'Near-Miss: Trip': { tasks: 'Tasks 30, 31, 35', char: 'Abrupt obstacle jerk + involuntary grasp reflex' },
                'Near-Miss: Slip': { tasks: 'Tasks 32–34, 36', char: 'Rapid loss of footing + somatic handle clench' },
                'Falls: Syncope / Transfer': { tasks: 'Tasks 20–29', char: 'Postural collapse / loss of consciousness' },
                'Standing': { tasks: 'Task 01', char: 'Static gravitational baseline' }
            };
            
            const totalFiles = data.total_files;
            for (const [catName, count] of Object.entries(data.activity_counts)) {
                const tr = document.createElement('tr');
                const pct = ((count / totalFiles) * 100).toFixed(1);
                const info = metaMap[catName] || { tasks: 'Various', char: 'Routine ambulatory activity' };
                
                tr.innerHTML = `
                    <td><strong>${catName}</strong></td>
                    <td class="mono">${count.toLocaleString()}</td>
                    <td class="mono">${pct}%</td>
                    <td><code>${info.tasks}</code></td>
                    <td>${info.char}</td>
                `;
                tbody.appendChild(tr);
            }
        } catch (err) {
            console.error('Error loading dataset coverage:', err);
        }
    }
    
    async loadEvaluationData() {
        try {
            const resp = await fetch('/api/evaluation');
            const data = await resp.json();
            
            // Populate Table 2: Benchmark Metrics
            const tbodyBench = document.getElementById('tbodyBenchmark');
            tbodyBench.innerHTML = '';
            
            const rowConfig = [
                { key: 'IMU_Only', name: '1. IMU-Only Baseline', note: 'Jerk > 55 m/s³' },
                { key: 'Grip_Only', name: '2. Grip-Only Baseline', note: 'Grip rise > 12 N' },
                { key: 'Fused_Coupling', name: '3. Fused Coupling (Proposed)', note: 'Jerk & Grip rise within 350 ms' }
            ];
            
            for (const item of rowConfig) {
                const m = data.metrics[item.key];
                if (!m) continue;
                const tr = document.createElement('tr');
                const isFused = item.key === 'Fused_Coupling';
                if (isFused) tr.style.backgroundColor = '#fef2f2';
                
                tr.innerHTML = `
                    <td><strong>${item.name}</strong><br><small style="color:var(--ink-muted);">${item.note}</small></td>
                    <td class="mono" style="font-weight:700;">${(m.sensitivity * 100).toFixed(1)}%</td>
                    <td class="mono" style="font-weight:700;">${(m.precision * 100).toFixed(1)}%</td>
                    <td class="mono" style="color:${isFused ? 'var(--highlight-tp)' : 'var(--accent-vermilion)'}; font-weight:700; font-size:14px;">
                        ${m.fa_per_hr.toFixed(1)} FA/hr
                    </td>
                    <td class="mono">${m.latency_ms} ms</td>
                    <td class="mono">${m.tp}</td>
                    <td class="mono">${m.fp}</td>
                    <td class="mono">${m.fn}</td>
                    <td class="mono">${data.total_duration_hours} hrs (${data.total_trials_evaluated} trials)</td>
                `;
                tbodyBench.appendChild(tr);
            }
            
            // Populate Table 3: Per-Subject Cross-Validation Breakdown
            const tbodySubs = document.getElementById('tbodySubjects');
            tbodySubs.innerHTML = '';
            (data.subject_breakdown || []).forEach(s => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="mono"><strong>${s.subject}</strong></td>
                    <td class="mono" style="color:var(--accent-vermilion);">${s.imu_false_alarms}</td>
                    <td class="mono" style="color:var(--highlight-tp); font-weight:700;">${s.fused_false_alarms}</td>
                    <td class="mono">${s.fused_true_positives}</td>
                    <td class="mono">${s.fused_missed}</td>
                    <td class="mono"><strong>${s.reduction_factor.toFixed(1)}×</strong></td>
                `;
                tbodySubs.appendChild(tr);
            });
            
            // Populate Table 4: Honest Failure Cases Audit
            const tbodyFail = document.getElementById('tbodyFailures');
            tbodyFail.innerHTML = '';
            (data.failure_cases || []).slice(0, 8).forEach(fc => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="mono"><strong>${fc.subject}</strong> (Task ${fc.task}, Trial ${fc.trial})</td>
                    <td><span style="color:var(--accent-vermilion); font-weight:700;">${fc.type}</span></td>
                    <td>${fc.description}</td>
                    <td>${fc.reason}</td>
                `;
                tbodyFail.appendChild(tr);
            });
        } catch (err) {
            console.error('Error loading evaluation data:', err);
        }
    }
    
    async loadEventLog() {
        try {
            const resp = await fetch('/api/event_log');
            const data = await resp.json();
            const tbody = document.getElementById('tbodyEventLog');
            tbody.innerHTML = '';
            
            (data.events || []).forEach(ev => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="mono">${ev.timestamp}</td>
                    <td><strong>${ev.event_type}</strong></td>
                    <td class="mono">${ev.peak_jerk}</td>
                    <td class="mono">${ev.grip_rise}</td>
                    <td class="mono">${ev.temporal_gap_ms} ms</td>
                    <td><span style="color:var(--highlight-tp); font-weight:600;">${ev.status}</span></td>
                `;
                tbody.appendChild(tr);
            });
        } catch (err) {
            console.error('Error loading event log:', err);
        }
    }
    
    async loadPlaylist() {
        try {
            const resp = await fetch('/api/curated_playlist');
            const data = await resp.json();
            this.playlist = data.playlist || [];
        } catch (err) {
            console.error('Error loading curated playlist:', err);
        }
    }
    
    async loadInitialSubjects() {
        try {
            const resp = await fetch('/api/subjects');
            const data = await resp.json();
            this.subjectSelect.innerHTML = '';
            data.subjects.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                this.subjectSelect.appendChild(opt);
            });
            this.subjectSelect.value = 'SA06';
            await this.updateAvailableCases();
        } catch (err) {
            console.error('Failed to load subjects:', err);
            this.loadSimulatedFallback();
        }
    }
    
    async onSubjectChange() {
        await this.updateAvailableCases();
    }
    
    async onCategoryChange() {
        await this.updateAvailableCases();
    }
    
    async updateAvailableCases() {
        const subj = this.subjectSelect.value || 'SA06';
        const cat = this.categoryFilter.value || 'ALL';
        
        try {
            const resp = await fetch(`/api/catalog_cases?subject=${subj}&category=${encodeURIComponent(cat)}`);
            const data = await resp.json();
            this.availableCases = data.cases || [];
            
            this.caseSelect.innerHTML = '';
            if (this.availableCases.length === 0) {
                const opt = document.createElement('option');
                opt.value = '';
                opt.textContent = 'No recordings match filter';
                this.caseSelect.appendChild(opt);
                return;
            }
            
            this.availableCases.forEach((c, idx) => {
                const opt = document.createElement('option');
                opt.value = idx;
                const tripTag = c.has_fall ? ' [Near-Miss/Fall]' : '';
                opt.textContent = `T${String(c.task).padStart(2, '0')} R${String(c.trial).padStart(2, '0')}: ${c.name}${tripTag}`;
                this.caseSelect.appendChild(opt);
            });
            
            // Prefer Task 30 (Trip) if present
            const tripIndex = this.availableCases.findIndex(c => c.task === 30);
            this.currentCaseIndex = tripIndex >= 0 ? tripIndex : 0;
            this.caseSelect.value = this.currentCaseIndex;
            
            await this.loadActiveRecording();
        } catch (err) {
            console.error('Error updating cases:', err);
        }
    }
    
    onCaseSelect() {
        this.currentCaseIndex = parseInt(this.caseSelect.value || 0);
        this.loadActiveRecording();
    }
    
    navigateCase(direction) {
        if (this.availableCases.length === 0) return;
        this.currentCaseIndex = (this.currentCaseIndex + direction + this.availableCases.length) % this.availableCases.length;
        this.caseSelect.value = this.currentCaseIndex;
        this.loadActiveRecording();
    }
    
    // ------------------------------------------------------------------------
    // RECORDING INGESTION & PLAYBACK
    // ------------------------------------------------------------------------
    
    async loadActiveRecording() {
        if (!this.availableCases || this.availableCases.length === 0) return;
        const curCase = this.availableCases[this.currentCaseIndex];
        if (!curCase) return;
        
        try {
            const url = `/api/load_recording?subject=${curCase.subject}&task=${curCase.task}&trial=${curCase.trial}&jerk_th=${this.jerkThresh}&grip_th=${this.gripThresh}&win_sec=${this.windowSec}`;
            const resp = await fetch(url);
            const data = await resp.json();
            
            this.stream = data.stream;
            this.detection = data.detection;
            this.currentIndex = 0;
            this.scrubber.max = this.stream.n_samples - 1;
            this.scrubber.value = 0;
            
            if (this.stream.data_source === 'REAL') {
                this.provenanceBadge.className = 'provenance-badge real';
                this.provenanceBadge.textContent = `[REAL RECORDING: ${this.stream.subject}_T${String(this.stream.task).padStart(2, '0')}_R${String(this.stream.trial).padStart(2, '0')}]`;
            } else {
                this.provenanceBadge.className = 'provenance-badge simulated';
                this.provenanceBadge.textContent = `[SIMULATED FALLBACK MODE]`;
            }
            
            const metaStr = `Active: ${this.stream.task_desc} (${this.stream.duration_s.toFixed(1)}s @ ${this.stream.fs}Hz) • Category: ${curCase.category}`;
            document.getElementById('traceMeta').textContent = metaStr;
            
            this.resetTallies();
        } catch (err) {
            console.error('Failed to load recording, falling back:', err);
            this.loadSimulatedFallback();
        }
    }
    
    async loadSimulatedFallback() {
        try {
            const resp = await fetch('/api/fallback_simulation?activity=near_miss_trip');
            const data = await resp.json();
            this.stream = data.stream;
            this.detection = data.detection;
            this.currentIndex = 0;
            this.scrubber.max = this.stream.n_samples - 1;
            this.scrubber.value = 0;
            this.provenanceBadge.className = 'provenance-badge simulated';
            this.provenanceBadge.textContent = `[SIMULATED FALLBACK MODE]`;
            document.getElementById('traceMeta').textContent = `${this.stream.task_desc} (${this.stream.duration_s.toFixed(1)}s synthetic)`;
            this.resetTallies();
        } catch (err) {
            console.error('Failed fallback:', err);
        }
    }
    
    async recomputeDetections() {
        if (!this.stream) return;
        try {
            const resp = await fetch('/api/recompute_detection', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jerk_threshold: this.jerkThresh,
                    grip_rise_threshold: this.gripThresh,
                    coincidence_window_sec: this.windowSec
                })
            });
            this.detection = await resp.json();
            this.updateTallyReadouts();
        } catch (err) {
            console.error('Error recomputing detections:', err);
        }
    }
    
    async runPersonalCalibration() {
        const subj = this.stream ? this.stream.subject : 'SA06';
        try {
            const resp = await fetch(`/api/calibrate?subject=${subj}&k=3.0`);
            const data = await resp.json();
            
            this.jerkThresh = data.calibrated_jerk_th;
            this.gripThresh = data.calibrated_grip_th;
            
            this.sliderJerk.value = this.jerkThresh;
            this.valJerk.textContent = this.jerkThresh.toFixed(1);
            this.sliderGrip.value = this.gripThresh;
            this.valGrip.textContent = this.gripThresh.toFixed(1);
            
            this.calibFeedback.textContent = `Personalized for ${data.subject}: T_jerk=${data.calibrated_jerk_th} m/s³, T_grip=${data.calibrated_grip_th} N (derived from steady gait μ + 3σ).`;
            this.recomputeDetections();
        } catch (err) {
            console.error('Error running calibration:', err);
        }
    }
    
    // ------------------------------------------------------------------------
    // 'PLAY ALL CASES' CURATED PLAYLIST AUTO-CYCLE
    // ------------------------------------------------------------------------
    
    startPlayAllCases() {
        if (!this.playlist || this.playlist.length === 0) return;
        this.isPlayingPlaylist = true;
        this.playlistIndex = 0;
        this.playlistStatus.style.display = 'flex';
        this.loadPlaylistCase();
    }
    
    stopPlayAllCases() {
        this.isPlayingPlaylist = false;
        this.playlistStatus.style.display = 'none';
    }
    
    async loadPlaylistCase() {
        if (!this.isPlayingPlaylist || this.playlistIndex >= this.playlist.length) {
            this.stopPlayAllCases();
            return;
        }
        
        const item = this.playlist[this.playlistIndex];
        this.playlistBannerText.textContent = `Auto-Cycling Case ${this.playlistIndex + 1} of ${this.playlist.length}: [${item.subject}] ${item.label} (${item.type})`;
        
        // Select subject
        this.subjectSelect.value = item.subject;
        this.categoryFilter.value = 'ALL';
        await this.updateAvailableCases();
        
        // Find exact task/trial match
        const matchIdx = this.availableCases.findIndex(c => c.task === item.task && c.trial === item.trial);
        if (matchIdx >= 0) {
            this.currentCaseIndex = matchIdx;
            this.caseSelect.value = matchIdx;
            await this.loadActiveRecording();
            this.isPlaying = true;
            this.btnPlay.textContent = '❚❚ PAUSE';
        }
    }
    
    // ------------------------------------------------------------------------
    // PLAYBACK LOOP & TALLIES
    // ------------------------------------------------------------------------
    
    togglePlay() {
        this.isPlaying = !this.isPlaying;
        this.btnPlay.textContent = this.isPlaying ? '❚❚ PAUSE' : '▶ PLAY';
        this.lastFrameTime = performance.now();
    }
    
    onScrub(value) {
        this.currentIndex = parseInt(value);
        this.updateTallyReadouts();
    }
    
    resetTallies() {
        this.tallies = {
            imu_fa: 0, imu_tp: 0,
            grip_fa: 0, grip_tp: 0,
            fused_fa: 0, fused_tp: 0
        };
        this.updateTallyReadouts();
    }
    
    updateTallyReadouts() {
        if (!this.stream || !this.detection) return;
        
        const idx = this.currentIndex;
        const imuActive = this.detection.imu.flags[idx] === 1;
        const gripActive = this.detection.grip.flags[idx] === 1;
        const fusedActive = this.detection.fused.flags[idx] === 1;
        
        // Update Verdict Banners
        if (imuActive) {
            this.verdictIMU.className = 'verdict-banner alarm';
            this.verdictIMU.textContent = 'ALERT: JERK SPIKE';
        } else {
            this.verdictIMU.className = 'verdict-banner';
            this.verdictIMU.textContent = 'NORMAL GAIT';
        }
        
        if (gripActive) {
            this.verdictGrip.className = 'verdict-banner alarm';
            this.verdictGrip.textContent = 'ALERT: GRIP SURGE';
        } else {
            this.verdictGrip.className = 'verdict-banner';
            this.verdictGrip.textContent = 'NORMAL GAIT';
        }
        
        if (fusedActive) {
            this.verdictFused.className = 'verdict-banner alarm';
            this.verdictFused.textContent = 'FUSED: NEAR-MISS CONFIRMED';
        } else {
            this.verdictFused.className = 'verdict-banner';
            this.verdictFused.textContent = 'NORMAL GAIT';
        }
        
        // Compute tallies up to currentIndex
        const tCur = this.stream.time_s[idx];
        const countOccurred = (eventTimes) => eventTimes.filter(t => t <= tCur).length;
        
        const imuEvents = countOccurred(this.detection.imu.event_times);
        const gripEvents = countOccurred(this.detection.grip.event_times);
        const fusedEvents = countOccurred(this.detection.fused.event_times);
        
        if (this.stream.is_fall) {
            this.tallyImuTp.textContent = Math.min(this.detection.imu.true_positives, imuEvents);
            this.tallyImuFa.textContent = Math.max(0, imuEvents - this.detection.imu.true_positives);
            this.tallyGripTp.textContent = Math.min(this.detection.grip.true_positives, gripEvents);
            this.tallyGripFa.textContent = Math.max(0, gripEvents - this.detection.grip.true_positives);
            this.tallyFusedTp.textContent = Math.min(this.detection.fused.true_positives, fusedEvents);
            this.tallyFusedFa.textContent = Math.max(0, fusedEvents - this.detection.fused.true_positives);
        } else {
            this.tallyImuTp.textContent = 0;
            this.tallyImuFa.textContent = imuEvents;
            this.tallyGripTp.textContent = 0;
            this.tallyGripFa.textContent = gripEvents;
            this.tallyFusedTp.textContent = 0;
            this.tallyFusedFa.textContent = fusedEvents;
        }
    }
    
    animationLoop(now) {
        const dt = (now - this.lastFrameTime) / 1000.0;
        this.lastFrameTime = now;
        
        if (this.isPlaying && this.stream) {
            const samplesPerSec = this.stream.fs * this.playbackSpeed;
            this.currentIndex += Math.round(samplesPerSec * dt);
            
            if (this.currentIndex >= this.stream.n_samples) {
                this.currentIndex = this.stream.n_samples - 1;
                this.isPlaying = false;
                this.btnPlay.textContent = '▶ PLAY';
                
                // If in Playlist mode, advance to next after 1.5s pause
                if (this.isPlayingPlaylist) {
                    setTimeout(() => {
                        this.playlistIndex++;
                        this.loadPlaylistCase();
                    }, 1500);
                }
            }
            this.scrubber.value = this.currentIndex;
            this.updateTallyReadouts();
        }
        
        this.renderCanvas();
        requestAnimationFrame((t) => this.animationLoop(t));
    }
    
    // ------------------------------------------------------------------------
    // CANVAS DRAWING (TRACE RECORDER WITH AXES & LABELS)
    // ------------------------------------------------------------------------
    
    renderCanvas() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        
        ctx.clearRect(0, 0, w, h);
        
        // Draw Light Grid & Frame
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let x = 40; x < w; x += 50) {
            ctx.moveTo(x, 15);
            ctx.lineTo(x, h - 25);
        }
        for (let y = 20; y < h - 25; y += 40) {
            ctx.moveTo(40, y);
            ctx.lineTo(w - 10, y);
        }
        ctx.stroke();
        
        // Axes lines
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(40, 15);
        ctx.lineTo(40, h - 25);
        ctx.lineTo(w - 10, h - 25);
        ctx.stroke();
        
        // Axis Labels
        ctx.font = '10px Consolas, monospace';
        ctx.fillStyle = '#475569';
        ctx.fillText('Time (s)', w / 2, h - 8);
        
        ctx.save();
        ctx.translate(12, h / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('|a| (m/s²) / Force (N)', 0, 0);
        ctx.restore();
        
        if (!this.stream) {
            ctx.font = '14px Merriweather, serif';
            ctx.fillStyle = '#94a3b8';
            ctx.textAlign = 'center';
            ctx.fillText('Select a case and press Play to begin kinematic replay', w / 2, h / 2);
            return;
        }
        
        const curSample = this.currentIndex;
        const fs = this.stream.fs;
        const totalSamples = this.stream.n_samples;
        
        // Update Time Readout
        const tCur = (curSample / fs).toFixed(2);
        const tTotal = (totalSamples / fs).toFixed(2);
        this.timeReadout.textContent = `${tCur}s / ${tTotal}s`;
        
        // Display window: 4 seconds width
        const winSamples = Math.round(this.windowSeconds * fs);
        const startSample = Math.max(0, curSample - winSamples);
        const endSample = Math.min(totalSamples, startSample + winSamples);
        
        const plotX = (idx) => 40 + ((idx - startSample) / winSamples) * (w - 60);
        const plotY = (val, maxVal) => (h - 30) - (Math.min(val, maxVal) / maxVal) * (h - 55);
        
        // Draw Ground Truth Interval Shading (if stumbled)
        const gt = this.stream.is_stumble_gt;
        ctx.fillStyle = 'rgba(254, 202, 202, 0.35)';
        let inGt = false;
        let gtStart = 0;
        for (let i = startSample; i < endSample; i++) {
            if (gt[i] === 1 && !inGt) {
                inGt = true;
                gtStart = plotX(i);
            } else if (gt[i] === 0 && inGt) {
                inGt = false;
                ctx.fillRect(gtStart, 20, plotX(i) - gtStart, h - 50);
            }
        }
        if (inGt) {
            ctx.fillRect(gtStart, 20, plotX(endSample) - gtStart, h - 50);
        }
        
        // Draw Acceleration Trace (Dark Graphite)
        ctx.strokeStyle = '#262423';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let started = false;
        for (let i = startSample; i < endSample; i++) {
            const x = plotX(i);
            const y = plotY(this.stream.acc_mag[i], 35.0); // 0 to 35 m/s²
            if (!started) { ctx.moveTo(x, y); started = true; }
            else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
        
        // Draw Grip Force Trace (Olive/Ochre)
        ctx.strokeStyle = '#6e6734';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        started = false;
        for (let i = startSample; i < endSample; i++) {
            const x = plotX(i);
            const y = plotY(this.stream.grip_n[i], 45.0); // 0 to 45 N
            if (!started) { ctx.moveTo(x, y); started = true; }
            else { ctx.lineTo(x, y); }
        }
        ctx.stroke();
        
        // Draw Fused Detection Markers with exact latency brackets
        if (this.detection && this.detection.fused.flags) {
            const fusedFlags = this.detection.fused.flags;
            const gaps = this.detection.fused.timing_gaps || [];
            
            ctx.fillStyle = '#b91c1c';
            ctx.strokeStyle = '#b91c1c';
            ctx.lineWidth = 1.5;
            
            for (let i = startSample; i < endSample; i++) {
                if (fusedFlags[i] === 1) {
                    const x = plotX(i);
                    ctx.beginPath();
                    ctx.arc(x, 28, 4, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // Match timing gap
                    const gapObj = gaps.find(g => Math.abs(g.j_idx - i) <= 2);
                    const gapText = gapObj ? `Δt=${gapObj.gap_ms}ms` : 'Near-Miss';
                    
                    ctx.font = 'bold 9px Consolas, monospace';
                    ctx.fillText(gapText, x - 15, 20);
                }
            }
        }
        
        // Current Time Playhead Cursor (Red vertical line)
        const curX = plotX(curSample);
        if (curX >= 40 && curX <= w - 10) {
            ctx.strokeStyle = '#b91c1c';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(curX, 15);
            ctx.lineTo(curX, h - 25);
            ctx.stroke();
        }
    }
}

// Instantiate once DOM loads
window.addEventListener('DOMContentLoaded', () => {
    window.app = new SmartCaneDemoApp();
});
