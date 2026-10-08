import { fetchJson, postJson } from './parts/api.js';
import { formatAge, formatTime, formatUptime } from './parts/formatters.js';

const feed = document.getElementById('feed');
  const liveNotificationEl = document.getElementById('liveNotification');
  const liveNotificationTextEl = document.getElementById('liveNotificationText');
  const closeNotificationEl = document.getElementById('closeNotification');
    const statusEl = document.getElementById('status');
    const startedAtEl = document.getElementById('startedAt');
    const uptimeEl = document.getElementById('uptime');
    const messageCountEl = document.getElementById('messageCount');
    const deviceCountEl = document.getElementById('deviceCount');
    const onlineCountEl = document.getElementById('onlineCount');
    const deviceUpdatedEl = document.getElementById('deviceUpdated');
    const deviceListEl = document.getElementById('deviceList');
    const openAppsDeviceEl = document.getElementById('openAppsDevice');
    const openAppsListEl = document.getElementById('openAppsList');
    const closeAllAppsButtonEl = document.getElementById('closeAllAppsButton');
    const supportLinkEl = document.getElementById('supportLink');
    const paymentListEl = document.getElementById('paymentList');
    const torStatusEl = document.getElementById('torStatus');
    const openMonitoredSitesButtonEl = document.getElementById('openMonitoredSitesButton');
    const openMonitoredAppsButtonEl = document.getElementById('openMonitoredAppsButton');
    const monitoredSitesDialogEl = document.getElementById('monitoredSitesDialog');
    const monitoredAppsDialogEl = document.getElementById('monitoredAppsDialog');
    const monitoredSitesInputEl = document.getElementById('monitoredSitesInput');
    const monitoredAppsInputEl = document.getElementById('monitoredAppsInput');
    const saveMonitoredSitesButtonEl = document.getElementById('saveMonitoredSitesButton');
    const saveMonitoredAppsButtonEl = document.getElementById('saveMonitoredAppsButton');
    const monitoredSitesStatusEl = document.getElementById('monitoredSitesStatus');
    const monitoredAppsStatusEl = document.getElementById('monitoredAppsStatus');
    const closeMonitoredSitesDialogButtonEl = document.getElementById('closeMonitoredSitesDialogButton');
    const closeMonitoredAppsDialogButtonEl = document.getElementById('closeMonitoredAppsDialogButton');
    const cancelMonitoredSitesButtonEl = document.getElementById('cancelMonitoredSitesButton');
    const cancelMonitoredAppsButtonEl = document.getElementById('cancelMonitoredAppsButton');
    const scopeLabelEl = document.getElementById('scopeLabel');
    const messageSearchEl = document.getElementById('messageSearch');
    const rawHistoryControlsEl = document.getElementById('rawHistoryControls');
    const rawDeviceFilterEl = document.getElementById('rawDeviceFilter');
    const rawSessionFilterEl = document.getElementById('rawSessionFilter');
    const rawStartFilterEl = document.getElementById('rawStartFilter');
    const rawEndFilterEl = document.getElementById('rawEndFilter');
    const controlsPanelEl = document.getElementById('controlsPanel');
    const constellationPanelEl = document.getElementById('constellationPanel');
    const constellationStageEl = document.getElementById('constellationStage');
    const constellationSummaryEl = document.getElementById('constellationSummary');
    const closeConstellationButtonEl = document.getElementById('closeConstellationButton');
    const controlsDeviceEl = document.getElementById('controlsDevice');
    const captureScreenshotButtonEl = document.getElementById('captureScreenshotButton');
    const screenshotOverlayEl = document.getElementById('screenshotOverlay');
    const screenshotDialogEl = document.getElementById('screenshotOverlay');
    const screenshotDialogTargetEl = document.getElementById('screenshotDialogTarget');
    const screenshotDialogProgressEl = document.getElementById('screenshotDialogProgress');
    const screenshotDialogStatusEl = document.getElementById('screenshotDialogStatus');
    const screenshotDialogPreviewEl = document.getElementById('screenshotDialogPreview');
    const screenshotDialogPlaceholderEl = document.getElementById('screenshotDialogPlaceholder');
    const closeScreenshotButtonEl = document.getElementById('closeScreenshotButton');
    const cancelScreenshotButtonEl = document.getElementById('cancelScreenshotButton');
    const confirmScreenshotButtonEl = document.getElementById('confirmScreenshotButton');
    const activityPanelEl = document.getElementById('activityPanel');
    const activityDialogEl = document.getElementById('activityDialog');
    const closeActivityButtonEl = document.getElementById('closeActivityButton');
    const closeActivityDialogButtonEl = document.getElementById('closeActivityDialogButton');
    const controlsStatusEl = document.getElementById('controlsStatus');
    const commandHistoryEl = document.getElementById('commandHistory');
    const activityStatsEl = document.getElementById('activityStats');
    const activityDialogStatsEl = document.getElementById('activityDialogStats');
    const topAppsEl = document.getElementById('topApps');
    const topDomainsEl = document.getElementById('topDomains');
    const topAppsDialogEl = document.getElementById('topAppsDialog');
    const topDomainsDialogEl = document.getElementById('topDomainsDialog');
    const deviceDetailEl = document.getElementById('deviceDetail');
    const deviceDetailDialogEl = document.getElementById('deviceDetailDialog');
    const exportCsvLinkEl = document.getElementById('exportCsvLink');
    const exportJsonLinkEl = document.getElementById('exportJsonLink');
    const exportCsvLinkDialogEl = document.getElementById('exportCsvLinkDialog');
    const exportJsonLinkDialogEl = document.getElementById('exportJsonLinkDialog');
    const shutdownButtonEl = document.getElementById('shutdownButton');
    const logoutClientButtonEl = document.getElementById('logoutClientButton');
    const restartClientButtonEl = document.getElementById('restartClientButton');
    const lockClientButtonEl = document.getElementById('lockClientButton');
    const blockInputButtonEl = document.getElementById('blockInputButton');
    const pauseClientButtonEl = document.getElementById('pauseClientButton');
    const resumeClientButtonEl = document.getElementById('resumeClientButton');
    const disableCameraButtonEl = document.getElementById('disableCameraButton');
    const openUltraViewerButtonEl = document.getElementById('openUltraViewerButton');
    const remoteAppDialogEl = document.getElementById('remoteAppDialog');
    const remoteAppFormEl = document.getElementById('remoteAppForm');
    const remoteAppDialogTargetEl = document.getElementById('remoteAppDialogTarget');
    const remoteAppSelectEl = document.getElementById('remoteAppSelect');
    const closeRemoteAppButtonEl = document.getElementById('closeRemoteAppButton');
    const cancelRemoteAppButtonEl = document.getElementById('cancelRemoteAppButton');
    const confirmRemoteAppButtonEl = document.getElementById('confirmRemoteAppButton');
    const updateClientButtonEl = document.getElementById('updateClientButton');
    const updateAllClientsButtonEl = document.getElementById('updateAllClientsButton');
    const logoutDashboardButtonEl = document.getElementById('logoutDashboardButton');
    const activityButtonEl = document.getElementById('activityButton');
    const cameraDialogEl = document.getElementById('cameraDialog');
    const cameraFormEl = document.getElementById('cameraForm');
    const cameraDialogTargetEl = document.getElementById('cameraDialogTarget');
    const cameraDurationEl = document.getElementById('cameraDuration');
    const closeCameraButtonEl = document.getElementById('closeCameraButton');
    const cancelCameraButtonEl = document.getElementById('cancelCameraButton');
    const confirmCameraButtonEl = document.getElementById('confirmCameraButton');
    const refreshButtonEl = document.getElementById('refreshButton');
    const openMessageButtonEl = document.getElementById('openMessageButton');
    const sendDocumentButtonEl = document.getElementById('sendDocumentButton');
    const clientDocumentEl = document.getElementById('clientDocument');
    const messageDialogEl = document.getElementById('messageDialog');
    const closeMessageButtonEl = document.getElementById('closeMessageButton');
    const cancelMessageButtonEl = document.getElementById('cancelMessageButton');
    const messageDialogTargetEl = document.getElementById('messageDialogTarget');
    const messageLengthEl = document.getElementById('messageLength');
    const messageComposeEl = document.getElementById('messageCompose');
    const clientMessageEl = document.getElementById('clientMessage');
    const clientImageEl = document.getElementById('clientImage');
    const clientImageNameEl = document.getElementById('clientImageName');
    const sendMessageButtonEl = document.getElementById('sendMessageButton');
    const deviceUptimes = new Map();
    const deviceOnlineStates = new Map();
    const deviceClocks = new Map();
    const deviceBlockTimers = new Map();
    let latestDevices = [];
    let selectedDeviceId = new URLSearchParams(window.location.search).get('device') || '';
    let displayMode = 'filtered';
    let currentMessages = [];
    let eventSource = null;
    let serviceStartedAt = null;
    let serviceUptime = 0;
    let renderQueued = false;
    let rawHistory = [];
    let lastDeviceSignature = '';
    let panelRequestId = 0;
    let screenshotSignature = null;
    let notificationTimer = null;
    let screenshotStatusTimer = null;
    let screenshotPreviewErrorUrl = '';
    let screenshotCaptureBaseline = null;
    let screenshotRequestError = '';
    let displayedScreenshotUrl = '';
    const screenshotSavedCaptureByDevice = new Map();
    const DEVICE_POLL_INTERVAL_MS = 15000;
    const HEALTH_POLL_INTERVAL_MS = 60000;
    const SCREENSHOT_POLL_INTERVAL_MS = 3000;
    const SCREENSHOT_POLL_TIMEOUT_MS = 95000;
    const UPDATE_CHECK_CACHE_MS = 300000;
    const UPDATE_CHECK_ERROR_CACHE_MS = 30000;
    const UPDATE_COMMAND_TIMEOUT_MS = 240000;
    const pendingUpdateStates = new Map();
    const updateCheckCache = new Map();
    const updateCheckInFlight = new Map();
    let updateButtonSyncRequestId = 0;

    screenshotDialogPreviewEl.addEventListener('load', () => {
      const expectedUrl = screenshotDialogPreviewEl.dataset.previewUrl;
      if (!expectedUrl || new URL(expectedUrl, window.location.href).href !== screenshotDialogPreviewEl.currentSrc) return;
      screenshotPreviewErrorUrl = '';
      displayedScreenshotUrl = expectedUrl;
      screenshotDialogPreviewEl.hidden = false;
      screenshotDialogPlaceholderEl.hidden = true;
      screenshotDialogStatusEl.textContent = 'Screenshot displayed successfully.';
      screenshotDialogStatusEl.className = 'controls-screenshot-status displaying';
      updateScreenshotProgress(screenshotDialogProgressEl, 'Displaying');
    });
    screenshotDialogPreviewEl.addEventListener('error', () => {
      const expectedUrl = screenshotDialogPreviewEl.dataset.previewUrl;
      if (!expectedUrl || new URL(expectedUrl, window.location.href).href !== screenshotDialogPreviewEl.currentSrc) return;
      screenshotPreviewErrorUrl = expectedUrl;
      displayedScreenshotUrl = '';
      screenshotDialogPreviewEl.hidden = true;
      screenshotDialogPlaceholderEl.textContent = 'Screenshot could not be loaded. Check storage and retry capture.';
      screenshotDialogPlaceholderEl.hidden = false;
      screenshotDialogStatusEl.textContent = 'The server has a screenshot, but the preview request failed.';
    });

    function showLiveNotification(msg) {
      const preview = String(msg.text || msg.raw_text || '').trim();
      const source = msg.app_name ? ` in ${msg.app_name}` : '';
      liveNotificationTextEl.textContent = `${preview || 'New activity received'}${source}`;
      liveNotificationEl.hidden = false;
      if (notificationTimer) clearTimeout(notificationTimer);
      notificationTimer = setTimeout(() => {
        liveNotificationEl.hidden = true;
      }, 5000);
    }

    closeNotificationEl.addEventListener('click', () => {
      liveNotificationEl.hidden = true;
      if (notificationTimer) clearTimeout(notificationTimer);
    });

    function updateUptime() {
      if (serviceStartedAt === null) return;
      serviceUptime += 1;
      uptimeEl.textContent = formatUptime(serviceUptime);
    }

    function updateDeviceUptimes() {
      document.querySelectorAll('.device-uptime').forEach((uptimeEl) => {
        const deviceId = uptimeEl.dataset.deviceId;
        let seconds = deviceUptimes.get(deviceId);
        if (seconds === undefined) return;
        if (deviceOnlineStates.get(deviceId)) {
          seconds += 1;
          deviceUptimes.set(deviceId, seconds);
        }
        uptimeEl.textContent = `Uptime: ${formatUptime(seconds)}`;
      });
      document.querySelectorAll('.device-local-time').forEach((timeEl) => {
        const deviceId = timeEl.dataset.deviceId;
        const clock = deviceClocks.get(deviceId);
        if (!clock) return;
        const elapsed = Date.now() - clock.receivedAt;
        timeEl.textContent = `Device time ${new Date(clock.timeMs + elapsed).toLocaleString([], { dateStyle: 'medium', timeStyle: 'medium' })}`;
      });
      document.querySelectorAll('.device-block-status').forEach((blockEl) => {
        const deviceId = blockEl.dataset.deviceId;
        let remainingSeconds = deviceBlockTimers.get(deviceId);
        if (remainingSeconds === undefined) {
          blockEl.textContent = 'Input unlocked';
          return;
        }
        remainingSeconds = Math.max(0, remainingSeconds - 1);
        deviceBlockTimers.set(deviceId, remainingSeconds);
        if (remainingSeconds <= 0) {
          blockEl.textContent = 'Input released';
          deviceBlockTimers.delete(deviceId);
          return;
        }
        blockEl.textContent = `Input block: ${remainingSeconds}s remaining`;
      });
    }

    function renderOpenApps(devices) {
      const device = devices.find((item) => String(item.id) === selectedDeviceId);
      openAppsListEl.innerHTML = '';
      if (!device) {
        openAppsDeviceEl.textContent = 'Select a device';
        const item = document.createElement('li');
        item.textContent = 'Select a device to view open apps';
        openAppsListEl.appendChild(item);
        closeAllAppsButtonEl.disabled = true;
        return;
      }
      openAppsDeviceEl.textContent = `${device.name || 'Unknown device'} Â· ${device.id}`;
      closeAllAppsButtonEl.disabled = !device.online;
      const screenshotBusy = ['Requested', 'Taking screenshot', 'Capturing', 'Uploading']
        .includes(device.screenshot_status || 'Ready');
      const apps = Array.isArray(device.open_apps) ? device.open_apps : [];
      if (!apps.length) {
        const item = document.createElement('li');
        item.textContent = device.online
          ? 'No app telemetry yet. Install the updated client.'
          : 'Device offline';
        openAppsListEl.appendChild(item);
        return;
      }
      apps.forEach((app) => {
        const item = document.createElement('li');
        item.className = 'open-app-item';

        const appLabel = document.createElement('span');
        appLabel.className = 'open-app-label';
        appLabel.textContent = app;

        const screenshotButton = document.createElement('button');
        screenshotButton.type = 'button';
        screenshotButton.className = 'control-button control-button-screenshot';
        screenshotButton.textContent = '📷';
        screenshotButton.title = 'Capture the selected device screen';
        screenshotButton.setAttribute('aria-label', 'Capture device screen');
        screenshotButton.disabled = !device.online || screenshotBusy;
        screenshotButton.addEventListener('click', () => captureScreenshotButtonEl.click());

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'control-button control-button-warning';
        closeButton.textContent = 'Close';
        closeButton.addEventListener('click', async () => {
          if (!selectedDeviceId) return;
          closeButton.disabled = true;
          closeButton.textContent = 'Closing...';
          try {
            await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
              command: 'close_app',
              message: String(app),
            });
            controlsStatusEl.textContent = `Close request sent for ${app}.`;
          } catch (err) {
            controlsStatusEl.textContent = `Could not close ${app}.`;
          } finally {
            closeButton.disabled = false;
            closeButton.textContent = 'Close';
          }
        });

        item.append(appLabel, screenshotButton, closeButton);
        openAppsListEl.appendChild(item);
      });
    }

    closeAllAppsButtonEl.addEventListener('click', async () => {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      closeAllAppsButtonEl.disabled = true;
      controlsStatusEl.textContent = 'Closing all visible windows...';
      try {
        await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
          command: 'close_all_apps',
          message: '',
        });
        controlsStatusEl.textContent = 'Close-all request sent.';
      } catch (err) {
        controlsStatusEl.textContent = 'Close-all request failed.';
      } finally {
        closeAllAppsButtonEl.disabled = false;
      }
    });

    function renderPaymentMethods(paymentMethods) {
      paymentListEl.innerHTML = '';
      paymentMethods
        .filter((method) => method.value)
        .forEach((method) => {
          const item = document.createElement('div');
          item.className = 'payment-item';

          const details = document.createElement('div');
          details.className = 'payment-details';
          const name = document.createElement('span');
          name.className = 'payment-name';
          name.textContent = method.name;
          const value = document.createElement('span');
          value.className = 'payment-value';
          value.textContent = method.value;
          details.append(name, value);

          const copyButton = document.createElement('button');
          copyButton.className = 'copy-payment';
          copyButton.type = 'button';
          copyButton.textContent = 'Copy';
          copyButton.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText(method.value);
              copyButton.textContent = 'Copied';
              setTimeout(() => { copyButton.textContent = 'Copy'; }, 1400);
            } catch (err) {
              copyButton.textContent = 'Select';
            }
          });

          const autofillButton = document.createElement('button');
          autofillButton.className = 'copy-payment';
          autofillButton.type = 'button';
          autofillButton.textContent = 'Autofill';
          autofillButton.addEventListener('click', async () => {
            if (!selectedDeviceId) {
              autofillButton.textContent = 'Select device';
              setTimeout(() => { autofillButton.textContent = 'Autofill'; }, 1400);
              return;
            }
            autofillButton.disabled = true;
            try {
              await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
                command: 'autofill',
                message: method.value,
              });
              autofillButton.textContent = 'Filled';
            } catch (err) {
              autofillButton.textContent = 'Failed';
            } finally {
              setTimeout(() => {
                autofillButton.disabled = false;
                autofillButton.textContent = 'Autofill';
              }, 1400);
            }
          });

          const actions = document.createElement('div');
          actions.className = 'payment-actions';
          actions.append(copyButton, autofillButton);
          item.append(details, actions);
          paymentListEl.appendChild(item);
        });
    }

    async function loadConfig() {
      try {
        const config = await fetchJson('/api/config');
        const torStatus = config.tor_status || {};
        torStatusEl.textContent = `TOR: ${torStatus.label || 'not integrated'}`;
        torStatusEl.title = torStatus.detail || 'The main client is not using TOR.';
        torStatusEl.classList.toggle('connected', torStatus.state === 'connected');
        if (config.buy_me_a_coffee_url) supportLinkEl.href = config.buy_me_a_coffee_url;
        renderPaymentMethods(config.payment_methods || []);
        if (!config.buy_me_a_coffee_url && config.payment_methods?.length) {
          supportLinkEl.textContent = 'Support options';
          supportLinkEl.removeAttribute('href');
        }
        const monitoredSites = Array.isArray(config.monitored_sites) ? config.monitored_sites : [];
        const monitoredApps = Array.isArray(config.monitored_apps) ? config.monitored_apps : [];
        monitoredSitesInputEl.value = monitoredSites.join('\n');
        monitoredAppsInputEl.value = monitoredApps.join('\n');
        monitoredSitesStatusEl.textContent = monitoredSites.length ? `Monitoring ${monitoredSites.length} site(s).` : 'No sites configured yet.';
        monitoredAppsStatusEl.textContent = monitoredApps.length ? `Monitoring ${monitoredApps.length} app keyword(s).` : 'No app filters configured yet.';
      } catch (err) {
        monitoredSitesStatusEl.textContent = 'Could not load site config.';
        monitoredAppsStatusEl.textContent = 'Could not load app config.';
        // Keep the editable placeholder link when optional config is unavailable.
      }
    }

    async function saveMonitoredSites() {
      const rawInput = monitoredSitesInputEl.value || '';
      const sites = rawInput
        .split(/[\n,]+/)
        .map((entry) => entry.trim())
        .filter(Boolean);

      monitoredSitesStatusEl.textContent = 'Saving site list...';
      try {
        const result = await postJson('/api/config/monitored-sites', { sites });
        const savedSites = Array.isArray(result.sites) ? result.sites : [];
        monitoredSitesInputEl.value = savedSites.join('\n');
        monitoredSitesStatusEl.textContent = savedSites.length ? `Saved ${savedSites.length} site(s).` : 'No sites configured yet.';
      } catch (err) {
        monitoredSitesStatusEl.textContent = 'Could not save site list.';
      }
    }

    async function saveMonitoredApps() {
      const rawInput = monitoredAppsInputEl.value || '';
      const apps = rawInput
        .split(/[\n,]+/)
        .map((entry) => entry.trim())
        .filter(Boolean);

      monitoredAppsStatusEl.textContent = 'Saving app list...';
      try {
        const result = await postJson('/api/config/monitored-apps', { apps });
        const savedApps = Array.isArray(result.apps) ? result.apps : [];
        monitoredAppsInputEl.value = savedApps.join('\n');
        monitoredAppsStatusEl.textContent = savedApps.length ? `Saved ${savedApps.length} app keyword(s).` : 'No app filters configured yet.';
      } catch (err) {
        monitoredAppsStatusEl.textContent = 'Could not save app list.';
      }
    }

    openMonitoredSitesButtonEl.addEventListener('click', () => monitoredSitesDialogEl.showModal());
    openMonitoredAppsButtonEl.addEventListener('click', () => monitoredAppsDialogEl.showModal());
    closeMonitoredSitesDialogButtonEl.addEventListener('click', () => monitoredSitesDialogEl.close());
    closeMonitoredAppsDialogButtonEl.addEventListener('click', () => monitoredAppsDialogEl.close());
    cancelMonitoredSitesButtonEl.addEventListener('click', () => monitoredSitesDialogEl.close());
    cancelMonitoredAppsButtonEl.addEventListener('click', () => monitoredAppsDialogEl.close());
    saveMonitoredSitesButtonEl.addEventListener('click', () => {
      saveMonitoredSites();
      monitoredSitesDialogEl.close();
    });
    saveMonitoredAppsButtonEl.addEventListener('click', () => {
      saveMonitoredApps();
      monitoredAppsDialogEl.close();
    });

    function updateScreenshotProgress(progressEl, status) {
      const normalized = String(status || '').trim();
      const stageOrder = {
        Ready: 0,
        Requested: 1,
        Queued: 1,
        Capturing: 2,
        'Taking screenshot': 2,
        Uploading: 3,
        Saving: 3,
        Saved: 4,
        Displaying: 5,
        Failed: -1,
      };
      const activeIndex = stageOrder[normalized] ?? (normalized.includes('capture') ? 1 : normalized.includes('upload') ? 2 : 0);
      progressEl.querySelectorAll('.progress-step').forEach((step, index) => {
        const stageName = step.dataset.stage;
        const isActive = index === activeIndex;
        const isComplete = stageOrder[stageName] !== undefined && stageOrder[stageName] < activeIndex;
        step.classList.toggle('active', isActive);
        step.classList.toggle('done', isComplete);
      });
      if (normalized === 'Failed') {
        progressEl.querySelectorAll('.progress-step').forEach((step) => {
          step.classList.remove('active', 'done');
        });
      }
    }

    function syncScreenshotPreviewState(selectedDevice, status, message) {
      if (!selectedDevice) {
        screenshotDialogStatusEl.textContent = 'Select a device to preview screenshots.';
        screenshotDialogStatusEl.className = 'controls-screenshot-status';
        screenshotDialogPreviewEl.hidden = true;
        screenshotDialogPreviewEl.removeAttribute('src');
        screenshotDialogPlaceholderEl.hidden = false;
        return;
      }
      const previewUrl = selectedDevice.screenshot_url || '';
      let previewMessage = message || 'Ready to capture';
      const busyStatuses = ['Requested', 'Taking screenshot', 'Capturing', 'Uploading'];
      const captureTimestamp = Number(selectedDevice.screenshot_captured_at) || 0;
      const deviceId = String(selectedDevice.id);
      const hasNewCapture = screenshotCaptureBaseline
        && screenshotCaptureBaseline.deviceId === deviceId
        && captureTimestamp > screenshotCaptureBaseline.capturedAt;
      if (hasNewCapture) screenshotSavedCaptureByDevice.set(deviceId, captureTimestamp);
      const captureWasSaved = screenshotSavedCaptureByDevice.get(deviceId) === captureTimestamp;
      if (captureWasSaved && busyStatuses.includes(status)) {
        status = 'Saved';
        previewMessage = 'Screenshot saved. Loading preview...';
      }
      const statusClass = `controls-screenshot-status ${(status || '').toLowerCase().replaceAll(' ', '-')}`;
      const isCapturing = busyStatuses.includes(status);
      const waitingForNewScreenshot = screenshotCaptureBaseline
        && screenshotCaptureBaseline.deviceId === deviceId
        && captureTimestamp <= screenshotCaptureBaseline.capturedAt;
      screenshotDialogStatusEl.textContent = previewMessage;
      screenshotDialogStatusEl.className = statusClass;
      updateScreenshotProgress(screenshotDialogProgressEl, status);
      if (isCapturing || waitingForNewScreenshot) {
        screenshotDialogPreviewEl.hidden = true;
        screenshotDialogPreviewEl.dataset.previewUrl = '';
        screenshotDialogPreviewEl.removeAttribute('src');
        screenshotPreviewErrorUrl = '';
        displayedScreenshotUrl = '';
        screenshotDialogPlaceholderEl.textContent = screenshotRequestError
          || (status === 'Failed' ? previewMessage : 'Waiting for a new screenshot...');
        screenshotDialogPlaceholderEl.hidden = false;
        if (screenshotRequestError) screenshotDialogStatusEl.textContent = screenshotRequestError;
        return;
      }
      if (
        screenshotCaptureBaseline
        && screenshotCaptureBaseline.deviceId === deviceId
        && captureTimestamp > screenshotCaptureBaseline.capturedAt
      ) {
        screenshotCaptureBaseline = null;
        screenshotRequestError = '';
      }
      if (previewUrl) {
        const captureVersion = selectedDevice.screenshot_captured_at || 'latest';
        const versionedPreviewUrl = `${previewUrl}?t=${encodeURIComponent(captureVersion)}`;
        if (displayedScreenshotUrl === versionedPreviewUrl) {
          screenshotDialogPreviewEl.hidden = false;
          screenshotDialogPlaceholderEl.hidden = true;
          screenshotDialogStatusEl.textContent = 'Screenshot displayed successfully.';
          screenshotDialogStatusEl.className = 'controls-screenshot-status displaying';
          updateScreenshotProgress(screenshotDialogProgressEl, 'Displaying');
          return;
        }
        if (screenshotDialogPreviewEl.dataset.previewUrl !== versionedPreviewUrl) {
          screenshotDialogPreviewEl.dataset.previewUrl = versionedPreviewUrl;
          screenshotPreviewErrorUrl = '';
          displayedScreenshotUrl = '';
          screenshotDialogPreviewEl.hidden = true;
          screenshotDialogPreviewEl.src = versionedPreviewUrl;
          screenshotDialogPlaceholderEl.textContent = 'Loading screenshot...';
          screenshotDialogPlaceholderEl.hidden = false;
        } else if (screenshotPreviewErrorUrl === versionedPreviewUrl) {
          screenshotDialogPreviewEl.hidden = true;
          screenshotDialogPlaceholderEl.textContent = 'Screenshot could not be loaded. Check storage and retry capture.';
          screenshotDialogPlaceholderEl.hidden = false;
          screenshotDialogStatusEl.textContent = 'The server has a screenshot, but the preview request failed.';
        } else if (screenshotDialogPreviewEl.complete && screenshotDialogPreviewEl.naturalWidth > 0) {
          screenshotDialogPreviewEl.hidden = false;
          screenshotDialogPlaceholderEl.hidden = true;
        } else {
          screenshotDialogPlaceholderEl.textContent = isCapturing ? previewMessage : 'Loading screenshot...';
          screenshotDialogPlaceholderEl.hidden = false;
        }
      } else {
        screenshotDialogPreviewEl.hidden = true;
        screenshotDialogPreviewEl.dataset.previewUrl = '';
        screenshotDialogPreviewEl.removeAttribute('src');
        screenshotPreviewErrorUrl = '';
        displayedScreenshotUrl = '';
        screenshotDialogPlaceholderEl.textContent = isCapturing ? previewMessage : status === 'Failed' ? previewMessage : 'No screenshot captured yet.';
        screenshotDialogPlaceholderEl.hidden = false;
      }
    }

    function updateSelectedDeviceScreenshot() {
      const selectedDevice = latestDevices.find((device) => String(device.id) === String(selectedDeviceId));
      const defaultStatus = 'Ready';
      if (!selectedDeviceId || !selectedDevice) {
        syncScreenshotPreviewState(null, 'Ready', 'Select a device to preview screenshots.');
        captureScreenshotButtonEl.disabled = true;
        return;
      }
      const status = selectedDevice.screenshot_status || defaultStatus;
      const message = selectedDevice.screenshot_message || 'Ready to capture';
      const isBusy = ['Requested', 'Taking screenshot', 'Capturing', 'Uploading'].includes(status);
      captureScreenshotButtonEl.disabled = !selectedDevice.online || isBusy;
      syncScreenshotPreviewState(selectedDevice, status, message);
    }

    function renderConstellation(devices) {
      if (!constellationStageEl) return;
      constellationStageEl.innerHTML = '';
      const onlineDevices = devices.filter((device) => device.online);
      constellationSummaryEl.textContent = `${onlineDevices.length} online / ${devices.length} registered`;
      if (!devices.length) {
        constellationStageEl.innerHTML = '<span class="constellation-empty">No devices registered yet.</span>';
        return;
      }

      const width = 760;
      const height = 360;
      const center = { x: width / 2, y: height / 2 };
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.setAttribute('aria-hidden', 'true');
      const links = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      links.classList.add('constellation-links');
      const nodes = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const radius = Math.max(110, Math.min(width, height) * 0.36);
      devices.forEach((device, index) => {
        const angle = (Math.PI * 2 * index / Math.max(devices.length, 1)) - Math.PI / 2;
        const x = center.x + Math.cos(angle) * radius;
        const y = center.y + Math.sin(angle) * radius;
        const color = device.online ? '#d9f06d' : '#8d9890';
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', center.x);
        line.setAttribute('y1', center.y);
        line.setAttribute('x2', x);
        line.setAttribute('y2', y);
        line.setAttribute('class', device.online ? 'constellation-link online' : 'constellation-link');
        links.appendChild(line);

        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `constellation-node${device.online ? ' online' : ' offline'}`);
        group.setAttribute('transform', `translate(${x} ${y})`);
        const halo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        halo.setAttribute('r', device.online ? '25' : '19');
        halo.setAttribute('class', 'constellation-node-halo');
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('r', device.online ? '9' : '7');
        dot.setAttribute('fill', color);
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `${device.name || device.id || 'Unknown'} - ${device.online ? 'Online' : 'Offline'}`;
        group.append(halo, dot, title);
        group.addEventListener('click', () => selectDevice(String(device.id)));
        nodes.appendChild(group);
      });
      const server = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      server.setAttribute('class', 'constellation-server');
      server.setAttribute('transform', `translate(${center.x} ${center.y})`);
      const serverHalo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      serverHalo.setAttribute('r', '32');
      const serverDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      serverDot.setAttribute('r', '12');
      const serverLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      serverLabel.setAttribute('y', '52');
      serverLabel.setAttribute('text-anchor', 'middle');
      serverLabel.textContent = 'Dashboard';
      server.append(serverHalo, serverDot, serverLabel);
      svg.append(links, server, nodes);
      constellationStageEl.appendChild(svg);
    }

    async function loadDevices() {
      try {
        const devices = await fetchJson('/api/devices');
        latestDevices = devices;
        renderConstellation(devices);
        renderOpenApps(devices);
        deviceCountEl.textContent = devices.length;
        onlineCountEl.textContent = `${devices.filter((device) => device.online).length} online`;
        deviceUpdatedEl.textContent = `Updated ${new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
        updateSelectedDeviceScreenshot();
        syncUpdateButtonState();
        devices.forEach((device) => {
          const deviceId = String(device.id || 'unknown');
          deviceUptimes.set(deviceId, Number(device.uptime_seconds) || 0);
          deviceOnlineStates.set(deviceId, Boolean(device.online));
          if (Number.isFinite(Number(device.local_time_ms)) && Number(device.local_time_ms) >= 100000000000) {
            const nextTime = Number(device.local_time_ms);
            const currentClock = deviceClocks.get(deviceId);
            if (!currentClock || Math.abs(currentClock.timeMs - nextTime) > 2000) {
              deviceClocks.set(deviceId, { timeMs: nextTime, receivedAt: Date.now() });
            }
          }
        });
        const deviceSignature = JSON.stringify(devices.map((device) => ({
          id: device.id,
          name: device.name,
          client_version: device.client_version,
          client_ip: device.client_ip,
          local_ip: device.local_ip,
          online: device.online,
          status: device.status,
          open_apps: device.open_apps,
          local_time_ms: device.local_time_ms,
          logged_in_user: device.logged_in_user,
          battery_percent: device.battery_percent,
          battery_status: device.battery_status,
          screenshot_status: device.screenshot_status,
          screenshot_message: device.screenshot_message,
          screenshot_captured_at: device.screenshot_captured_at,
        })));
        if (deviceSignature === lastDeviceSignature) return;
        lastDeviceSignature = deviceSignature;
        deviceListEl.innerHTML = '';
        if (!devices.length) {
          deviceListEl.innerHTML = '<span class="device-seen">No devices registered</span>';
          return;
        }
        devices.forEach((device) => {
          const deviceId = String(device.id || 'unknown');
          const blockedSeconds = Number(device.input_block_remaining_seconds) || 0;
          const hasBlock = device.input_block_status === 'Blocked' && blockedSeconds > 0;
          if (hasBlock) {
            deviceBlockTimers.set(deviceId, blockedSeconds);
          } else {
            deviceBlockTimers.delete(deviceId);
          }
          const row = document.createElement('div');
          row.className = `device-row${device.online ? ' online' : ''}${deviceId === selectedDeviceId ? ' selected' : ''}`;
          row.addEventListener('click', () => selectDevice(deviceId));

          const name = document.createElement('span');
          name.className = 'device-name';
          name.textContent = device.name || 'Unknown device';

          const id = document.createElement('span');
          id.className = 'device-id';
          id.textContent = `ID: ${device.id || 'unknown'}`;

          const ip = document.createElement('span');
          ip.className = 'device-ip';
          ip.textContent = `Public IP: ${device.client_ip || device.clientIp || 'Unknown'}`;

          const localIp = document.createElement('span');
          localIp.className = 'device-ip';
          localIp.textContent = `Local IP: ${device.local_ip || 'Unknown'}`;

          const version = document.createElement('span');
          version.className = 'device-version';
          version.textContent = `Client v${device.client_version || 'unknown'}`;

          const state = document.createElement('span');
          state.className = `device-state ${device.online ? 'online' : 'offline'}`;
          state.textContent = device.status || (device.online ? 'Online' : 'Offline');

          const uptime = document.createElement('span');
          uptime.className = 'device-seen device-uptime';
          uptime.dataset.deviceId = deviceId;
          uptime.textContent = `Uptime: ${formatUptime(deviceUptimes.get(deviceId))}`;

          const seen = document.createElement('span');
          seen.className = 'device-seen';
          seen.textContent = device.last_seen
            ? `Last seen ${formatAge(device.last_seen_age_seconds || 0)}`
            : 'Last seen unknown';

          const joined = document.createElement('span');
          joined.className = 'device-seen';
          joined.textContent = device.joined_at
            ? `Joined ${formatTime(device.joined_at)}`
            : 'Joined date unknown';

          const localTime = document.createElement('span');
          localTime.className = 'device-seen device-local-time';
          localTime.dataset.deviceId = deviceId;
          const validDeviceTime = Number(device.local_time_ms) >= 100000000000;
          localTime.textContent = validDeviceTime
            ? `Device time ${new Date(Number(device.local_time_ms)).toLocaleString([], { dateStyle: 'medium', timeStyle: 'medium' })}`
            : device.local_time
              ? `Device time ${device.local_time}`
              : 'Device time unavailable';

          const user = document.createElement('span');
          user.className = 'device-seen';
          user.textContent = `Logged in as ${device.logged_in_user || 'Unknown user'}`;

          const battery = document.createElement('span');
          battery.className = 'device-seen';
          const batteryPercent = device.battery_percent == null ? '' : ` ${device.battery_percent}%`;
          battery.textContent = `Battery: ${device.battery_status || 'Unknown'}${batteryPercent}`;

          const blockStatus = document.createElement('span');
          blockStatus.className = 'device-seen device-block-status';
          blockStatus.dataset.deviceId = deviceId;
          blockStatus.textContent = hasBlock ? `Input block: ${blockedSeconds}s remaining` : 'Input unlocked';

          row.append(name, id, ip, localIp, version, state, uptime, seen, joined, localTime, user, battery, blockStatus);
          deviceListEl.appendChild(row);
        });
      } catch (err) {
        if (!lastDeviceSignature) deviceListEl.innerHTML = '<span class="device-seen">Unavailable</span>';
      }
    }

    async function loadHealth() {
      try {
        const health = await fetchJson('/health');
        serviceStartedAt = health.started_at;
        serviceUptime = health.uptime_seconds;
        startedAtEl.textContent = formatTime(serviceStartedAt);
        messageCountEl.textContent = health.count;
        updateUptime();
      } catch (err) {
        startedAtEl.textContent = 'Unavailable';
        uptimeEl.textContent = 'Unavailable';
      }
    }

    function appendHighlightedMentions(container, value) {
      const text = String(value || '');
      const mentionPattern = /(?:^|\s)(?:[A-Za-z0-9._'-]+\s+)?@[A-Za-z0-9._-]+/g;
      let cursor = 0;
      let match;
      while ((match = mentionPattern.exec(text)) !== null) {
        const highlightStart = match.index + (match[0].startsWith(' ') ? 1 : 0);
        if (highlightStart > cursor) {
          container.appendChild(document.createTextNode(text.slice(cursor, highlightStart)));
        }
        const mention = document.createElement('mark');
        mention.className = 'mention-highlight';
        mention.textContent = text.slice(highlightStart, match.index + match[0].length);
        container.appendChild(mention);
        cursor = match.index + match[0].length;
      }
      if (cursor < text.length) {
        container.appendChild(document.createTextNode(text.slice(cursor)));
      }
    }

    function addMessage(msg) {
      if (displayMode === 'filtered' && msg.raw_only) return;
      const wrap = document.createElement('div');
      wrap.className = 'bubble-wrap';

      const bubble = document.createElement('div');
      const bubbleType = msg.is_pasted ? 'pasted' : (msg.is_copied ? 'copied' : '');
      bubble.className = `bubble${bubbleType ? ` ${bubbleType}` : ''}`;
      appendHighlightedMentions(bubble, displayMode === 'raw' ? (msg.raw_text || msg.text) : msg.text);

      if (msg.is_pasted || msg.is_copied) {
        const label = document.createElement('span');
        label.className = 'paste-label';
        label.textContent = msg.is_copied ? 'Copied' : 'Pasted';
        bubble.prepend(label);
      }

      const time = document.createElement('span');
      time.className = 'time';
      time.textContent = formatTime(msg.time);
      bubble.appendChild(time);

      const device = document.createElement('span');
      device.className = 'device';
      device.textContent = `From device ${msg.device_id || 'unknown'}${msg.device_name ? ` (${msg.device_name})` : ''}`;
      bubble.appendChild(device);

      const source = document.createElement('span');
      source.className = 'source';
      source.textContent = `Entered in: ${msg.app_name || 'Unknown app'}`;
      bubble.appendChild(source);

      let safeSourceUrl = '';
      try {
        const parsedSourceUrl = new URL(msg.source_url, window.location.origin);
        if (parsedSourceUrl.protocol === 'http:' || parsedSourceUrl.protocol === 'https:') {
          safeSourceUrl = parsedSourceUrl.href;
        }
      } catch (error) {
        safeSourceUrl = '';
      }
      if (safeSourceUrl) {
        const sourceLinkRow = document.createElement('div');
        sourceLinkRow.className = 'source-link-row';
        const sourceLink = document.createElement('a');
        sourceLink.className = 'source-link';
        sourceLink.href = safeSourceUrl;
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener noreferrer';
        sourceLink.title = safeSourceUrl;
        sourceLink.textContent = safeSourceUrl;

        const copySourceButton = document.createElement('button');
        copySourceButton.className = 'copy-source';
        copySourceButton.type = 'button';
        copySourceButton.textContent = 'Copy link';
        copySourceButton.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(safeSourceUrl);
            copySourceButton.textContent = 'Copied';
            setTimeout(() => { copySourceButton.textContent = 'Copy link'; }, 1400);
          } catch (err) {
            copySourceButton.textContent = 'Select';
          }
        });

        sourceLinkRow.append(sourceLink, copySourceButton);
        bubble.appendChild(sourceLinkRow);
      }

      wrap.appendChild(bubble);
      return wrap;
    }

    function visibleMessages() {
      const search = messageSearchEl.value.trim().toLowerCase();
      const matchesSearch = (msg) => {
        if (!search) return true;
        return [msg.text, msg.raw_text, msg.device_name, msg.device_id, msg.app_name]
          .some((value) => String(value || '').toLowerCase().includes(search));
      };
      if (displayMode === 'raw') {
        const rawMessages = currentMessages.filter((msg) => msg.raw_only && matchesSearch(msg));
        return rawMessages;
      }
      return currentMessages.filter((msg) => !msg.raw_only && matchesSearch(msg));
    }

    function updateMessageCount() {
      messageCountEl.textContent = visibleMessages().length;
    }

    function queueFeedRender() {
      if (renderQueued) return;
      renderQueued = true;
      requestAnimationFrame(() => {
        renderQueued = false;
        renderFeed();
      });
    }

    function renderFeed() {
      feed.innerHTML = '';
      if (displayMode === 'raw-history') {
        const fragment = document.createDocumentFragment();
        rawHistory.forEach((batch) => {
          const section = document.createElement('section');
          section.className = 'raw-batch';
          const heading = document.createElement('header');
          heading.className = 'raw-batch-heading';
          heading.textContent = `${formatTime(batch.started_at)} - ${formatTime(batch.ended_at)} | ${batch.device_name} | ${batch.event_count} events`;
          const session = document.createElement('span');
          session.textContent = `Session ${batch.session_id}`;
          heading.appendChild(session);
          section.appendChild(heading);
          batch.events.forEach((event) => {
            const row = document.createElement('div');
            row.className = 'raw-event';
            const time = document.createElement('time');
            time.textContent = formatTime(event.time);
            const key = document.createElement('code');
            key.textContent = event.key;
            const app = document.createElement('span');
            app.textContent = event.app_name || 'Unknown app';
            row.append(time, key, app);
            section.appendChild(row);
          });
          fragment.appendChild(section);
        });
        feed.appendChild(fragment);
        messageCountEl.textContent = rawHistory.reduce((count, batch) => count + batch.event_count, 0);
        feed.scrollTop = 0;
        return;
      }
      if (displayMode === 'raw') {
        const rawLog = document.createElement('pre');
        rawLog.className = 'raw-log';
        rawLog.textContent = visibleMessages()
          .map((msg) => msg.raw_text || msg.text)
          .join('');
        feed.appendChild(rawLog);
        updateMessageCount();
        feed.scrollTop = feed.scrollHeight;
        return;
      }
      const fragment = document.createDocumentFragment();
      visibleMessages().forEach((msg) => fragment.appendChild(addMessage(msg)));
      feed.appendChild(fragment);
      updateMessageCount();
      feed.scrollTop = feed.scrollHeight;
    }

    async function loadInitialMessages() {
      try {
        const query = selectedDeviceId ? `?device_id=${encodeURIComponent(selectedDeviceId)}` : '';
        const messages = await fetchJson(`/messages${query}`);
        currentMessages = messages;
        renderFeed();
        statusEl.textContent = selectedDeviceId ? 'Device filtered keys: ' + visibleMessages().length : 'Latest filtered keys: ' + visibleMessages().length;
        return true;
      } catch (err) {
        statusEl.textContent = 'Listening for filtered keysâ€¦';
        return false;
      }
    }

    async function loadRawHistory() {
      const requestId = ++panelRequestId;
      showFeedLoader('Loading local saved events');
      const params = new URLSearchParams();
      const deviceId = rawDeviceFilterEl.value.trim() || selectedDeviceId;
      if (deviceId) params.set('device_id', deviceId);
      if (rawSessionFilterEl.value.trim()) params.set('session_id', rawSessionFilterEl.value.trim());
      if (rawStartFilterEl.value) params.set('start_time', String(new Date(rawStartFilterEl.value).getTime()));
      if (rawEndFilterEl.value) params.set('end_time', String(new Date(rawEndFilterEl.value).getTime()));
      params.set('limit', '100');
      try {
        rawHistory = await fetchJson(`/api/raw-history?${params}`);
        if (requestId !== panelRequestId) return;
        renderFeed();
        statusEl.textContent = `Local saved: ${rawHistory.length} batches`;
      } catch (err) {
        rawHistory = [];
        renderFeed();
        statusEl.textContent = 'Local saved events unavailable';
      }
    }

    async function loadScreenshots() {
      const requestId = ++panelRequestId;
      try {
        const query = selectedDeviceId ? `?device_id=${encodeURIComponent(selectedDeviceId)}` : '';
        const screenshots = await fetchJson(`/api/screenshots${query}`);
        if (requestId !== panelRequestId) return;
        const nextSignature = screenshots.map((item) => item.id).join(',');
        if (nextSignature === screenshotSignature) return;
        screenshotSignature = nextSignature;
        feed.innerHTML = '';
        if (!screenshots.length) {
          feed.innerHTML = '<span class="device-seen">No screenshots saved</span>';
        } else {
          const grid = document.createElement('div');
          grid.className = 'screenshot-grid';
          screenshots.forEach((item) => {
            const card = document.createElement('article');
            card.className = 'screenshot-card';
            const image = document.createElement('img');
            image.src = item.image_url;
            image.alt = `Screenshot from ${item.device_name}`;
            image.loading = 'lazy';
            image.addEventListener('load', () => image.classList.add('loaded'));
            image.addEventListener('error', () => {
              image.classList.add('loaded');
              image.alt = 'Screenshot unavailable - check Render logs and storage configuration';
            });
            image.addEventListener('click', () => window.open(item.image_url, '_blank', 'noopener'));
            const device = document.createElement('strong');
            device.textContent = `${item.device_name} (${item.device_id})`;
            const time = document.createElement('span');
            time.textContent = formatTime(item.captured_at);
            card.append(image, device, time);
            grid.appendChild(card);
          });
          feed.appendChild(grid);
        }
        messageCountEl.textContent = screenshots.length;
        statusEl.textContent = `Screenshots: ${screenshots.length}`;
      } catch (err) {
        feed.innerHTML = '<span class="device-seen">Screenshots unavailable</span>';
        statusEl.textContent = 'Screenshots unavailable';
      }
    }

    function showFeedLoader(label) {
      feed.innerHTML = '';
      const loader = document.createElement('div');
      loader.className = 'feed-loader';
      loader.textContent = label;
      feed.appendChild(loader);
    }

    function connectEvents() {
      const params = new URLSearchParams();
      if (selectedDeviceId) params.set('device_id', selectedDeviceId);
      const lastMessageId = currentMessages.reduce((latest, msg) => Math.max(latest, Number(msg.id) || 0), 0);
      if (lastMessageId) params.set('since', String(lastMessageId));
      const query = params.toString() ? `?${params.toString()}` : '';
      eventSource = new EventSource(`/events${query}`);
      eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);
        currentMessages.push(message);
        if (currentMessages.length > 200) currentMessages.shift();
        showLiveNotification(message);
        queueFeedRender();
        statusEl.textContent = 'Live stream connected';
      };
      eventSource.onerror = () => {
        statusEl.textContent = 'Reconnect in progressâ€¦';
      };
    }

    async function selectDevice(deviceId) {
      if (selectedDeviceId === deviceId) return;
      selectedDeviceId = deviceId;
      const query = selectedDeviceId ? `/?device=${encodeURIComponent(selectedDeviceId)}` : '/';
      window.history.pushState({}, '', query);
      panelRequestId += 1;
      currentMessages = [];
      screenshotSignature = null;
      scopeLabelEl.textContent = `Device ${selectedDeviceId}`;
      controlsDeviceEl.textContent = `Selected device: ${selectedDeviceId}`;
      updateSelectedDeviceScreenshot();
      syncUpdateButtonState();
      if (eventSource) eventSource.close();
      await loadInitialMessages();
      connectEvents();
      await loadDevices();
      if (displayMode === 'screenshots') await loadScreenshots();
      if (displayMode === 'activity') await loadActivity();
      if (displayMode === 'controls') await loadCommandHistory();
    }

    function updateViewVisibility() {
      const isControlsView = displayMode === 'controls';
      const isConstellationView = displayMode === 'constellation';
      const isFeedView = !isControlsView;
      rawHistoryControlsEl.hidden = displayMode !== 'raw-history';
      controlsPanelEl.hidden = !isControlsView;
      constellationPanelEl.hidden = !isConstellationView;
      activityPanelEl.hidden = true;
      feed.hidden = !isFeedView || isConstellationView;
      if (!isFeedView) {
        feed.innerHTML = '';
      }
    }

    document.querySelectorAll('[data-mode]').forEach((button) => {
      button.addEventListener('click', async () => {
        panelRequestId += 1;
        displayMode = button.dataset.mode;
        button.setAttribute('aria-busy', 'true');
        document.querySelectorAll('[data-mode]').forEach((item) => item.classList.toggle('active', item === button));
        updateViewVisibility();
        if (displayMode === 'raw-history') {
          if (eventSource) eventSource.close();
          await loadRawHistory();
        } else if (displayMode === 'screenshots') {
          if (eventSource) eventSource.close();
          await loadScreenshots();
        } else if (displayMode === 'controls') {
          if (eventSource) eventSource.close();
          statusEl.textContent = 'Device controls';
          await loadCommandHistory();
        } else if (displayMode === 'constellation') {
          if (eventSource) eventSource.close();
          statusEl.textContent = 'Device constellation';
          renderConstellation(latestDevices);
        } else if (displayMode === 'activity') {
          if (eventSource) eventSource.close();
          await loadActivity();
        } else {
          if (!eventSource || eventSource.readyState === EventSource.CLOSED) connectEvents();
          renderFeed();
        }
        button.removeAttribute('aria-busy');
      });
    });

    closeConstellationButtonEl.addEventListener('click', () => {
      const filteredButton = document.querySelector('[data-mode="filtered"]');
      if (filteredButton) filteredButton.click();
    });

    rawHistoryControlsEl.addEventListener('submit', (event) => {
      event.preventDefault();
      loadRawHistory();
    });

    async function requestClientCommand(command, button, confirmation) {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      if (!window.confirm(confirmation)) return;
      button.disabled = true;
      controlsStatusEl.textContent = `Requesting client ${command}...`;
      try {
        await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, { command });
        controlsStatusEl.textContent = `Client ${command} requested.`;
      } catch (err) {
        button.disabled = false;
        controlsStatusEl.textContent = `Client ${command} failed.`;
      }
    }

    function parseVersionParts(version) {
      const normalized = String(version || '').trim().replace(/^v/i, '').replace(/[^0-9.]+/g, '.');
      const parts = normalized.split('.').map((part) => Number.parseInt(part, 10) || 0);
      while (parts.length < 5) parts.push(0);
      return parts.slice(0, 5);
    }

    function compareVersions(currentVersion, latestVersion) {
      const currentParts = parseVersionParts(currentVersion);
      const latestParts = parseVersionParts(latestVersion);
      for (let index = 0; index < 5; index += 1) {
        if (currentParts[index] < latestParts[index]) return -1;
        if (currentParts[index] > latestParts[index]) return 1;
      }
      return 0;
    }

    async function getUpdateStatus(deviceId, force = false) {
      const cached = updateCheckCache.get(deviceId);
      const cacheAge = cached ? Date.now() - cached.checkedAt : Infinity;
      const cacheDuration = cached?.error ? UPDATE_CHECK_ERROR_CACHE_MS : UPDATE_CHECK_CACHE_MS;
      if (!force && cached && cacheAge < cacheDuration) {
        if (cached.error) throw new Error(cached.error);
        return cached.status;
      }
      if (!force && updateCheckInFlight.has(deviceId)) return updateCheckInFlight.get(deviceId);
      const checkPromise = (async () => {
        try {
          const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/update-check${force ? '?force=true' : ''}`);
          const status = await response.json().catch(() => ({}));
          if (!response.ok || !status.ok) {
            throw new Error(status.error || `Update check failed with HTTP ${response.status}.`);
          }
          updateCheckCache.set(deviceId, { checkedAt: Date.now(), status });
          return status;
        } catch (error) {
          updateCheckCache.set(deviceId, {
            checkedAt: Date.now(),
            error: error.message || 'Update check failed. Check the server connection and retry.'
          });
          throw error;
        } finally {
          updateCheckInFlight.delete(deviceId);
        }
      })();
      updateCheckInFlight.set(deviceId, checkPromise);
      return checkPromise;
    }

    function syncUpdateButtonState() {
      const requestId = ++updateButtonSyncRequestId;
      const selectedDevice = latestDevices.find((device) => String(device.id) === String(selectedDeviceId));
      if (!selectedDeviceId || !selectedDevice) {
        updateClientButtonEl.disabled = true;
        updateClientButtonEl.textContent = 'Update client';
        return;
      }
      const deviceId = String(selectedDevice.id);
      const currentVersion = String(selectedDevice.client_version || '').trim();
      if (!currentVersion || currentVersion === 'unknown') {
        updateClientButtonEl.disabled = true;
        updateClientButtonEl.textContent = 'Version unknown';
        return;
      }
      const pendingUpdate = pendingUpdateStates.get(deviceId);
      if (pendingUpdate) {
        if (pendingUpdate.latestVersion && compareVersions(currentVersion, pendingUpdate.latestVersion) >= 0) {
          pendingUpdateStates.delete(deviceId);
          updateCheckCache.delete(deviceId);
        } else {
          updateClientButtonEl.disabled = true;
          updateClientButtonEl.textContent = pendingUpdate.label;
          return;
        }
      }
      if (!selectedDevice.online) {
        updateClientButtonEl.disabled = true;
        updateClientButtonEl.textContent = 'Client offline';
        return;
      }
      const cached = updateCheckCache.get(deviceId);
      const cachedAge = cached ? Date.now() - cached.checkedAt : Infinity;
      const cachedDuration = cached?.error ? UPDATE_CHECK_ERROR_CACHE_MS : UPDATE_CHECK_CACHE_MS;
      if (!cached || cachedAge >= cachedDuration) {
        updateClientButtonEl.disabled = true;
        updateClientButtonEl.textContent = 'Checking updates...';
      }
      getUpdateStatus(deviceId)
        .then((updateStatus) => {
          if (requestId !== updateButtonSyncRequestId || deviceId !== String(selectedDeviceId)) return;
          updateClientButtonEl.title = '';
          const needsUpdate = Boolean(updateStatus.needs_update);
          updateClientButtonEl.disabled = !needsUpdate;
          updateClientButtonEl.textContent = needsUpdate ? 'Update client' : 'Latest version';
        })
        .catch((error) => {
          if (requestId !== updateButtonSyncRequestId || deviceId !== String(selectedDeviceId)) return;
          updateClientButtonEl.disabled = false;
          updateClientButtonEl.textContent = 'Retry update check';
          updateClientButtonEl.title = error.message || 'Update check failed. Select to retry.';
          controlsStatusEl.textContent = `Update check failed: ${error.message || 'check server connection and retry.'}`;
        });
    }

    function waitForDelay(milliseconds) {
      return new Promise((resolve) => setTimeout(resolve, milliseconds));
    }

    async function waitForUpdateCommand(deviceId, commandId, latestVersion) {
      const deadline = Date.now() + UPDATE_COMMAND_TIMEOUT_MS;
      while (Date.now() < deadline) {
        let commands;
        try {
          commands = await fetchJson(`/api/devices/${encodeURIComponent(deviceId)}/commands?limit=100`);
        } catch (error) {
          const label = 'Checking update status...';
          pendingUpdateStates.set(deviceId, { commandId, latestVersion, label });
          if (deviceId === String(selectedDeviceId)) updateClientButtonEl.textContent = label;
          await waitForDelay(1500);
          continue;
        }
        const command = commands.find((item) => String(item.command_id) === String(commandId));
        if (command?.status === 'completed') return true;
        if (command?.status === 'failed') {
          pendingUpdateStates.delete(deviceId);
          throw new Error(command.error || 'The client update failed.');
        }
        const label = command?.status === 'claimed' ? 'Downloading update...' : 'Waiting for client...';
        pendingUpdateStates.set(deviceId, { commandId, latestVersion, label });
        if (deviceId === String(selectedDeviceId)) updateClientButtonEl.textContent = label;
        await waitForDelay(1500);
      }
      return false;
    }

    async function waitForUpdatedVersion(deviceId, latestVersion) {
      const deadline = Date.now() + 60000;
      while (Date.now() < deadline) {
        try {
          const devices = await fetchJson('/api/devices');
          const device = devices.find((item) => String(item.id) === deviceId);
          if (device && compareVersions(device.client_version, latestVersion) >= 0) return true;
        } catch (err) {
          // Keep checking while the updated client restarts and reconnects.
        }
        await waitForDelay(1500);
      }
      return false;
    }

    async function requestClientUpdate(button) {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      const deviceId = String(selectedDeviceId);
      const selectedDevice = latestDevices.find((device) => String(device.id) === deviceId);
      if (!selectedDevice) {
        controlsStatusEl.textContent = 'Selected device is no longer available.';
        return;
      }
      if (!selectedDevice.online) {
        controlsStatusEl.textContent = 'The selected client is offline.';
        return;
      }
      const currentVersion = String(selectedDevice.client_version || '').trim();
      if (!currentVersion || currentVersion === 'unknown') {
        controlsStatusEl.textContent = 'The selected device version is unavailable, so no update comparison can be made.';
        return;
      }
      button.disabled = true;
      controlsStatusEl.textContent = `Checking latest release against client v${currentVersion}...`;
      try {
        const updateStatus = await getUpdateStatus(deviceId, true);
        if (!updateStatus.ok) {
          throw new Error(updateStatus.error || 'The update check failed.');
        }
        const latestVersion = String(updateStatus.latest_version || '').trim();
        const normalizedCurrent = currentVersion.replace(/^v/i, '');
        const normalizedLatest = latestVersion.replace(/^v/i, '');
        if (!updateStatus.needs_update) {
          controlsStatusEl.textContent = `Client is already up to date: v${normalizedCurrent} is current.`;
          updateClientButtonEl.disabled = true;
          updateClientButtonEl.textContent = 'Latest version';
          return;
        }
        const deviceLabel = selectedDevice.name || selectedDevice.id;
        if (!window.confirm(`Update ${deviceLabel} from v${normalizedCurrent} to v${normalizedLatest}?`)) {
          controlsStatusEl.textContent = 'Update cancelled.';
          return;
        }
        const queuedCommand = await postJson(`/api/devices/${encodeURIComponent(deviceId)}/command`, { command: 'update_client' });
        if (!queuedCommand.command_id) throw new Error('The server did not return an update command ID.');
        pendingUpdateStates.set(deviceId, {
          commandId: queuedCommand.command_id,
          latestVersion,
          label: 'Update queued',
        });
        controlsStatusEl.textContent = `Update queued for ${deviceLabel}: v${normalizedCurrent} -> v${normalizedLatest}. Waiting for the client...`;
        const commandCompleted = await waitForUpdateCommand(deviceId, queuedCommand.command_id, latestVersion);
        if (!commandCompleted) {
          pendingUpdateStates.set(deviceId, {
            commandId: queuedCommand.command_id,
            latestVersion,
            label: 'Update status unknown',
          });
          controlsStatusEl.textContent = 'No completion was received after four minutes. Check the client before retrying.';
          return;
        }
        pendingUpdateStates.set(deviceId, {
          commandId: queuedCommand.command_id,
          latestVersion,
          label: 'Waiting for version check-in...',
        });
        const versionConfirmed = await waitForUpdatedVersion(deviceId, latestVersion);
        if (versionConfirmed) {
          pendingUpdateStates.delete(deviceId);
          updateCheckCache.delete(deviceId);
          controlsStatusEl.textContent = `Client ${deviceLabel} is running v${normalizedLatest}.`;
        } else {
          controlsStatusEl.textContent = `The update started, but ${deviceLabel} has not reported v${normalizedLatest} yet.`;
        }
      } catch (err) {
        controlsStatusEl.textContent = `Could not check for client updates: ${err.message || String(err)}`;
      } finally {
        if (selectedDeviceId === deviceId) syncUpdateButtonState();
      }
    }

    async function requestAllClientsUpdate(button) {
      const eligibleDevices = latestDevices.filter((device) => (
        device.online
        && device.client_version
        && String(device.client_version).toLowerCase() !== 'unknown'
      ));
      if (!eligibleDevices.length) {
        controlsStatusEl.textContent = 'No online clients with a known version are available.';
        return;
      }
      button.disabled = true;
      controlsStatusEl.textContent = `Checking ${eligibleDevices.length} client(s) for updates...`;
      try {
        const checkedDevices = await Promise.all(eligibleDevices.map(async (device) => {
          try {
            const status = await getUpdateStatus(String(device.id), true);
            return status.needs_update ? { device, status } : null;
          } catch (error) {
            return { device, error };
          }
        }));
        const failedChecks = checkedDevices.filter((item) => item?.error);
        const updates = checkedDevices.filter((item) => item && !item.error);
        if (!updates.length) {
          controlsStatusEl.textContent = failedChecks.length
            ? `No updates queued. ${failedChecks.length} update check(s) failed.`
            : 'All online clients are already up to date.';
          return;
        }
        if (!window.confirm(`Queue updates for ${updates.length} client(s)?`)) {
          controlsStatusEl.textContent = 'Update all cancelled.';
          return;
        }
        const queueResults = await Promise.all(updates.map(async ({ device, status }) => {
          try {
            const response = await postJson(`/api/devices/${encodeURIComponent(device.id)}/command`, {
              command: 'update_client',
            });
            if (!response.command_id) throw new Error('No command ID returned.');
            pendingUpdateStates.set(String(device.id), {
              commandId: response.command_id,
              latestVersion: status.latest_version,
              label: 'Update queued',
            });
            return true;
          } catch (error) {
            return false;
          }
        }));
        const queuedCount = queueResults.filter(Boolean).length;
        controlsStatusEl.textContent = `Queued updates for ${queuedCount} of ${updates.length} client(s).${failedChecks.length ? ` ${failedChecks.length} check(s) failed.` : ''}`;
        syncUpdateButtonState();
      } finally {
        button.disabled = false;
      }
    }

    shutdownButtonEl.addEventListener('click', () => requestClientCommand(
      'shutdown', shutdownButtonEl, 'Shut down the selected client computer?'
    ));
    logoutClientButtonEl.addEventListener('click', () => requestClientCommand(
      'logout', logoutClientButtonEl, 'Log out the selected Windows user?'
    ));
    restartClientButtonEl.addEventListener('click', () => requestClientCommand(
      'restart', restartClientButtonEl, 'Restart the selected client computer?'
    ));
    lockClientButtonEl.addEventListener('click', () => requestClientCommand(
      'lock', lockClientButtonEl, 'Lock the selected client computer?'
    ));
    blockInputButtonEl.addEventListener('click', async () => {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      const rawSeconds = window.prompt('Block input for how many seconds?', '20');
      if (rawSeconds === null) return;
      const seconds = Number.parseInt(rawSeconds, 10);
      if (!Number.isInteger(seconds) || seconds < 1 || seconds > 3600) {
        controlsStatusEl.textContent = 'Enter a duration from 1 to 3600 seconds.';
        return;
      }
      blockInputButtonEl.disabled = true;
      controlsStatusEl.textContent = `Blocking input for ${seconds} seconds...`;
      try {
        const response = await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
          command: 'block_input',
          message: String(seconds),
        });
        if (!response.ok) throw new Error('The server rejected the block-input command.');
        controlsStatusEl.textContent = `Input blocked on the client for ${seconds} seconds.`;
      } catch (err) {
        controlsStatusEl.textContent = 'Could not block client input.';
      } finally {
        blockInputButtonEl.disabled = false;
      }
    });
    pauseClientButtonEl.addEventListener('click', () => requestClientCommand(
      'pause', pauseClientButtonEl, 'Pause collection on the selected client?'
    ));
    resumeClientButtonEl.addEventListener('click', () => requestClientCommand(
      'resume', resumeClientButtonEl, 'Resume collection on the selected client?'
    ));
    updateClientButtonEl.addEventListener('click', () => requestClientUpdate(updateClientButtonEl));
    updateAllClientsButtonEl.addEventListener('click', () => requestAllClientsUpdate(updateAllClientsButtonEl));

    function openCameraDialog() {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      cameraDialogTargetEl.textContent = `Applying to ${controlsDeviceEl.textContent}`;
      cameraDialogEl.showModal();
      cameraDurationEl.focus();
      cameraDurationEl.select();
    }

    function closeCameraDialog() {
      if (cameraDialogEl.open) cameraDialogEl.close();
    }

    disableCameraButtonEl.addEventListener('click', openCameraDialog);
    closeCameraButtonEl.addEventListener('click', closeCameraDialog);
    cancelCameraButtonEl.addEventListener('click', closeCameraDialog);
    openUltraViewerButtonEl.addEventListener('click', () => {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      remoteAppDialogTargetEl.textContent = `Applying to ${controlsDeviceEl.textContent}`;
      remoteAppDialogEl.showModal();
      remoteAppSelectEl.focus();
    });
    const closeRemoteAppDialog = () => {
      if (remoteAppDialogEl.open) remoteAppDialogEl.close();
    };
    closeRemoteAppButtonEl.addEventListener('click', closeRemoteAppDialog);
    cancelRemoteAppButtonEl.addEventListener('click', closeRemoteAppDialog);
    remoteAppFormEl.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!selectedDeviceId) {
        closeRemoteAppDialog();
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      const appName = remoteAppSelectEl.value;
      confirmRemoteAppButtonEl.disabled = true;
      controlsStatusEl.textContent = `Opening ${appName}...`;
      try {
        await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
          command: 'open_remote_app',
          message: appName,
        });
        closeRemoteAppDialog();
        controlsStatusEl.textContent = `${appName} launch requested.`;
      } catch (err) {
        controlsStatusEl.textContent = `${appName} could not be opened.`;
      } finally {
        confirmRemoteAppButtonEl.disabled = false;
      }
    });

    cameraFormEl.addEventListener('submit', async (event) => {
      event.preventDefault();
      const seconds = Number.parseInt(cameraDurationEl.value, 10);
      if (!selectedDeviceId) {
        closeCameraDialog();
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      if (!Number.isInteger(seconds) || seconds < 1 || seconds > 3600) {
        controlsStatusEl.textContent = 'Enter a duration from 1 to 3600 seconds.';
        cameraDurationEl.focus();
        return;
      }
      confirmCameraButtonEl.disabled = true;
      controlsStatusEl.textContent = `Opening camera for ${seconds} seconds...`;
      try {
        await postJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/command`, {
          command: 'open_camera',
          message: String(seconds),
        });
        closeCameraDialog();
        controlsStatusEl.textContent = `Camera opened for ${seconds} seconds.`;
      } catch (err) {
        controlsStatusEl.textContent = 'Camera could not be opened.';
      } finally {
        confirmCameraButtonEl.disabled = false;
      }
    });

    function openScreenshotDialog() {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      screenshotDialogTargetEl.textContent = `Previewing ${controlsDeviceEl.textContent}`;
      const selectedDevice = latestDevices.find((device) => String(device.id) === String(selectedDeviceId));
      if (selectedDevice) {
        screenshotSavedCaptureByDevice.delete(String(selectedDevice.id));
        screenshotCaptureBaseline = {
          deviceId: String(selectedDevice.id),
          capturedAt: Number(selectedDevice.screenshot_captured_at) || 0,
        };
        screenshotRequestError = '';
        displayedScreenshotUrl = '';
        syncScreenshotPreviewState(selectedDevice, 'Requested', 'Requesting a fresh screenshot...');
      }
      if (typeof screenshotDialogEl.showModal === 'function') {
        try {
          screenshotDialogEl.showModal();
        } catch (err) {
          screenshotOverlayEl.hidden = false;
          screenshotOverlayEl.classList.add('show');
        }
      } else {
        screenshotOverlayEl.hidden = false;
        screenshotOverlayEl.classList.add('show');
      }
      if (screenshotOverlayEl && screenshotOverlayEl.hidden === false) {
        screenshotOverlayEl.classList.add('show');
      }
      if (screenshotStatusTimer) clearInterval(screenshotStatusTimer);
      const screenshotPollStartedAt = Date.now();
      screenshotStatusTimer = setInterval(async () => {
        if (Date.now() - screenshotPollStartedAt >= SCREENSHOT_POLL_TIMEOUT_MS) {
          clearInterval(screenshotStatusTimer);
          screenshotStatusTimer = null;
          screenshotDialogStatusEl.textContent = 'Screenshot request timed out. The last saved screenshot remains available.';
          screenshotDialogStatusEl.className = 'controls-screenshot-status failed';
          updateScreenshotProgress(screenshotDialogProgressEl, 'Failed');
          const timedOutDevice = latestDevices.find((device) => String(device.id) === String(selectedDeviceId));
          captureScreenshotButtonEl.disabled = !timedOutDevice?.online;
          return;
        }
        if (!screenshotOverlayEl.hidden && !selectedDeviceId) {
          clearInterval(screenshotStatusTimer);
          screenshotStatusTimer = null;
          return;
        }
        await loadDevices();
        const currentDevice = latestDevices.find((device) => String(device.id) === String(selectedDeviceId));
        if (!currentDevice) {
          clearInterval(screenshotStatusTimer);
          screenshotStatusTimer = null;
          return;
        }
        const status = currentDevice.screenshot_status || 'Ready';
        if (!['Requested', 'Taking screenshot', 'Capturing', 'Uploading'].includes(status)) {
          clearInterval(screenshotStatusTimer);
          screenshotStatusTimer = null;
        }
        syncScreenshotPreviewState(currentDevice, status, currentDevice.screenshot_message || 'Ready to capture');
      }, SCREENSHOT_POLL_INTERVAL_MS);
    }

    function closeScreenshotDialog() {
      if (screenshotStatusTimer) {
        clearInterval(screenshotStatusTimer);
        screenshotStatusTimer = null;
      }
      if (typeof screenshotDialogEl.close === 'function' && screenshotDialogEl.open) {
        screenshotDialogEl.close();
      }
      if (screenshotOverlayEl) {
        screenshotOverlayEl.classList.remove('show');
        screenshotOverlayEl.hidden = true;
      }
    }

    captureScreenshotButtonEl.addEventListener('click', async () => {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      const requestDeviceId = String(selectedDeviceId);
      openScreenshotDialog();
      captureScreenshotButtonEl.disabled = true;
      screenshotDialogStatusEl.textContent = 'Requesting screenshot...';
      screenshotDialogStatusEl.className = 'controls-screenshot-status requested';
      try {
        const response = await fetch(`/api/devices/${encodeURIComponent(selectedDeviceId)}/screenshot`, { method: 'POST' });
        if (!response.ok) throw new Error('request failed');
        controlsStatusEl.textContent = 'Screenshot queued for the selected client.';
        screenshotDialogStatusEl.textContent = 'Screenshot queued. Waiting for the client...';
        screenshotDialogStatusEl.className = 'controls-screenshot-status requested';
        await loadDevices();
      } catch (err) {
        controlsStatusEl.textContent = 'Screenshot request failed.';
        screenshotRequestError = `Screenshot request failed: ${err.message || 'check the server and retry.'}`;
        const currentDevice = latestDevices.find((device) => String(device.id) === requestDeviceId);
        if (currentDevice) syncScreenshotPreviewState(currentDevice, 'Failed', screenshotRequestError);
      }
    });

    logoutDashboardButtonEl.addEventListener('click', () => {
      window.location.assign('/logout');
    });

    closeScreenshotButtonEl.addEventListener('click', closeScreenshotDialog);
    cancelScreenshotButtonEl.addEventListener('click', closeScreenshotDialog);
    confirmScreenshotButtonEl.addEventListener('click', async () => {
      captureScreenshotButtonEl.click();
    });

    function openMessageDialog() {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      messageDialogTargetEl.textContent = `Sending to ${controlsDeviceEl.textContent}`;
      messageDialogEl.showModal();
      clientMessageEl.focus();
    }

    function closeMessageDialog() {
      if (messageDialogEl.open) messageDialogEl.close();
    }

    openMessageButtonEl.addEventListener('click', openMessageDialog);
    sendDocumentButtonEl.addEventListener('click', () => {
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      clientDocumentEl.value = '';
      clientDocumentEl.click();
    });
    clientDocumentEl.addEventListener('change', async () => {
      const documentFile = clientDocumentEl.files[0];
      const targetDeviceId = selectedDeviceId;
      if (!documentFile) return;
      if (!targetDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      const extension = documentFile.name.toLowerCase().match(/\.[^.]+$/)?.[0];
      if (!['.pdf', '.docx', '.rtf', '.txt'].includes(extension)) {
        controlsStatusEl.textContent = 'Choose a PDF, DOCX, RTF, or TXT file.';
        clientDocumentEl.value = '';
        return;
      }
      if (documentFile.size > 20 * 1024 * 1024) {
        controlsStatusEl.textContent = 'Choose a document smaller than 20 MB.';
        clientDocumentEl.value = '';
        return;
      }
      sendDocumentButtonEl.disabled = true;
      controlsStatusEl.textContent = 'Uploading document...';
      try {
        const formData = new FormData();
        formData.append('file', documentFile);
        const uploadResponse = await fetch('/api/devices/document-upload', { method: 'POST', body: formData });
        if (!uploadResponse.ok) throw new Error(`Document upload failed: ${uploadResponse.status}`);
        const uploadedDocument = await uploadResponse.json();
        controlsStatusEl.textContent = 'Queueing document for the client...';
        await postJson(`/api/devices/${encodeURIComponent(targetDeviceId)}/command`, {
          command: 'open_document',
          message: JSON.stringify({ attachment_id: uploadedDocument.attachment_id })
        });
        controlsStatusEl.textContent = `Document queued for ${controlsDeviceEl.textContent}.`;
      } catch (err) {
        controlsStatusEl.textContent = 'Document could not be sent.';
      } finally {
        clientDocumentEl.value = '';
        sendDocumentButtonEl.disabled = false;
      }
    });
    closeMessageButtonEl.addEventListener('click', closeMessageDialog);
    cancelMessageButtonEl.addEventListener('click', closeMessageDialog);
    clientMessageEl.addEventListener('input', () => {
      messageLengthEl.textContent = `${clientMessageEl.value.length} / 2000`;
    });
    clientImageEl.addEventListener('change', () => {
      clientImageNameEl.textContent = clientImageEl.files[0]?.name || 'No image selected';
    });

    messageComposeEl.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = clientMessageEl.value.trim();
      const imageFile = clientImageEl.files[0];
      const targetDeviceId = selectedDeviceId;
      if (!selectedDeviceId) {
        controlsStatusEl.textContent = 'Select a device first.';
        return;
      }
      if (!message && !imageFile) {
        controlsStatusEl.textContent = 'Write a message or choose an image first.';
        if (!message) clientMessageEl.focus();
        return;
      }
      if (imageFile && imageFile.size > 10 * 1024 * 1024) {
        controlsStatusEl.textContent = 'Choose an image smaller than 10 MB.';
        return;
      }
      sendMessageButtonEl.disabled = true;
      controlsStatusEl.textContent = imageFile ? 'Uploading image...' : 'Sending message...';
      try {
        if (imageFile) {
          const formData = new FormData();
          formData.append('file', imageFile);
          const uploadResponse = await fetch('/api/devices/media-upload', { method: 'POST', body: formData });
          if (!uploadResponse.ok) throw new Error(`Image upload failed: ${uploadResponse.status}`);
          const uploadedImage = await uploadResponse.json();
          controlsStatusEl.textContent = 'Queueing image for the client...';
          await postJson(`/api/devices/${encodeURIComponent(targetDeviceId)}/command`, {
            command: 'show_image',
            message: JSON.stringify({ attachment_id: uploadedImage.attachment_id, caption: message })
          });
        } else {
          await postJson(`/api/devices/${encodeURIComponent(targetDeviceId)}/command`, { command: 'message', message });
        }
        clientMessageEl.value = '';
        clientImageEl.value = '';
        clientImageNameEl.textContent = 'No image selected';
        messageLengthEl.textContent = '0 / 2000';
        closeMessageDialog();
        controlsStatusEl.textContent = imageFile ? 'Image queued for the selected client.' : 'Message queued for the selected client.';
      } catch (err) {
        controlsStatusEl.textContent = imageFile ? 'Image could not be sent.' : 'Message could not be sent.';
      } finally {
        sendMessageButtonEl.disabled = false;
      }
    });

    refreshButtonEl.addEventListener('click', () => window.location.reload());

    async function loadCommandHistory() {
      commandHistoryEl.innerHTML = '';
      if (!selectedDeviceId) {
        commandHistoryEl.textContent = 'Select a device to view command history.';
        return;
      }
      try {
        const commands = await fetchJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/commands`);
        if (!commands.length) {
          commandHistoryEl.textContent = 'No commands recorded yet.';
          return;
        }
        commands.forEach((command) => {
          const item = document.createElement('div');
          item.className = 'command-history-item';
          const errorText = command.error ? ` | ${command.error}` : '';
          item.textContent = `${command.command} | ${command.status} | ${formatTime(command.created_at)}${errorText}`;
          commandHistoryEl.appendChild(item);
        });
      } catch (err) {
        commandHistoryEl.textContent = 'Command history unavailable.';
      }
    }

    activityButtonEl.addEventListener('click', async () => {
      if (activityDialogEl.open) {
        activityDialogEl.close();
        return;
      }
      activityPanelEl.hidden = true;
      if (typeof activityDialogEl.showModal === 'function') {
        activityDialogEl.showModal();
      }
      await loadActivity();
    });

    closeActivityButtonEl.addEventListener('click', () => {
      if (typeof activityDialogEl.close === 'function') {
        activityDialogEl.close();
      }
    });

    closeActivityDialogButtonEl.addEventListener('click', () => {
      if (typeof activityDialogEl.close === 'function') {
        activityDialogEl.close();
      }
    });

    async function loadActivity() {
      const query = selectedDeviceId ? `?device_id=${encodeURIComponent(selectedDeviceId)}` : '';
      try {
        const activity = await fetchJson(`/api/activity${query}`);
        const renderActivitySummary = (container) => {
          container.innerHTML = '';
          [[activity.messages || 0, 'Messages'], [activity.website_visits || 0, 'Website visits'], [activity.raw_events || 0, 'Raw events']].forEach(([value, label]) => {
            const stat = document.createElement('div');
            stat.className = 'activity-stat';
            stat.textContent = `${value} ${label}`;
            container.appendChild(stat);
          });
        };
        renderActivitySummary(activityStatsEl);
        renderActivitySummary(activityDialogStatsEl);
        const renderList = (container, values) => {
          container.innerHTML = '';
          values.forEach(([name, count]) => {
            const item = document.createElement('li');
            item.textContent = `${name}: ${count}`;
            container.appendChild(item);
          });
          if (!values.length) container.innerHTML = '<li>No data yet</li>';
        };
        renderList(topAppsEl, Array.isArray(activity.top_apps) ? activity.top_apps : []);
        renderList(topDomainsEl, Array.isArray(activity.top_domains) ? activity.top_domains : []);
        renderList(topAppsDialogEl, Array.isArray(activity.top_apps) ? activity.top_apps : []);
        renderList(topDomainsDialogEl, Array.isArray(activity.top_domains) ? activity.top_domains : []);
        const suffix = selectedDeviceId ? `?device_id=${encodeURIComponent(selectedDeviceId)}` : '';
        const csvHref = `/api/export/messages${suffix}`;
        const jsonHref = `/api/export/messages?format=json${selectedDeviceId ? `&device_id=${encodeURIComponent(selectedDeviceId)}` : ''}`;
        exportCsvLinkEl.href = csvHref;
        exportJsonLinkEl.href = jsonHref;
        exportCsvLinkDialogEl.href = csvHref;
        exportJsonLinkDialogEl.href = jsonHref;
        await loadDeviceDetail();
        statusEl.textContent = 'Activity summary loaded';
      } catch (err) {
        statusEl.textContent = 'Activity unavailable';
      }
    }

    async function loadDeviceDetail() {
      let updateLabel = 'Update status unavailable';
      const fillContainer = (container, payload) => {
        container.innerHTML = '';
        if (!selectedDeviceId) {
          container.textContent = 'Select a device to view detailed telemetry.';
          return;
        }
        if (!payload) {
          container.textContent = 'Device detail unavailable.';
          return;
        }
        const device = payload.device;
        const heading = document.createElement('h3');
        heading.textContent = `${device.name || 'Unknown device'} (${device.id})`;
        const summary = document.createElement('p');
        summary.textContent = `${device.online ? 'Online' : 'Offline'} | Client v${device.client_version || 'unknown'} | ${device.logged_in_user || 'Unknown user'} | ${device.battery_status || 'Battery unknown'}${device.battery_percent == null ? '' : ` ${device.battery_percent}%`}`;
        const blockStatus = device.input_block_status === 'Blocked'
          ? ` | Input blocked: ${Math.max(0, Number(device.input_block_remaining_seconds) || 0)}s remaining`
          : ' | Input unlocked';
        const health = document.createElement('p');
        health.textContent = `Update: ${updateLabel} | Screenshot: ${device.screenshot_status || 'Ready'}${device.screenshot_message ? ` (${device.screenshot_message})` : ''}${blockStatus}`;
        const network = document.createElement('p');
        network.textContent = `Public IP: ${device.client_ip || 'Unknown'} | Local IP: ${device.local_ip || 'Unknown'}`;
        const apps = document.createElement('p');
        apps.textContent = `Open applications: ${(device.open_apps || []).join(', ') || 'None reported'}`;
        const commands = document.createElement('p');
        commands.textContent = `Recent commands: ${(payload.commands || []).map((item) => `${item.command} (${item.status})`).join(', ') || 'None'}`;
        container.append(heading, summary, health, network, apps, commands);
      };

      if (!selectedDeviceId) {
        fillContainer(deviceDetailEl, null);
        fillContainer(deviceDetailDialogEl, null);
        return;
      }

      try {
        const [detail, updateStatus] = await Promise.all([
          fetchJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/detail`),
          fetchJson(`/api/devices/${encodeURIComponent(selectedDeviceId)}/update-check`).catch(() => null),
        ]);
        updateLabel = updateStatus?.ok
          ? (updateStatus.needs_update ? `Update available (${updateStatus.latest_version || 'new version'})` : 'Up to date')
          : 'Update status unavailable';
        fillContainer(deviceDetailEl, detail);
        fillContainer(deviceDetailDialogEl, detail);
      } catch (err) {
        fillContainer(deviceDetailEl, null);
        fillContainer(deviceDetailDialogEl, null);
      }
    }

    messageSearchEl.addEventListener('input', queueFeedRender);
    window.addEventListener('keydown', (event) => {
      if (event.key === '/' && document.activeElement !== messageSearchEl) {
        event.preventDefault();
        messageSearchEl.focus();
      }
    });

    scopeLabelEl.textContent = selectedDeviceId ? `Device ${selectedDeviceId}` : 'All devices';
    controlsDeviceEl.textContent = selectedDeviceId
      ? `Selected device: ${selectedDeviceId}`
      : 'Select a device from the device list to enable client actions.';
    updateSelectedDeviceScreenshot();
    async function startApp() {
      await loadInitialMessages();
      connectEvents();
      loadConfig();
      loadHealth();
      loadDevices();
    }

    startApp();
    setInterval(updateUptime, 1000);
    setInterval(updateDeviceUptimes, 1000);
    setInterval(loadHealth, HEALTH_POLL_INTERVAL_MS);
    setInterval(loadDevices, DEVICE_POLL_INTERVAL_MS);
    setInterval(() => {
      if (displayMode === 'screenshots') loadScreenshots();
    }, 15000);

