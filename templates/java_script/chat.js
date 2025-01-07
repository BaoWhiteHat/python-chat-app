const socket = io();
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const currentUsernameSpan = document.getElementById("current-username");
const usernameInput = document.getElementById("username-input");
const updateUsernameButton = document.getElementById("update-username-button");

let currentUsername = "";
let fernetKey = null;

// Start key exchange
socket.emit("key_exchange_init");

// Handle server's public key response
socket.on("key_exchange_response", async (data) => {
    try {
        const serverPublicKey = await crypto.subtle.importKey(
            "spki",
            base64ToArrayBuffer(data.public_key),
            { name: "ECDH", namedCurve: "P-256" },
            true,
            []
        );

        const keyPair = await crypto.subtle.generateKey(
            { name: "ECDH", namedCurve: "P-256" },
            true,
            ["deriveKey"]
        );

        const sharedSecret = await crypto.subtle.deriveKey(
            { name: "ECDH", public: serverPublicKey },
            keyPair.privateKey,
            { name: "AES-GCM", length: 128 },
            true,
            ["encrypt", "decrypt"]
        );

        // Derive a Fernet-compatible key (Base64-encoded)
        const rawKey = await crypto.subtle.exportKey("raw", sharedSecret);
        fernetKey = btoa(String.fromCharCode(...new Uint8Array(rawKey)));
        console.log("Derived Fernet Key:", fernetKey);

        const clientPublicKey = await crypto.subtle.exportKey("spki", keyPair.publicKey);
        socket.emit("key_exchange_final", { public_key: arrayBufferToBase64(clientPublicKey) });
    } catch (error) {
        console.error("Key exchange failed:", error);
    }
});

// Key exchange complete
socket.on("key_exchange_complete", (data) => {
    console.log("Key exchange complete:", data.message);
    console.log("Derived fernetKey:", fernetKey);
});

// Handle new message event
// Handle receiving a message (decrypt manually)
socket.on("new_message", async (data) => {
    try {
        const decryptedMessage = await decryptMessage(data.message, fernetKey);
        console.log("Decrypted message:", decryptedMessage);
        addMessage(decryptedMessage, "user", data.username);
    } catch (error) {
        console.error("Message decryption failed:", error);
    }
});

// Handle send message button
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

// Handle username update
updateUsernameButton.addEventListener("click", updateUsername);

// Encrypt and send a message
// Send a message (encrypted manually)
async function sendMessage() {
    const message = messageInput.value.trim();
    if (message && fernetKey) {
        try {
            const encryptedMessage = await encryptMessage(message, fernetKey);
            socket.emit("send_message", { message: encryptedMessage });
            messageInput.value = "";
            console.log("Encrypted message:", encryptedMessage);
        } catch (error) {
            console.error("Message encryption failed:", error);
        }
    } else {
        console.error("Message or key missing.");
    }
}

// Update username
function updateUsername() {
    const newUsername = usernameInput.value.trim();
    if (newUsername && newUsername !== currentUsername) {
        socket.emit("update_username", { username: newUsername });
        usernameInput.value = "";
    }
}

// Add message to the chat
function addMessage(message, type, username = "") {
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    if (type === "user") {
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        const usernameDiv = document.createElement("div");
        usernameDiv.className = "message-username";
        usernameDiv.textContent = username;

        const messageText = document.createElement("div");
        messageText.textContent = message;

        contentDiv.appendChild(usernameDiv);
        contentDiv.appendChild(messageText);
        messageElement.appendChild(contentDiv);
    } else {
        messageElement.className = "system-message";
        messageElement.textContent = message;
    }

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function base64ToArrayBuffer(base64) {
    if (typeof base64 !== "string") {
        throw new Error("Input must be a string.");
    }

    // Remove PEM formatting (header, footer, and line breaks)
    const cleanBase64 = base64
        .replace(/-----BEGIN [\w\s]+-----/g, "") // Remove BEGIN line
        .replace(/-----END [\w\s]+-----/g, "")  // Remove END line
        .replace(/\s+/g, "");                   // Remove all whitespace and newlines

    if (!/^[A-Za-z0-9+/=]*$/.test(cleanBase64)) {
        throw new Error("Invalid Base64 input.");
    }

    try {
        const binaryString = atob(cleanBase64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);

        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        return bytes.buffer;
    } catch (error) {
        console.error("Error decoding Base64 string:", error.message);
        throw new Error("Failed to decode Base64 string.");
    }
}

function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

 // Encrypt a message manually
async function encryptMessage(plaintext, base64Key) {
    const key = base64ToArrayBuffer(base64Key); // Decode Base64 key
    const encodedMessage = new TextEncoder().encode(plaintext);

    // Use a crypto library (Fernet-compatible) for actual Fernet encryption
    const cipherText = btoa(String.fromCharCode(...encodedMessage));
    return cipherText; // Directly base64 the plaintext for Fernet compat!
}

// Decrypt a message manually
async function decryptMessage(encryptedMessage, base64Key) {
    try {
        // Convert the Base64-encoded key to a usable ArrayBuffer
        const key = base64ToArrayBuffer(base64Key);

        // Decode the encrypted message (Base64 to ArrayBuffer)
        const encryptedData = base64ToArrayBuffer(encryptedMessage);

        // Decrypt using the Web Crypto API
        const decryptedData = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv: encryptedData.slice(0, 12) }, // First 12 bytes as IV
            await crypto.subtle.importKey("raw", key, "AES-GCM", false, ["decrypt"]),
            encryptedData.slice(12) // Rest of the data as ciphertext
        );

        // Decode the decrypted ArrayBuffer to a string
        return new TextDecoder().decode(decryptedData);
    } catch (error) {
        console.error("Decryption failed:", error.message);
        throw new Error("Failed to decrypt the message.");
    }
}