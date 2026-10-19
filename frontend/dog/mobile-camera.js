const params = new URLSearchParams(window.location.search);

const sessionId = params.get("session");
const sessionToken = params.get("token");

const videoPreview = document.getElementById("camera-preview");

const permissionScreen =
    document.getElementById("permission-screen");

const enableCameraBtn =
    document.getElementById("enable-camera-btn");

const startRecordingBtn =
    document.getElementById("start-recording-btn");

const submitBtn =
    document.getElementById("submit-btn");

const connectionText =
    document.getElementById("connection-text");

const statusDot =
    document.getElementById("status-dot");

const cameraMessage =
    document.getElementById("camera-message");


let cameraStream = null;
let mediaRecorder = null;
let recordedChunks = [];

let peerConnection = null;

const rtcConfiguration = {
    iceServers: [
        {
            urls: "stun:stun.l.google.com:19302"
        }
    ]
};


// ----------------------------------------
// Validate mobile session
// ----------------------------------------

if (!sessionId || !sessionToken) {

    cameraMessage.textContent =
        "Invalid or missing PawAI camera session.";

    enableCameraBtn.disabled = true;

    connectionText.textContent =
        "Invalid session";

} else {

    connectionText.textContent =
        "Session ready";

    statusDot.classList.add("connected");
}


// ----------------------------------------
// Request mobile camera
// ----------------------------------------

async function enableCamera() {

    try {

        cameraMessage.textContent =
            "Requesting camera permission...";

            if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
                cameraMessage.textContent =
                    "Camera access requires HTTPS. Please open the PawAI link from the QR code.";
                connectionText.textContent = "HTTPS required";
                enableCameraBtn.disabled = true;
                return;
            }
        cameraStream =
            await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: {
                        ideal: "environment"
                    },
                    width: {
                        ideal: 1920
                    },
                    height: {
                        ideal: 1080
                    }
                },
                audio: true
            });


        videoPreview.srcObject = cameraStream;
        connectMobileWebSocket();

        await videoPreview.play();


        permissionScreen.classList.add("hidden");

        startRecordingBtn.disabled = false;

        cameraMessage.textContent =
            "Rear camera ready. You can start recording.";

        connectionText.textContent =
            "Camera ready";

        statusDot.classList.add("connected");

    } catch (error) {

        console.error(
            "Camera permission error:",
            error
        );

        cameraMessage.textContent =
            "Camera access failed. Please allow camera and microphone permission.";

    }

}


// ----------------------------------------
// Start recording
// ----------------------------------------

function startRecording() {

    if (!cameraStream) {
        return;
    }


    recordedChunks = [];


    let mimeType = "";

    const supportedTypes = [
        "video/webm;codecs=vp9,opus",
        "video/webm;codecs=vp8,opus",
        "video/webm"
    ];


    for (const type of supportedTypes) {

        if (MediaRecorder.isTypeSupported(type)) {

            mimeType = type;
            break;

        }

    }


    mediaRecorder = mimeType
        ? new MediaRecorder(
            cameraStream,
            { mimeType }
        )
        : new MediaRecorder(cameraStream);


    mediaRecorder.ondataavailable = (event) => {

        if (event.data.size > 0) {

            recordedChunks.push(
                event.data
            );

        }

    };


    mediaRecorder.onstart = () => {

        startRecordingBtn.disabled = false;

        submitBtn.disabled = true;

        startRecordingBtn.textContent =
            "Stop Recording";

        connectionText.textContent =
            "Recording";

        statusDot.classList.add(
            "recording"
        );

        cameraMessage.textContent =
            "Recording your pet...";

            if (
                mobileSocket &&
                mobileSocket.readyState === WebSocket.OPEN
            ) {
                mobileSocket.send(
                    JSON.stringify({
                        type: "recording_started",
                        session_id: sessionId
                    })
                );
            }
    };


    mediaRecorder.onstop = () => {

        startRecordingBtn.textContent =
            "Recording Complete";

        submitBtn.disabled = false;

        connectionText.textContent =
            "Recording complete";

        statusDot.classList.remove(
            "recording"
        );

        cameraMessage.textContent =
            "Recording complete. Press Submit.";
        
        if (
            mobileSocket &&
            mobileSocket.readyState === WebSocket.OPEN
        ) {
            mobileSocket.send(
                JSON.stringify({
                    type: "recording_stopped",
                    session_id: sessionId
                })
            );
        }
    };


    mediaRecorder.start(250);

}


// ----------------------------------------
// Stop recording
// ----------------------------------------

function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();

    }

}


// ----------------------------------------
// Button behavior
// ----------------------------------------

enableCameraBtn.addEventListener(
    "click",
    enableCamera
);


startRecordingBtn.addEventListener(
    "click",
    () => {

        if (
            mediaRecorder &&
            mediaRecorder.state === "recording"
        ) {

            stopRecording();

        } else {

            startRecording();

        }

    }
);

submitBtn.addEventListener(
    "click",
    async () => {

        if (!sessionId || !sessionToken) {
            cameraMessage.textContent =
                "Invalid mobile camera session.";
            return;
        }

        submitBtn.disabled = true;

        cameraMessage.textContent =
            "Submitting your recording...";

        connectionText.textContent =
            "Submitting";

        try {

            const protocol =
                window.location.protocol === "https:"
                    ? "https:"
                    : "http:";

            const apiBase =
                `${protocol}//${window.location.hostname}:8000`;

            const response = await fetch(
                `${apiBase}/api/mobile/session/${encodeURIComponent(sessionId)}/submit` +
                `?token=${encodeURIComponent(sessionToken)}`,
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Submission failed."
                );
            }

            cameraMessage.textContent =
                "Submission successful. You can leave this site for now.";

            connectionText.textContent =
                "Submitted";

            statusDot.classList.remove("recording");
            statusDot.classList.add("connected");

            if (cameraStream) {
                cameraStream.getTracks().forEach(
                    track => track.stop()
                );

                cameraStream = null;
            }

            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }

        } catch (error) {

            console.error(
                "Recording submission failed:",
                error
            );

            submitBtn.disabled = false;

            cameraMessage.textContent =
                "Could not submit the recording. Please try again.";

            connectionText.textContent =
                "Submission failed";
        }
    }
);

// ========================================
// PAWAI MOBILE WEBSOCKET CONNECTION
// ========================================

let mobileSocket = null;


function getWebSocketBaseUrl() {

    const protocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const host =
        window.location.hostname;

    const port = "8000";

    return `${protocol}//${host}:${port}`;
}


function connectMobileWebSocket() {

    if (!sessionId || !sessionToken) {

        console.error(
            "Missing PawAI mobile session."
        );

        return;
    }


    const wsBase =
        getWebSocketBaseUrl();


    const wsUrl =
        `${wsBase}/api/mobile/ws/${encodeURIComponent(sessionId)}` +
        `?role=mobile&token=${encodeURIComponent(sessionToken)}`;


    console.log(
        "Connecting to PawAI WebSocket:",
        wsUrl
    );


    mobileSocket =
        new WebSocket(wsUrl);


    mobileSocket.onopen = () => {

        console.log(
            "PawAI mobile WebSocket connected."
        );

        connectionText.textContent =
            "Connected to PawAI";

        statusDot.classList.add(
            "connected"
        );

        cameraMessage.textContent =
            "Phone connected. Waiting for laptop...";
    };


    mobileSocket.onmessage = async (event) => {

        const message =
            JSON.parse(event.data);

        console.log(
            "WebSocket message:",
            message
        );


        if (message.type === "connected") {

            cameraMessage.textContent =
                "Mobile connected. Waiting for laptop.";

        }


        if (message.type === "peer_connected") {

            cameraMessage.textContent =
                "Laptop connected. Starting live camera...";

            createMobilePeerConnection()
                .catch((error) => {

                    console.error(
                        "WebRTC initialization failed:",
                        error
                    );

                    cameraMessage.textContent =
                        "Could not start live camera.";

                });

        }

        if (message.type === "answer") {

            if (!peerConnection) {

                console.warn(
                    "Received WebRTC answer before peer connection existed."
                );

                return;

            }


            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(
                    message.sdp
                )
            );


            console.log(
                "Laptop WebRTC answer received."
            );

        }

        if (message.type === "ice_candidate") {

            if (!peerConnection) {

                console.warn(
                    "Received ICE candidate before peer connection existed."
                );

                return;

            }


            try {

                await peerConnection.addIceCandidate(
                    new RTCIceCandidate(
                        message.candidate
                    )
                );

            } catch (error) {

                console.error(
                    "Failed to add remote ICE candidate:",
                    error
                );

            }

        }

        if (message.type === "submission_complete") {

            cameraMessage.textContent =
                "Submission complete. You can close this page.";

            connectionText.textContent =
                "Completed";

            statusDot.classList.remove("recording");

            startRecordingBtn.disabled = true;
            submitBtn.disabled = true;

            if (cameraStream) {

                cameraStream.getTracks().forEach(
                    track => track.stop()
                );

                cameraStream = null;
            }

            if (videoPreview) {
                videoPreview.srcObject = null;
            }
        }

        if (message.type === "error") {

            cameraMessage.textContent =
                message.message;

        }

    };


    mobileSocket.onerror = (error) => {

        console.error(
            "Mobile WebSocket error:",
            error
        );

        connectionText.textContent =
            "Connection error";

    };


    mobileSocket.onclose = () => {

        console.log(
            "PawAI mobile WebSocket disconnected."
        );

        connectionText.textContent =
            "Disconnected";

        statusDot.classList.remove(
            "connected"
        );

    };

}

// ========================================
// PAWAI MOBILE WEBRTC
// ========================================

async function createMobilePeerConnection() {

    console.log(
        "Creating mobile WebRTC peer connection..."
    );

    peerConnection =
        new RTCPeerConnection(
            rtcConfiguration
        );


    // ----------------------------------------
    // Add mobile camera + microphone tracks
    // ----------------------------------------

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach((track) => {

                peerConnection.addTrack(
                    track,
                    cameraStream
                );

            });

    }


    // ----------------------------------------
    // ICE candidate handling
    // ----------------------------------------

    peerConnection.onicecandidate = (event) => {

        if (
            event.candidate &&
            mobileSocket &&
            mobileSocket.readyState === WebSocket.OPEN
        ) {

            mobileSocket.send(
                JSON.stringify({
                    type: "ice_candidate",
                    candidate: event.candidate
                })
            );

        }

    };


    // ----------------------------------------
    // Connection state
    // ----------------------------------------

    peerConnection.onconnectionstatechange = () => {

        console.log(
            "WebRTC connection state:",
            peerConnection.connectionState
        );


        if (
            peerConnection.connectionState ===
            "connected"
        ) {

            connectionText.textContent =
                "Live camera connected";

            statusDot.classList.add(
                "connected"
            );

            cameraMessage.textContent =
                "Your mobile camera is live on the laptop.";

        }


        if (
            peerConnection.connectionState ===
            "failed"
        ) {

            connectionText.textContent =
                "Camera connection failed";

            cameraMessage.textContent =
                "Could not establish live camera connection.";

        }

    };


    // ----------------------------------------
    // Create WebRTC offer
    // ----------------------------------------

    const offer =
        await peerConnection.createOffer();


    await peerConnection.setLocalDescription(
        offer
    );


    // Send offer to laptop through signaling server

    if (
        mobileSocket &&
        mobileSocket.readyState === WebSocket.OPEN
    ) {

        mobileSocket.send(
            JSON.stringify({
                type: "offer",
                sdp: peerConnection.localDescription
            })
        );

        console.log(
            "WebRTC offer sent to laptop."
        );

    }

}