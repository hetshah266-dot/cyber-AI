import streamlit as st
from langchain_community.llms import Ollama
import re
import json
import os
import hashlib
import time
import base64
import bleach
import html
import urllib.request

# Document Parsers for File Upload Handling
from pypdf import PdfReader
import docx
import pptx

# Cryptographic primitives for secure key derivation
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# =====================================================================
# AUTOMATED STREAMLIT CONFIGURATION INJECTION
# =====================================================================
st.config.set_option("server.headless", False)      
st.config.set_option("server.maxUploadSize", 5)     

# =====================================================================
# 1. HARDENED CRYPTOGRAPHIC STORAGE ENGINE (Environment Enforced)
# =====================================================================
# Read master password dynamically from environment with secure hardcoded fallback string
MASTER_PASSWORD = os.getenv("LAB_PORTAL_KEY") or "cyberlab2026"

def derive_secure_key(password: str) -> bytes:
    static_salt = b'\x19\xbf\x83\xad\xfa\xbc\xde\x02\x93\x84\x75\x61\x05\x04\x03\x02'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=static_salt,
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_data(plain_text: str) -> str:
    try:
        if not MASTER_PASSWORD: return ""
        key = derive_secure_key(MASTER_PASSWORD)
        f = Fernet(key)
        return f.encrypt(plain_text.encode()).decode()
    except Exception:
        return ""

def decrypt_data(cipher_text: str) -> str:
    try:
        if not MASTER_PASSWORD: return "{}"
        key = derive_secure_key(MASTER_PASSWORD)
        f = Fernet(key)
        return f.decrypt(cipher_text.encode()).decode()
    except Exception:
        return "{}"

# =====================================================================
# 2. DEFENSIVE SECURITY MATRIX & RATE LIMITERS
# =====================================================================
def advanced_sanitize_input(user_text: str) -> str:
    if not user_text:
        return ""
    return bleach.clean(user_text, tags=[], attributes={}, strip=True).strip()

def enforce_dos_ddos_protection() -> bool:
    current_time = time.time()
    if "request_count" not in st.session_state:
        st.session_state.request_count = 0
        st.session_state.window_start = current_time

    if current_time - st.session_state.window_start > 10.0:
        st.session_state.request_count = 0
        st.session_state.window_start = current_time

    st.session_state.request_count += 1
    return st.session_state.request_count <= 5

def verify_cybersecurity_relevance(text_content: str) -> bool:
    if not text_content or len(text_content.strip()) < 2:
        return False
        
    normalized_text = text_content.lower().strip()
    
    if len(st.session_state.get("active_messages", [])) > 0:
        conversational_modifiers = [
            "in points", "points", "bullet points", "bullets", "list", "summarize", 
            "short", "long", "explain", "elaborate", "give examples", "more details",
            "continue", "next", "show me", "yes", "no", "clear", "repeat"
        ]
        if any(mod in normalized_text for mod in conversational_modifiers) or len(normalized_text) < 15:
            return True
    
    educational_intents = [
        "knowledge", "learn", "explain", "how to", "what is", "study", 
        "details on", "means", "meaning", "define", "definition", "simple", "question",
        "topic", "give me", "tell me", "overview", "concept", "basics", "help", "in points", "points"
    ]
    if any(intent in normalized_text for intent in educational_intents):
        return True

    cyber_vocabulary = [
        "cyber", "security", "malware", "vulnerability", "exploit", "cve", "attack", "defense",
        "network", "packet", "firewall", "port", "ip address", "hash", "sha256", "md5", "cryptography",
        "encryption", "phishing", "ransomware", "trojan", "spyware", "siem", "splunk", "wazuh",
        "wireshark", "nmap", "metasploit", "forensics", "artifact", "log", "audit", "auth", "pfsense",
        "linux", "kali", "terminal", "dns", "dhcp", "routing", "soc", "incident", "threat", "dos", "ddos", "antivirus",
        "hacker", "black-hat", "white-hat", "grey-hat", "iso", "nist", "compliance", "risk", "mitigate"
    ]
    return any(word in normalized_text for word in cyber_vocabulary)

def highlight_cyber_keywords(text: str) -> str:
    if not text:
        return ""
    safe_text = html.escape(text)
    highlight_map = {
        r"\b(malware|vulnerability|exploit|cve|attack|phishing|ransomware|trojan|spyware|threat|dos|ddos|hacker|hackers|black-hat|white-hat|grey-hat|script kiddies)\b": "#ff6b6b",
        r"\b(cybersecurity|security|defense|firewall|cryptography|encryption|siem|splunk|wazuh|wireshark|nmap|metasploit|antivirus|soc|ids|ips)\b": "#4dadff",
        r"\b(network|packet|port|ip address|hash|sha256|md5|forensics|artifact|log|audit|auth|pfsense|linux|kali|terminal|dns|dhcp|routing|incident|file system|memory forensics)\b": "#2ecc71",
        r"\b(iso 27001|nist|csf|soc 2|compliance|governance|risk|mitigate|strategies|standards|regulatory frameworks|framework)\b": "#f1c40f"
    }
    highlighted_text = safe_text
    for pattern, color in highlight_map.items():
        replacement = f'<span style="color: {color} !important; font-weight: bold;">\\1</span>'
        highlighted_text = re.sub(pattern, replacement, highlighted_text, flags=re.IGNORECASE)
    return highlighted_text

# =====================================================================
# 3. INTERACTIVE CONTEXT CHUNKING ENGINE (Prevents LLM Overflow)
# =====================================================================
def chunk_text_context(text: str, chunk_size: int = 4000, overlap: int = 400) -> list:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def extract_text_from_file(uploaded_file) -> str:
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        st.error("🚨 [FILE DENIED]: Content block size exceeds secure threshold (5MB Limit).")
        return ""

    file_type = uploaded_file.name.split(".")[-1].lower()
    if file_type not in ["pdf", "docx", "pptx", "ppt", "txt"]:
        st.error("🚨 [UNSUPPORTED PAYLOAD]: Rejected extension footprint.")
        return ""

    extracted_text = ""
    try:
        if file_type == "txt":
            extracted_text = uploaded_file.read().decode("utf-8", errors="ignore")
        elif file_type == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text: extracted_text += text + "\n"
        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: extracted_text += para.text + "\n"
        elif file_type in ["pptx", "ppt"]:
            presentation = pptx.Presentation(uploaded_file)
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text: extracted_text += shape.text + "\n"
    except Exception:
        return ""
    return extracted_text.strip()

def track_session_timeout():
    TIMEOUT_LIMIT = 900
    current_time = time.time()
    if st.session_state.get("authenticated", False):
        if "last_activity" in st.session_state:
            if current_time - st.session_state.last_activity > TIMEOUT_LIMIT:
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.warning("🔒 Session terminated due to user inactivity.")
                st.stop()
        st.session_state.last_activity = current_time

# =====================================================================
# 4. OLLAMA BACKEND SERVICE HEALTH CHECK
# =====================================================================
def verify_ollama_status(model_name: str = "llama3:latest") -> bool:
    try:
        response = urllib.request.urlopen("http://localhost:11434/", timeout=2)
        if response.getcode() == 200:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=2) as res:
                data = json.loads(res.read().decode())
                models = [m['name'] for m in data.get('models', [])]
                if model_name in models or "llama3:latest" in models:
                    return True
        return False
    except Exception:
        return False

# =====================================================================
# 5. SECURE PERSISTENT CHAT HISTORY STORAGE
# =====================================================================
HISTORY_FILE = "secure_chat_history.enc"

def load_all_history_from_disk() -> dict:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                encrypted_content = f.read()
            decrypted_content = decrypt_data(encrypted_content)
            return json.loads(decrypted_content)
        except Exception:
            return {}
    return {}

def save_all_history_to_disk(all_history: dict):
    try:
        serialized_data = json.dumps(all_history, indent=4)
        encrypted_data = encrypt_data(serialized_data)
        with open(HISTORY_FILE, "w") as f:
            f.write(encrypted_data)
    except Exception:
        pass

def create_new_persistent_session() -> bool:
    all_history = load_all_history_from_disk()
    if "operator" not in all_history: 
        all_history["operator"] = {}
        
    if len(all_history["operator"]) >= 15:
        return False
        
    session_idx = len(all_history["operator"]) + 1
    session_id = f"session_{int(time.time())}"
    
    all_history["operator"][session_id] = {"title": f"🔍 incident_log_#{session_idx}", "messages": []}
    save_all_history_to_disk(all_history)
    st.session_state.current_session_id = session_id
    st.session_state.active_messages = []
    return True

# Initialize state structures
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None
if "active_messages" not in st.session_state: st.session_state.active_messages = []

track_session_timeout()

# =====================================================================
# 6. UI RENDER ENGINE & STYLING MATRIX
# =====================================================================
st.set_page_config(page_title="Personal Cyber AI Agent", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3, h4, h5, h6 { color: #58a6ff !important; font-family: 'Courier New', monospace; }
    .stChatMessage p, .stChatMessage li, .stChatMessage ul, .stChatMessage ol,
    .stChatMessage strong, .stChatMessage em { color: #f0f6fc !important; font-size: 15px; line-height: 1.6; }
    .stChatMessage code { background-color: #1f242c !important; color: #ff79c6 !important; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
    .zero-trust-banner { padding: 16px; background-color: rgba(88, 166, 255, 0.1); border: 1px solid #58a6ff; border-left: 5px solid #58a6ff; border-radius: 6px; font-family: monospace; font-size: 13px; color: #58a6ff !important; margin-bottom: 25px; }
    .status-box { padding: 15px; background: rgba(88, 166, 255, 0.1); border: 1px solid #30363d; border-left: 4px solid #58a6ff; border-radius: 6px; font-family: monospace; color: #58a6ff !important; }
    .role-tag { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-family: monospace; font-size: 12px; background-color: #8957e5; color: white;}
    .session-title { color: #8b949e; font-size: 12px; font-family: monospace; margin-top: 15px; }
    .study-legend { padding: 8px; background: #161b22; border-radius: 6px; border: 1px solid #30363d; font-family: monospace; font-size: 11px; margin-bottom: 10px; display: flex; gap: 15px; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 7. GATEWAY AUTHENTICATION PROFILES (WITH ANTI-BRUTE FORCE)
# =====================================================================
if "login_attempts" not in st.session_state: st.session_state.login_attempts = 0
if "lockout_time" not in st.session_state: st.session_state.lockout_time = 0.0

if not st.session_state.authenticated:
    st.title("🛡️ Terminal Access Portal")
    st.markdown('<div class="zero-trust-banner">🔒 [WAF / INTRUSION LAYER ENGAGED]: Secure PBKDF2 Engine Active.</div>', unsafe_allow_html=True)
    
    current_time = time.time()
    if current_time < st.session_state.lockout_time:
        remaining_lockout = int(st.session_state.lockout_time - current_time)
        st.error(f"🚨 [ACCOUNT LOCKED]: Access disabled for {remaining_lockout} seconds.")
        st.stop()
        
    with st.form("login_form"):
        st.markdown("### 🔑 ENTER MASTER PORTAL KEY")
        input_password = st.text_input("Access Password Key", type="password")
        submit_btn = st.form_submit_button("Unlock Console")
        
        if submit_btn:
            if not enforce_dos_ddos_protection():
                st.error("🚨 Flood Warning: Connection requests arriving too rapidly.")
                st.stop()
                
            if st.session_state.login_attempts >= 3:
                time.sleep(2) 

            if input_password == MASTER_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.session_state.lockout_time = 0.0
                st.session_state.last_activity = time.time()
                
                all_history = load_all_history_from_disk()
                if "operator" in all_history and all_history["operator"]:
                    st.session_state.current_session_id = list(all_history["operator"].keys())[-1]
                    st.session_state.active_messages = all_history["operator"][st.session_state.current_session_id]["messages"]
                else:
                    create_new_persistent_session()
                st.rerun() 
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= 5:
                    st.session_state.lockout_time = time.time() + 60.0
                    st.error("❌ Access Denied: Failure threshold breached. Interface locked down.")
                    st.rerun()
                else:
                    st.error(f"❌ Access Denied: Invalid key signature.")
else:
    # RUNTIME HEALTH CHECK: Execute Ollama validation only after successful portal validation
    if not verify_ollama_status("llama3:latest"):
        st.error("🚨 [CORE SERVICE CRASH]: Ollama service is not reachable on `http://localhost:11434` or `llama3:latest` model missing.")
        st.info("💡 **To fix this, open your system terminal window and run:**\n```bash\nollama run llama3\n```\nKeep that terminal open and refresh this browser panel.")
        st.stop()

    all_history = load_all_history_from_disk()
    user_sessions = all_history.get("operator", {})

    if st.session_state.current_session_id not in user_sessions:
        if user_sessions:
            st.session_state.current_session_id = list(user_sessions.keys())[-1]
            st.session_state.active_messages = user_sessions[st.session_state.current_session_id]["messages"]
        else:
            success = create_new_persistent_session()
            if not success:
                st.error("🚨 Capacity Warning: Session ceiling hit (15 Workspace max limit).")
                st.stop()
            all_history = load_all_history_from_disk()
            user_sessions = all_history.get("operator", {})
            st.session_state.active_messages = user_sessions[st.session_state.current_session_id]["messages"]
    else:
        st.session_state.active_messages = user_sessions[st.session_state.current_session_id]["messages"]

    # Sidebar Panel Setup
    with st.sidebar:
        st.markdown("### 📁 SYSTEM MONITOR")
        st.markdown('<span class="role-tag">ROLE: ROOT_OPERATOR</span>', unsafe_allow_html=True)
        st.write("---")
        
        uploaded_file = st.file_uploader(
            "Ingest Reports/Artifacts", 
            type=["pdf", "docx", "pptx", "ppt", "txt"]
        )
        st.write("---")
        
        if st.button("➕ Open New Lab Session", use_container_width=True):
            if create_new_persistent_session(): st.rerun()

        st.markdown('<p class="session-title">📜 SECURE CHAT HISTORY LOGS</p>', unsafe_allow_html=True)
        for sess_id, sess_data in list(user_sessions.items()):
            is_active = (sess_id == st.session_state.current_session_id)
            btn_label = f"➡️ {sess_data['title']}" if is_active else f"📁 {sess_data['title']}"
            
            col_nav, col_del = st.columns([0.82, 0.18])
            with col_nav:
                if st.button(btn_label, key=f"nav_{sess_id}", use_container_width=True):
                    st.session_state.current_session_id = sess_id
                    st.session_state.active_messages = sess_data["messages"]
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{sess_id}"):
                    all_history = load_all_history_from_disk()
                    if "operator" in all_history and sess_id in all_history["operator"]:
                        del all_history["operator"][sess_id]
                        save_all_history_to_disk(all_history)
                    if st.session_state.current_session_id == sess_id:
                        remaining_sessions = all_history.get("operator", {})
                        if remaining_sessions:
                            st.session_state.current_session_id = list(remaining_sessions.keys())[-1]
                            st.session_state.active_messages = remaining_sessions[st.session_state.current_session_id]["messages"]
                        else:
                            st.session_state.current_session_id = None
                            st.session_state.active_messages = []
                    st.rerun()

        st.write("---")
        if st.button("Lock Console (Wipe RAM State)", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]    
            st.rerun()

    # Chat UI Panel
    st.title("🛡️ Secure Cyber Lab Platform")
    st.markdown("<p style='color: #8b949e; font-family: monospace;'>[PRIVILEGE STATUS: ROOT_OPERATOR] [WAF ENGINE: ENFORCED]</p>", unsafe_allow_html=True)
    st.markdown("<div class=\"study-legend\"><span>🔴 Attack/Threats</span><span>🔵 Controls/SOC</span><span>🟢 Networks/Forensics</span><span>🟡 Standards/Risk</span></div>", unsafe_allow_html=True)
    st.write("---")

    for message in st.session_state.active_messages:
        with st.chat_message(message["role"]): 
            st.markdown(highlight_cyber_keywords(message["content"]), unsafe_allow_html=True)

    if user_input := st.chat_input("Analyze payloads or vulnerabilities..."):
        if not enforce_dos_ddos_protection():
            st.toast("🚨 Rate limit threshold triggered!", icon="🛑")
            st.stop()

        clean_prompt = advanced_sanitize_input(user_input)
        
        file_context = ""
        if uploaded_file is not None:
            with st.spinner("Extracting asset text stream..."):
                raw_text = extract_text_from_file(uploaded_file)
                if raw_text:
                    text_chunks = chunk_text_context(raw_text, chunk_size=3500, overlap=300)
                    file_context = "\n--- CONTEXT CHUNK ---\n".join(text_chunks[:3]) 
                    if len(text_chunks) > 3:
                        st.warning("⚠️ Large file detected. Input context optimized to fit model execution window securely.")

        if file_context:
            full_user_payload = f"[ATTACHED DATA ({uploaded_file.name})]:\n\"\"\"\n{file_context}\n\"\"\"\n\nTASK: {clean_prompt}"
        else:
            full_user_payload = clean_prompt

        if not full_user_payload: st.stop()

        if not verify_cybersecurity_relevance(clean_prompt):
            with st.chat_message("user"): st.markdown(clean_prompt)
            with st.chat_message("assistant"):
                error_msg = "⚠️ [POLICY VIOLATION DETECTED]: This terminal console is restricted entirely to Cybersecurity tasks. Query dropped."
                st.markdown(error_msg)
            st.session_state.active_messages.append({"role": "user", "content": clean_prompt})
            st.session_state.active_messages.append({"role": "assistant", "content": error_msg})
            all_history = load_all_history_from_disk()
            all_history["operator"][st.session_state.current_session_id]["messages"] = st.session_state.active_messages
            save_all_history_to_disk(all_history)
            st.stop()

        with st.chat_message("user"): 
            display_text = f"📎 **Uploaded Asset:** `{uploaded_file.name}`\n\n{clean_prompt}" if uploaded_file is not None else clean_prompt
            st.markdown(highlight_cyber_keywords(display_text), unsafe_allow_html=True)
                
        st.session_state.active_messages.append({"role": "user", "content": clean_prompt if not file_context else full_user_payload})

        all_history = load_all_history_from_disk()
        if "incident_log_#" in all_history["operator"][st.session_state.current_session_id]["title"]:
            title_text = clean_prompt[:20] + "..." if len(clean_prompt) > 20 else clean_prompt
            all_history["operator"][st.session_state.current_session_id]["title"] = f"🔍 {title_text}"

        all_history["operator"][st.session_state.current_session_id]["messages"] = st.session_state.active_messages
        save_all_history_to_disk(all_history)

        SYSTEM_PROMPT = (
            "You are an expert, highly specialized Defensive Cybersecurity, Network Engineering, and Digital Forensics Assistant. "
            "You operate inside a secure sandboxed lab environment. You must answer conceptual, theoretical, educational, and general "
            "informational questions regarding cybersecurity directly from the user's text. "
            "Only refuse and state 'I am locked down to cybersecurity operations only.' if the user asks completely non-cyber questions."
        )

        compiled_execution_context = f"SYSTEM INSTRUCTIONS:\n{SYSTEM_PROMPT}\n\n"
        for msg in st.session_state.active_messages[:-1]:
            if "POLICY VIOLATION DETECTED" not in msg["content"]:
                compiled_execution_context += f"{msg['role'].upper()}: {msg['content']}\n"
        compiled_execution_context += f"USER TRANSACTION: {full_user_payload}\nASSISTANT SYSTEM DIRECTIVE: Provide direct, professional answers with expert cybersecurity insight."

        with st.chat_message("assistant"):
            status_placeholder = st.markdown('<div class="status-box">🔄 Running analysis loop...</div>', unsafe_allow_html=True)
            try:
                llm = Ollama(model="llama3:latest", temperature=0.1)
                text_placeholder = st.empty()
                response_accumulator = ""
                
                for chunk in llm.stream(compiled_execution_context):
                    response_accumulator += chunk
                    text_placeholder.markdown(highlight_cyber_keywords(response_accumulator), unsafe_allow_html=True)
                
                status_placeholder.empty()
                st.session_state.active_messages.append({"role": "assistant", "content": response_accumulator})
                all_history = load_all_history_from_disk()
                all_history["operator"][st.session_state.current_session_id]["messages"] = st.session_state.active_messages
                save_all_history_to_disk(all_history)
            except Exception as e:
                status_placeholder.empty()
                st.error(f"Inference error: {e}")